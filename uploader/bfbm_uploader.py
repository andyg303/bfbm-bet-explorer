#!/usr/bin/env python3
"""BFBM Bet Explorer scheduled CSV uploader.

This helper is designed to run on the same Windows VPS/PC as BF Bot Manager.
It reads a configured BFBM CSV/master CSV file (or every CSV in a folder),
keeps only recent settled rows, and uploads them to BFBM Bet Explorer using a
revocable automation token.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import re
import secrets
import subprocess
import sys
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


APP_NAME = "BFBM Bet Explorer Uploader"
DEFAULT_API_URL = "https://bfbmbetexplorer.com/api"
DEFAULT_TASK_NAME = "BFBM Bet Explorer Upload"
DEFAULT_UPLOAD_TIMEOUT = 900

if os.name == "nt":
    CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
else:
    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "bfbm-bet-explorer-uploader"
CONFIG_PATH = CONFIG_DIR / "config.json"
LOG_PATH = CONFIG_DIR / "uploader.log"

DATE_HEADER_KEYS = (
    "settleddate",
    "settled",
    "starttime",
    "marketstarttime",
    "matcheddate",
    "placeddate",
)
STATUS_HEADER_KEYS = ("status",)
CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")

XML_FIELD_TO_CSV_HEADER = {
    "BetId": "BetId",
    "Name": "Name",
    "Status": "Status",
    "Matched": "Matched",
    "AvgPrice": "AvgPrice",
    "PriceRequested": "Price Requested",
    "BetType": "Bet Type",
    "PlacedDate": "PlacedDate",
    "MatchedDate": "Matched Date",
    "SettledDate": "Settled Date",
    "StartTime": "StartTime",
    "StrategyName": "StrategyName",
    "StrategyID": "StrategyID",
    "ProfitLoss": "ProfitLoss",
    "ShortDescription": "Short Description",
    "LossRecoveryAmount": "Loss rec. amount",
    "CountryCode": "Country Code",
    "CompetitionName": "Competition",
    "SelectionName": "SelectionName",
    "MarketName": "MarketName",
    "MarketId": "MarketId",
    "EventTypeName": "EventTypeName",
    "MarketType": "Market Type",
    "TotalMatchedOnMarket": "Total matched on market",
    "TotalMatchedOnRunner": "Total matched on runner",
    "NumberOfRunners": "Number of selections",
    "FavoriteByPosition": "Favorite Position",
    "BSP": "BSP",
    "Tipster": "Tipster",
}
BFBM_XML_HEADERS = list(dict.fromkeys(XML_FIELD_TO_CSV_HEADER.values()))


def validate_api_url(api_url: str) -> None:
    parsed = urlparse(api_url)
    if parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
        return
    raise ValueError("API URL must be HTTPS. HTTP is allowed only for localhost development.")


def normalize_header(name: str) -> str:
    name = str(name).strip().replace("\ufeff", "").replace("\ufffd", "")
    name = name.strip("\"'").strip()
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_header(headers: list[str], accepted_keys: tuple[str, ...]) -> str | None:
    by_key = {normalize_header(header): header for header in headers}
    for key in accepted_keys:
        if key in by_key:
            return by_key[key]
    return None


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip().strip("'")
    if not text:
        return None

    iso_text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso_text)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed
    except ValueError:
        pass

    formats = (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass


def append_log(message: str) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass


def read_csv_file(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as fh:
                reader = csv.DictReader(fh)
                if not reader.fieldnames:
                    return [], []
                rows = [dict(row) for row in reader]
                return list(reader.fieldnames), rows
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    return [], []


def read_gzip_or_plain_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if data.startswith(b"\x1f\x8b"):
        return gzip.decompress(data)
    return data


def looks_like_xml(data: bytes) -> bool:
    sample = data[:256].lstrip(b"\xef\xbb\xbf\r\n\t ")
    return sample.startswith(b"<?xml") or sample.startswith(b"<ArrayOfBetHistoryItem")


def read_bfbm_xml_history(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    data = read_gzip_or_plain_bytes(path)
    text = data.decode("utf-8-sig")
    root = ET.fromstring(text)
    if root.tag != "ArrayOfBetHistoryItem":
        raise ValueError(f"Unexpected BFBM XML root: {root.tag}")

    rows: list[dict[str, str]] = []
    for item in root.findall("BetHistoryItem"):
        row = {header: "" for header in BFBM_XML_HEADERS}
        values = {child.tag: child.text or "" for child in item}
        for xml_field, csv_header in XML_FIELD_TO_CSV_HEADER.items():
            row[csv_header] = values.get(xml_field, "")
        rows.append(row)
    return BFBM_XML_HEADERS, rows


def read_source_file(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    data = read_gzip_or_plain_bytes(path)
    if looks_like_xml(data):
        return read_bfbm_xml_history(path)

    if path.suffix.lower() == ".gz":
        for encoding in CSV_ENCODINGS:
            try:
                text = data.decode(encoding)
                reader = csv.DictReader(io.StringIO(text))
                if not reader.fieldnames:
                    return [], []
                return list(reader.fieldnames), [dict(row) for row in reader]
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode compressed source: {path}")

    return read_csv_file(path)


def filter_recent_rows(
    headers: list[str],
    rows: list[dict[str, str]],
    lookback_hours: int,
    settled_only: bool,
) -> list[dict[str, str]]:
    status_header = find_header(headers, STATUS_HEADER_KEYS)
    date_header = find_header(headers, DATE_HEADER_KEYS)
    if not date_header:
        raise ValueError("CSV does not contain a recognised settled/start/placed date column")

    cutoff = datetime.now() - timedelta(hours=lookback_hours)
    filtered: list[dict[str, str]] = []
    for row in rows:
        if settled_only:
            if not status_header:
                continue
            status_value = str(row.get(status_header, "")).strip().upper()
            if status_value != "SETTLED":
                continue

        row_dt = parse_datetime(row.get(date_header))
        if not row_dt:
            continue
        if row_dt >= cutoff:
            filtered.append(row)
    return filtered


def csv_bytes(headers: list[str], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def iter_sources(source: str) -> list[Path]:
    path = Path(source).expanduser()
    if path.is_file():
        return [path]
    if path.is_dir():
        candidates: dict[Path, None] = {}
        for pattern in ("*.csv", "*.gz", "*bets_history*"):
            for candidate in path.glob(pattern):
                if candidate.is_file():
                    candidates[candidate] = None
        return sorted(candidates.keys(), key=lambda p: p.stat().st_mtime, reverse=True)
    raise FileNotFoundError(f"Source not found: {path}")


def default_bfbm_history_paths() -> list[Path]:
    paths: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        bfbm_dir = Path(local_app_data) / "bfbotmanager.com" / "Bf Bot Manager V3"
        paths.extend([
            bfbm_dir / "uk_bets_history.gz",
            bfbm_dir / "uk_bets_history",
            bfbm_dir / "uk_bets_history.gz.bck",
        ])
    return paths


def find_default_bfbm_history() -> Path | None:
    for path in default_bfbm_history_paths():
        if path.exists():
            return path
    return None


def _https_open(request: urllib.request.Request, timeout: int):
    """Open an HTTPS request with a working SSL context on Windows VPS/server environments.

    On some Windows Server installations Python cannot locate the system CA
    bundle, causing ``CERTIFICATE_VERIFY_FAILED``.  We prefer ``certifi``'s
    bundled CA store (included in the PyInstaller build), then fall back to the
    default context which works on most systems.
    """
    try:
        import certifi  # bundled by PyInstaller spec
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        if sys.platform == "win32":
            try:
                ctx.load_default_certs()
            except Exception:
                pass
    https_handler = urllib.request.HTTPSHandler(context=ctx)
    opener = urllib.request.build_opener(https_handler)
    return opener.open(request, timeout=timeout)


def upload_csv(api_url: str, token: str, filename: str, payload: bytes, timeout: int) -> dict[str, Any]:
    validate_api_url(api_url)
    endpoint = f"{api_url.rstrip('/')}/automation/ingest"
    boundary = f"----BFBMBetExplorer{secrets.token_hex(16)}"
    safe_filename = filename.replace('"', "")
    body = b"".join([
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'
            "Content-Type: text/csv\r\n\r\n"
        ).encode("utf-8"),
        payload,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ])

    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "X-BFBM-Automation-Token": token,
            "User-Agent": "BFBM-Bet-Explorer-Uploader/1.0",
        },
    )
    try:
        with _https_open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Upload failed with HTTP {exc.code}: {detail}") from exc


def get_job_status(api_url: str, token: str, job_id: Any, timeout: int = 60) -> dict[str, Any]:
    validate_api_url(api_url)
    endpoint = f"{api_url.rstrip('/')}/automation/ingest/{job_id}"
    request = urllib.request.Request(
        endpoint,
        method="GET",
        headers={
            "Accept": "application/json",
            "X-BFBM-Automation-Token": token,
            "User-Agent": "BFBM-Bet-Explorer-Uploader/1.0",
        },
    )
    try:
        with _https_open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Status check failed with HTTP {exc.code}: {detail}") from exc


def wait_for_job(
    api_url: str,
    token: str,
    job_id: Any,
    timeout: int = DEFAULT_UPLOAD_TIMEOUT,
    poll_interval: int = 5,
    log=print,
) -> dict[str, Any]:
    """Poll the server until an async ingestion job finishes.

    Each poll is a quick request, so no single connection stays open long enough
    to be killed by an upstream proxy timeout — however long the server takes.
    """
    deadline = time.monotonic() + timeout
    last_note = time.monotonic()
    consecutive_errors = 0
    while True:
        try:
            status = get_job_status(api_url, token, job_id)
            consecutive_errors = 0
        except Exception as exc:
            consecutive_errors += 1
            if consecutive_errors >= 5:
                raise RuntimeError(
                    f"Lost contact with the server while waiting for job {job_id}: {exc}"
                ) from exc
            time.sleep(poll_interval)
            continue

        state = status.get("status")
        if status.get("done") or state in ("success", "partial", "error"):
            if state == "error":
                raise RuntimeError(status.get("error") or "Server reported an ingestion error")
            return status

        now = time.monotonic()
        if now - last_note >= 20:
            log(f"  …still processing on the server (job {job_id})")
            last_note = now
        if now >= deadline:
            raise RuntimeError(
                f"Timed out after {timeout}s waiting for the server to finish "
                f"(job {job_id} still '{state}')."
            )
        time.sleep(poll_interval)


def api_json_request(
    api_url: str,
    path: str,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    validate_api_url(api_url)
    endpoint = f"{api_url.rstrip('/')}/{path.lstrip('/')}"
    body = json.dumps(payload or {}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "BFBM-Bet-Explorer-Uploader/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(endpoint, data=body, method="POST", headers=headers)
    try:
        with _https_open(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            detail = parsed.get("detail", detail)
        except json.JSONDecodeError:
            pass
        raise RuntimeError(f"API request failed with HTTP {exc.code}: {detail}") from exc


def login_and_create_upload_token(
    api_url: str,
    email: str,
    password: str,
    token_name: str,
    timeout: int = 60,
) -> str:
    login = api_json_request(
        api_url,
        "/auth/login",
        {"email": email, "password": password},
        timeout=timeout,
    )
    access_token = login.get("access_token")
    if not access_token:
        raise RuntimeError("Login succeeded but no access token was returned")

    created = api_json_request(
        api_url,
        "/automation/tokens",
        {"name": token_name or "VPS uploader"},
        token=access_token,
        timeout=timeout,
    )
    upload_token = created.get("token")
    if not upload_token:
        raise RuntimeError("Token creation succeeded but no upload token was returned")
    return upload_token


def run_upload(
    api_url: str,
    token: str,
    source: str,
    lookback_hours: int = 48,
    timeout: int = DEFAULT_UPLOAD_TIMEOUT,
    settled_only: bool = True,
    log=print,
) -> int:
    uploaded = 0
    for path in iter_sources(source):
        headers, rows = read_source_file(path)
        if not headers:
            log(f"{path.name}: empty CSV, skipped")
            continue

        filtered = filter_recent_rows(headers, rows, lookback_hours, settled_only)
        if not filtered:
            log(f"{path.name}: no rows in the last {lookback_hours} hours")
            continue

        payload = csv_bytes(headers, filtered)
        upload_name = f"{path.stem}-last-{lookback_hours}h.csv"
        accepted = upload_csv(api_url, token, upload_name, payload, timeout)

        job_id = accepted.get("job_id") if isinstance(accepted, dict) else None
        if job_id is None:
            # Older server that processed the upload synchronously.
            result = accepted
        else:
            log(
                f"{path.name}: uploaded {len(filtered)} rows; "
                f"server is processing (job {job_id})…"
            )
            result = wait_for_job(api_url, token, job_id, timeout=timeout, log=log)

        uploaded += len(filtered)
        log(
            f"{path.name}: done — "
            f"inserted={result.get('inserted', 0)} "
            f"updated={result.get('updated', 0)} "
            f"skipped={result.get('skipped', 0)}"
        )
        warnings = result.get("warnings") or []
        if warnings:
            log(f"{path.name}: {len(warnings)} warning(s); first: {warnings[0]}")

    if uploaded == 0:
        log("Nothing to upload.")
    return uploaded


def command_configure(args: argparse.Namespace) -> int:
    config = load_config()
    if args.api_url:
        config["api_url"] = args.api_url
    elif "api_url" not in config:
        config["api_url"] = DEFAULT_API_URL

    if args.token:
        config["token"] = args.token
    if args.source:
        config["source"] = args.source
    if args.time:
        config["time"] = args.time
    if args.lookback_hours:
        config["lookback_hours"] = args.lookback_hours

    validate_api_url(config.get("api_url") or DEFAULT_API_URL)
    missing = [key for key in ("api_url", "token", "source") if not config.get(key)]
    if missing:
        print(f"Missing required config: {', '.join(missing)}", file=sys.stderr)
        return 2

    save_config(config)
    print(f"Saved config to {CONFIG_PATH}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    config = load_config()
    api_url = args.api_url or config.get("api_url") or DEFAULT_API_URL
    token = args.token or config.get("token")
    source = args.source or config.get("source")
    lookback_hours = int(args.lookback_hours or config.get("lookback_hours") or 48)
    timeout = int(args.timeout or config.get("timeout") or DEFAULT_UPLOAD_TIMEOUT)
    settled_only = not args.include_matched

    if not token:
        print("No automation token configured.", file=sys.stderr)
        return 2
    if not source:
        print("No CSV source configured.", file=sys.stderr)
        return 2

    def log(message: str) -> None:
        print(message)
        append_log(message)

    run_upload(
        api_url=api_url,
        token=token,
        source=source,
        lookback_hours=lookback_hours,
        timeout=timeout,
        settled_only=settled_only,
        log=log,
    )
    return 0


def task_command() -> str:
    """Combined command string for the basic (logged-on-only) schtasks /TR fallback."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" run'
    return f'"{sys.executable}" "{Path(__file__).resolve()}" run'


