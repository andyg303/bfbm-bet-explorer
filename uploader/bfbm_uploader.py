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
import threading
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
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Upload failed with HTTP {exc.code}: {detail}") from exc


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
        with urllib.request.urlopen(request, timeout=timeout) as response:
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
    timeout: int = 180,
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
        result = upload_csv(api_url, token, upload_name, payload, timeout)
        uploaded += len(filtered)
        log(
            f"{path.name}: uploaded {len(filtered)} rows; "
            f"inserted={result.get('inserted', 0)} "
            f"updated={result.get('updated', 0)} "
            f"skipped={result.get('skipped', 0)}"
        )

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
    timeout = int(args.timeout or config.get("timeout") or 180)
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
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" run'
    return f'"{sys.executable}" "{Path(__file__).resolve()}" run'


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
    cmd = [
        "schtasks",
        "/Create",
        "/TN",
        task_name,
        "/SC",
        "DAILY",
        "/ST",
        run_time,
        "/TR",
        task_command(),
        "/F",
    ]
    subprocess.run(cmd, check=True)
    print(f"Installed daily task '{task_name}' at {run_time}")
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
        self.ttk.Button(actions, text="Install Daily Task", command=self.install_task).pack(side="left")

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
                timeout=int(config.get("timeout") or 180),
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
            cmd = [
                "schtasks",
                "/Create",
                "/TN",
                DEFAULT_TASK_NAME,
                "/SC",
                "DAILY",
                "/ST",
                config["time"],
                "/TR",
                task_command(),
                "/F",
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.log(f"Installed daily upload task for {config['time']}.")

        self.run_background(work)

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