def task_exec_parts() -> tuple[str, str]:
    """Return (command, arguments) split apart for the Task Scheduler XML <Exec>."""
    if getattr(sys, "frozen", False):
        return sys.executable, "run"
    return sys.executable, f'"{Path(__file__).resolve()}" run'


def build_task_xml(run_time: str, command: str, arguments: str) -> str:
    """Build a Task Scheduler 1.2 XML definition.

    Uses LogonType ``S4U`` so the task runs **whether the user is logged on or
    not**, without storing the Windows password, and as the current user (so the
    helper's ``%APPDATA%`` config file still resolves correctly). ``schtasks``
    cannot create an S4U task from command-line flags — only via /XML.
    """
    hh, mm = run_time.split(":")
    start = datetime.now().replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    start_boundary = start.strftime("%Y-%m-%dT%H:%M:%S")
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    user = os.environ.get("USERNAME", "")
    domain = os.environ.get("USERDOMAIN", "")
    user_id = f"{domain}\\{user}" if domain and user else user

    def esc(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{now_str}</Date>
    <Author>{esc(user_id)}</Author>
    <Description>Daily upload of recent BFBM bets to BFBM Bet Explorer.</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{start_boundary}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{esc(user_id)}</UserId>
      <LogonType>S4U</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{esc(command)}</Command>
      <Arguments>{esc(arguments)}</Arguments>
    </Exec>
  </Actions>
</Task>"""


def install_daily_task(run_time: str, task_name: str = DEFAULT_TASK_NAME) -> str:
    """Create/replace the daily scheduled task.

    Returns ``"logged-off"`` when the task runs whether the user is logged on or
    not (preferred), or ``"logged-on"`` when only the basic logged-on-only task
    could be created. Raises ``RuntimeError`` if nothing could be installed.
    """
    if os.name != "nt":
        raise RuntimeError("Daily task installation is only available on Windows.")

    command, arguments = task_exec_parts()

    # Preferred: S4U task — runs whether logged on or not, no stored password.
    s4u_error = ""
    tmp_path = None
    try:
        xml = build_task_xml(run_time, command, arguments)
        fd, tmp_path = tempfile.mkstemp(suffix=".xml")
        os.close(fd)
        Path(tmp_path).write_text(xml, encoding="utf-16")
        result = subprocess.run(
            ["schtasks", "/Create", "/TN", task_name, "/XML", tmp_path, "/F"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return "logged-off"
        s4u_error = (result.stderr or result.stdout or "").strip()
    except Exception as exc:  # noqa: BLE001 — fall back to the basic method
        s4u_error = str(exc)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # Fallback: basic task that only runs while the user is logged on.
    fallback_cmd = [
        "schtasks", "/Create", "/TN", task_name,
        "/SC", "DAILY", "/ST", run_time,
        "/TR", task_command(), "/F",
    ]
    try:
        subprocess.run(fallback_cmd, check=True, capture_output=True, text=True)
        return "logged-on"
    except subprocess.CalledProcessError as exc:
        output = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(
            f"Task Scheduler failed (exit {exc.returncode}){': ' + output if output else '.'}\n"
            f"(Run-whether-logged-on-or-not mode also failed: {s4u_error})\n\n"
            "Tip: try running the uploader as Administrator, or use the \"Run in Background\" "
            "button and keep the app open."
        ) from exc


def command_install_task(args: argparse.Namespace) -> int:
    if os.name != "nt":
        print("Windows Task Scheduler install is only available on Windows.", file=sys.stderr)
        return 2

    config = load_config()
    run_time = args.time or config.get("time")
    if not run_time:
        print("Provide --time HH:MM or save it with configure first.", file=sys.stderr)
        return 2

    task_name = args.task_name or DEFAULT_TASK_NAME
    mode = install_daily_task(run_time, task_name)
    if mode == "logged-off":
        print(f"Installed daily task '{task_name}' at {run_time} (runs whether you are logged in or not).")
    else:
        print(
            f"Installed daily task '{task_name}' at {run_time} — NOTE: this VPS only allows "
            "tasks that run while you are logged in. Stay logged in, or keep the app open."
        )
    return 0


def command_show_config(_args: argparse.Namespace) -> int:
    config = load_config()
    safe_config = dict(config)
    if safe_config.get("token"):
        safe_config["token"] = f"{safe_config['token'][:18]}..."
    print(json.dumps(safe_config, indent=2))
    print(f"Config path: {CONFIG_PATH}")
    return 0


class UploaderGui:
    def __init__(self, root: Any, tk: Any, ttk: Any, filedialog: Any, messagebox: Any):
        self.root = root
        self.tk = tk
        self.ttk = ttk
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.config = load_config()

        root.title(APP_NAME)
        root.geometry("760x620")
        root.minsize(680, 560)

        self.api_url = tk.StringVar(value=self.config.get("api_url") or DEFAULT_API_URL)
        self.email = tk.StringVar()
        self.password = tk.StringVar()
        self.token_status = tk.StringVar(value=self._token_label())
        default_history = find_default_bfbm_history()
        self.source = tk.StringVar(value=self.config.get("source") or (str(default_history) if default_history else ""))
        self.run_time = tk.StringVar(value=self.config.get("time") or "02:15")
        self.lookback_hours = tk.StringVar(value=str(self.config.get("lookback_hours") or 48))
        self.busy = False
        self._scheduler_thread: threading.Thread | None = None
        self._scheduler_stop = threading.Event()
        self.scheduler_btn_text = tk.StringVar(value="Run in Background")

        self._build()

    def _token_label(self) -> str:
        token = self.config.get("token")
        return f"Connected ({token[:18]}...)" if token else "Not connected"

    def _build(self) -> None:
        main = self.ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        title = self.ttk.Label(main, text=APP_NAME, font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, sticky="w")
        self.ttk.Button(main, text="? Help", command=self.show_help).grid(
            row=0, column=0, sticky="e"
        )
        subtitle = self.ttk.Label(
            main,
            text="Connect your dashboard account, choose the BFBM/autosave CSV, then install the daily upload task.",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 14))

        account = self.ttk.LabelFrame(main, text="1. Connect Account", padding=12)
        account.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        account.columnconfigure(1, weight=1)

        self.ttk.Label(account, text="API URL").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.ttk.Entry(account, textvariable=self.api_url).grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)
        self.ttk.Label(account, text="Email").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.ttk.Entry(account, textvariable=self.email).grid(row=1, column=1, sticky="ew", pady=4)
        self.ttk.Label(account, text="Password").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.ttk.Entry(account, textvariable=self.password, show="*").grid(row=2, column=1, sticky="ew", pady=4)
        self.ttk.Button(account, text="Connect", command=self.connect_account).grid(row=1, column=2, rowspan=2, sticky="ns", padx=(8, 0), pady=4)
        self.ttk.Label(account, textvariable=self.token_status).grid(row=3, column=1, sticky="w", pady=(6, 0))

        source = self.ttk.LabelFrame(main, text="2. CSV Source", padding=12)
        source.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        source.columnconfigure(1, weight=1)

        self.ttk.Label(source, text="BFBM history / CSV").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.ttk.Entry(source, textvariable=self.source).grid(row=0, column=1, sticky="ew", pady=4)
        buttons = self.ttk.Frame(source)
        buttons.grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.ttk.Button(buttons, text="Auto", command=self.auto_detect_source).pack(side="left", padx=(0, 4))
        self.ttk.Button(buttons, text="File", command=self.choose_file).pack(side="left", padx=(0, 4))
        self.ttk.Button(buttons, text="Folder", command=self.choose_folder).pack(side="left")

        schedule = self.ttk.LabelFrame(main, text="3. Schedule", padding=12)
        schedule.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        for col in range(4):
            schedule.columnconfigure(col, weight=1)
        self.ttk.Label(schedule, text="Daily time (HH:MM)").grid(row=0, column=0, sticky="w", pady=4)
        self.ttk.Entry(schedule, textvariable=self.run_time, width=12).grid(row=0, column=1, sticky="w", pady=4)
        self.ttk.Label(schedule, text="Lookback hours").grid(row=0, column=2, sticky="w", pady=4)
        self.ttk.Entry(schedule, textvariable=self.lookback_hours, width=12).grid(row=0, column=3, sticky="w", pady=4)

        actions = self.ttk.Frame(main)
        actions.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        self.ttk.Button(actions, text="Save Settings", command=self.save_settings_clicked).pack(side="left", padx=(0, 8))
        self.ttk.Button(actions, text="Run Upload Now", command=self.run_now).pack(side="left", padx=(0, 8))
        self.ttk.Button(actions, text="Install Daily Task", command=self.install_task).pack(side="left", padx=(0, 8))
        self.ttk.Button(actions, textvariable=self.scheduler_btn_text, command=self.toggle_scheduler).pack(side="left")

        log_frame = self.ttk.LabelFrame(main, text="Status", padding=8)
        log_frame.grid(row=6, column=0, sticky="nsew")
        main.rowconfigure(6, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = self.tk.Text(log_frame, height=10, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = self.ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log(f"Config path: {CONFIG_PATH}")

    def show_help(self) -> None:
        win = self.tk.Toplevel(self.root)
        win.title(f"{APP_NAME} — Help")
        win.geometry("640x600")
        win.resizable(True, True)

        frame = self.ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = self.tk.Text(frame, wrap="word", padx=8, pady=8,
                            font=("Segoe UI", 9), relief="flat",
                            background=win.cget("background"))
        text.grid(row=0, column=0, sticky="nsew")
        sb = self.ttk.Scrollbar(frame, command=text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=sb.set)

        text.tag_configure("h1", font=("Segoe UI", 11, "bold"), spacing3=4)
        text.tag_configure("h2", font=("Segoe UI", 9, "bold"), spacing1=8, spacing3=2)
        text.tag_configure("important", font=("Segoe UI", 9, "bold"),
                           foreground="#1a6e1a", spacing1=4, spacing3=4)
        text.tag_configure("warn", font=("Segoe UI", 9, "bold"),
                           foreground="#a05000", spacing1=4)
        text.tag_configure("body", font=("Segoe UI", 9), spacing3=3)
        text.tag_configure("bullet", font=("Segoe UI", 9), lmargin1=18, lmargin2=28, spacing3=3)

        def h1(t):  text.insert("end", t + "\n", "h1")
        def h2(t):  text.insert("end", t + "\n", "h2")
        def imp(t): text.insert("end", t + "\n", "important")
        def warn(t):text.insert("end", t + "\n", "warn")
        def p(t):   text.insert("end", t + "\n", "body")
        def b(t):   text.insert("end", "  • " + t + "\n", "bullet")

        h1("Quick-start checklist")
        b("Step 1 — Enter your BFBM Bet Explorer email and password, then click Connect.")
        b("Step 2 — Click Auto to find your BFBM history file (or use File / Folder).")
        b("Step 3 — Set the daily upload time (e.g. 02:15 for 2:15 AM).")
        b("Step 4 — Click Install Daily Task. Once installed you can usually close this app.")
        p("")

        imp("✔  After 'Install Daily Task' the upload runs automatically each day.")
        p("The task is registered with Windows Task Scheduler and is set to run whether you "
          "are logged in or not, so uploads happen automatically at the configured time — "
          "even when the app is closed or the machine is locked.")
        warn("On some locked-down VPS setups Windows only allows tasks that run WHILE you are "
             "logged in. If uploads are not happening overnight, either stay logged in to the "
             "VPS, or use the \"Run in Background\" button below and leave the app open.")
        p("")

        h1("Section guide")

        h2("1. Connect Account")
        b("API URL — the address of your BFBM Bet Explorer dashboard. "
          "The default (https://bfbmbetexplorer.com/api) is correct; do not change it.")
        b("Email / Password — your dashboard login credentials. "
          "Your password is never stored on disk; only a secure upload token is saved.")
        b("Connect — logs you in and generates an upload token. "
          "Once connected the \"Connected (...)\" label shows the token is active. "
          "You only need to reconnect if you revoke the token from your Account Settings.")
        p("")

        h2("2. CSV Source")
        b("Auto — searches the default BFBM V3 folder for uk_bets_history.gz automatically. "
          "Use this first; it works for most standard BFBM installations.")
        b("File — manually select a single CSV or .gz history file.")
        b("Folder — select a folder; every CSV file inside it will be uploaded.")
        p("The uploader reads only rows settled within the Lookback window so uploads "
          "are fast even for large history files.")
        p("")

        h2("3. Schedule")
        b("Daily time (HH:MM) — the time the automatic task runs each day (24-hour clock). "
          "2:15 AM is recommended as BFBM is unlikely to be placing bets at that hour.")
        b("Lookback hours — how far back in time to include settled bets (default 48 h). "
          "Increase this if you restart your VPS infrequently or want a longer safety net. "
          "528 h (22 days) is safe for very infrequent uploads.")
        p("")

        h2("Buttons")
        b("Save Settings — saves all fields to disk without uploading anything.")
        b("Run Upload Now — immediately uploads recent bets. "
          "Use this to verify everything is working before relying on the daily task.")
        b("Install Daily Task — registers the task with Windows Task Scheduler. "
          "You can close the app straight after this.")
        b("Run in Background — keeps the app open and uploads every day at the set time from "
          "within the app itself. Use this if the scheduled task does not run on your VPS. "
          "The app must stay open for this mode to work; click again to stop it.")
        p("")

        h1("Troubleshooting")

        warn("'Install Daily Task' fails with a non-zero exit status")
        p("This usually means Windows Task Scheduler cannot be accessed from your current "
          "session (common on Virtual Desktop / RDP sessions inside a VPS).")
        b("Try right-clicking the .exe and choosing 'Run as administrator', "
          "then press 'Install Daily Task' again.")
        b("If you are running inside a Virtual Desktop (e.g. multiple BFBM instances via "
          "RDP inside a VPS), run the uploader directly on the host VPS desktop instead "
          "— Task Scheduler is a host-level service and cannot be reached from a "
          "nested virtual desktop session.")
        b("As a fallback, open Windows Task Scheduler (taskschd.msc) on the host machine "
          "and create the task manually with the action: "
          '\"BFBM Bet Explorer Uploader.exe\" run')
        p("")

        warn("The daily task was created but nothing uploaded overnight")
        p("Some Windows/VPS configurations only run scheduled tasks while a user is logged in. "
          "If you disconnect or log off your VPS session, a logged-on-only task will not fire. "
          "This uploader installs the task to run whether you are logged in or not, but if your "
          "system blocks that you have two options:")
        b("Stay logged in to the VPS (disconnect the RDP window without logging off), or")
        b("Click \"Run in Background\" and leave this app open — it uploads daily on its own.")
        p("")

        warn("SSL: CERTIFICATE_VERIFY_FAILED")
        p("This can occur on some Windows Server / VPS environments where Python cannot "
          "locate the system CA certificate store. Download the latest version of the "
          "uploader from your dashboard — newer builds bundle the required certificates.")
        p("")

        warn("'Not connected' after reopening the app")
        p("Your token is saved between sessions. If it shows 'Not connected', the token "
          "may have been revoked from your Account Settings page. "
          "Just enter your email and password and click Connect again.")

        text.configure(state="disabled")
        self.ttk.Button(win, text="Close", command=win.destroy).pack(pady=(0, 12))

    def log(self, message: str) -> None:
        append_log(message)

        def append() -> None:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")

        self.root.after(0, append)

    def choose_file(self) -> None:
        path = self.filedialog.askopenfilename(
            title="Choose BFBM history or CSV",
            filetypes=[
                ("BFBM history / CSV", "uk_bets_history* *.gz *.csv"),
                ("CSV files", "*.csv"),
                ("GZ files", "*.gz"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.source.set(path)

    def choose_folder(self) -> None:
        path = self.filedialog.askdirectory(title="Choose folder containing BFBM CSV files")
        if path:
            self.source.set(path)

    def auto_detect_source(self) -> None:
        path = find_default_bfbm_history()
        if path:
            self.source.set(str(path))
            self.log(f"Detected BFBM history file: {path}")
        else:
            self.messagebox.showinfo(APP_NAME, "Could not find uk_bets_history.gz in the default BFBM local app-data folder.")

    def validate_settings(self) -> dict[str, Any]:
        api_url = self.api_url.get().strip() or DEFAULT_API_URL
        source = self.source.get().strip()
        run_time = self.run_time.get().strip()
        try:
            lookback_hours = int(self.lookback_hours.get().strip())
        except ValueError as exc:
            raise ValueError("Lookback hours must be a number") from exc
        if lookback_hours <= 0:
            raise ValueError("Lookback hours must be greater than zero")
        if run_time and not re.match(r"^\d{2}:\d{2}$", run_time):
            raise ValueError("Daily time must use HH:MM format")

        config = load_config()
        config.update({
            "api_url": api_url,
            "source": source,
            "time": run_time,
            "lookback_hours": lookback_hours,
        })
        return config

    def save_settings(self) -> dict[str, Any]:
        config = self.validate_settings()
        save_config(config)
        self.config = config
        self.token_status.set(self._token_label())
        return config

    def save_settings_clicked(self) -> None:
        try:
            self.save_settings()
            self.log("Settings saved.")
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))

    def connect_account(self) -> None:
        email = self.email.get().strip()
        password = self.password.get()
        if not email or not password:
            self.messagebox.showerror(APP_NAME, "Enter your dashboard email and password.")
            return
        try:
            config = self.validate_settings()
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))
            return

        def work() -> None:
            api_url = config.get("api_url") or DEFAULT_API_URL
            self.log("Connecting account...")
            token = login_and_create_upload_token(api_url, email, password, "Windows VPS uploader")
            config["api_url"] = api_url
            config["token"] = token
            save_config(config)
            self.config = config
            self.root.after(0, self.password.set, "")
            self.root.after(0, self.token_status.set, self._token_label())
            self.log("Account connected. Password was not stored; only the upload token was saved.")

        self.run_background(work)

    def run_now(self) -> None:
        try:
            config = self.save_settings()
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))
            return

        def work() -> None:
            token = config.get("token")
            if not token:
                raise RuntimeError("Connect your account first.")
            if not config.get("source"):
                raise RuntimeError("Choose a CSV source first.")
            self.log("Upload started...")
            run_upload(
                api_url=config.get("api_url") or DEFAULT_API_URL,
                token=token,
                source=config["source"],
                lookback_hours=int(config.get("lookback_hours") or 48),
                timeout=int(config.get("timeout") or DEFAULT_UPLOAD_TIMEOUT),
                settled_only=True,
                log=self.log,
            )
            self.log("Upload finished.")

        self.run_background(work)

    def install_task(self) -> None:
        try:
            config = self.save_settings()
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))
            return

        def work() -> None:
            if os.name != "nt":
                raise RuntimeError("Daily task installation is only available on Windows.")
            if not config.get("time"):
                raise RuntimeError("Enter a daily upload time first.")
            mode = install_daily_task(config["time"])
            if mode == "logged-off":
                self.log(f"Installed daily upload task for {config['time']}.")
                self.log(
                    "This task is set to run whether you are logged in or not — "
                    "you can now close the app and it will still upload daily."
                )
            else:
                self.log(f"Installed daily upload task for {config['time']} (basic mode).")
                self.log(
                    "WARNING: this machine only allows tasks that run while you are logged in. "
                    "Either stay logged in to the VPS, or click \"Run in Background\" and "
                    "keep this app open."
                )

        self.run_background(work)

    def _next_run_dt(self, run_time_str: str) -> datetime:
        hh, mm = (int(x) for x in run_time_str.split(":"))
        now = datetime.now()
        candidate = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def toggle_scheduler(self) -> None:
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_stop.set()
            self.scheduler_btn_text.set("Run in Background")
            self.log("Background scheduler stopped.")
            return

        try:
            config = self.save_settings()
        except Exception as exc:
            self.messagebox.showerror(APP_NAME, str(exc))
            return
        if not config.get("token"):
            self.messagebox.showerror(APP_NAME, "Connect your account first.")
            return
        if not config.get("source"):
            self.messagebox.showerror(APP_NAME, "Choose a CSV source first.")
            return
        if not config.get("time"):
            self.messagebox.showerror(APP_NAME, "Enter a daily upload time first.")
            return

        self._scheduler_stop = threading.Event()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, args=(dict(config),), daemon=True
        )
        self._scheduler_thread.start()
        self.scheduler_btn_text.set("Stop Background Scheduler")
        self.log(
            "Background scheduler started — KEEP THIS APP OPEN. "
            "It will upload every day at the set time while the app stays running."
        )

    def _scheduler_loop(self, config: dict) -> None:
        run_time_str = config.get("time") or ""
        while not self._scheduler_stop.is_set():
            try:
                target = self._next_run_dt(run_time_str)
            except Exception as exc:
                self.log(f"Background scheduler ERROR (bad time '{run_time_str}'): {exc}")
                self.root.after(0, lambda: self.scheduler_btn_text.set("Run in Background"))
                return
            self.log(f"Next background upload scheduled for {target:%Y-%m-%d %H:%M}.")
            while not self._scheduler_stop.is_set():
                remaining = (target - datetime.now()).total_seconds()
                if remaining <= 0:
                    break
                if self._scheduler_stop.wait(min(remaining, 30)):
                    break
            if self._scheduler_stop.is_set():
                break
            try:
                self.log("Background scheduler: starting scheduled upload...")
                run_upload(
                    api_url=config.get("api_url") or DEFAULT_API_URL,
                    token=str(config.get("token") or ""),
                    source=config["source"],
                    lookback_hours=int(config.get("lookback_hours") or 48),
                    timeout=int(config.get("timeout") or DEFAULT_UPLOAD_TIMEOUT),
                    settled_only=True,
                    log=self.log,
                )
                self.log("Background scheduler: upload finished.")
            except Exception as exc:
                self.log(f"Background scheduler ERROR: {exc}")
            # Move past the trigger minute before computing the next day's run.
            self._scheduler_stop.wait(61)

    def run_background(self, func) -> None:
        if self.busy:
            return
        self.busy = True

        def worker() -> None:
            try:
                func()
            except Exception as exc:
                self.log(f"ERROR: {exc}")
                self.root.after(0, lambda: self.messagebox.showerror(APP_NAME, str(exc)))
            finally:
                self.busy = False

        threading.Thread(target=worker, daemon=True).start()


def launch_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except Exception as exc:
        print(f"GUI could not start: {exc}", file=sys.stderr)
        return 1

    root = tk.Tk()
    UploaderGui(root, tk, ttk, filedialog, messagebox)
    root.mainloop()
    return 0


def command_gui(_args: argparse.Namespace) -> int:
    return launch_gui()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload recent BFBM CSV rows to BFBM Bet Explorer.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gui = subparsers.add_parser("gui", help="Open the Windows setup app")
    gui.set_defaults(func=command_gui)

    configure = subparsers.add_parser("configure", help="Save uploader settings")
    configure.add_argument("--api-url", default=None, help=f"API base URL, default {DEFAULT_API_URL}")
    configure.add_argument("--token", default=None, help="Automation token from Account Settings")
    configure.add_argument("--source", default=None, help="CSV file or folder containing CSV files")
    configure.add_argument("--time", default=None, help="Daily upload time for Task Scheduler, HH:MM")
    configure.add_argument("--lookback-hours", type=int, default=None, help="Rows newer than this are uploaded")
    configure.set_defaults(func=command_configure)

    run = subparsers.add_parser("run", help="Upload recent rows now")
    run.add_argument("--api-url", default=None)
    run.add_argument("--token", default=None)
    run.add_argument("--source", default=None)
    run.add_argument("--lookback-hours", type=int, default=None)
    run.add_argument("--timeout", type=int, default=None)
    run.add_argument("--include-matched", action="store_true", help="Upload MATCHED rows too")
    run.set_defaults(func=command_run)

    install = subparsers.add_parser("install-task", help="Install a daily Windows scheduled task")
    install.add_argument("--time", default=None, help="Daily upload time, HH:MM")
    install.add_argument("--task-name", default=None)
    install.set_defaults(func=command_install_task)

    show = subparsers.add_parser("show-config", help="Show saved uploader settings")
    show.set_defaults(func=command_show_config)

    return parser


def main() -> int:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if len(sys.argv) == 1:
        return launch_gui()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        append_log(f"ERROR: {exc}")
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
