import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bfbm_uploader


class BfbmUploaderTests(unittest.TestCase):
    def test_run_upload_diagnostics_are_safe_for_windows_ansi_logs(self) -> None:
        messages: list[str] = []

        def cp1252_log(message: str) -> None:
            message.encode("cp1252", errors="strict")
            messages.append(message)

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "uk_bets_history.csv"
            source.write_text(
                "Status,Settled Date,BetId\n"
                f"SETTLED,{datetime.now():%Y-%m-%d %H:%M:%S},123\n",
                encoding="utf-8",
            )

            with patch.object(
                bfbm_uploader,
                "upload_csv",
                return_value={"inserted": 1, "updated": 0, "skipped": 0},
            ):
                uploaded = bfbm_uploader.run_upload(
                    api_url="https://example.com/api",
                    token="token",
                    source=str(source),
                    log=cp1252_log,
                )

        self.assertEqual(uploaded, 1)
        self.assertTrue(any("Date range" in message for message in messages))


class LookbackValidationTests(unittest.TestCase):
    def test_lookback_hours_must_be_at_least_48(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 48"):
            bfbm_uploader.validate_lookback_hours(47)

    def test_lookback_hours_accepts_48(self) -> None:
        self.assertEqual(bfbm_uploader.validate_lookback_hours(48), 48)


class BuildWindowsScriptTests(unittest.TestCase):
    def test_pyinstaller_failure_stops_before_success_message(self) -> None:
        script = (Path(__file__).resolve().parent / "build_windows.bat").read_text(
            encoding="utf-8"
        )
        pyinstaller_command = (
            "python -m PyInstaller --clean --noconfirm bfbm_uploader.spec"
        )

        self.assertIn(pyinstaller_command, script)
        after_pyinstaller = script.split(pyinstaller_command, 1)[1]
        error_check = after_pyinstaller.find("if errorlevel 1")
        success_message = after_pyinstaller.find("echo Built:")

        self.assertGreaterEqual(error_check, 0)
        self.assertGreaterEqual(success_message, 0)
        self.assertLess(error_check, success_message)


if __name__ == "__main__":
    unittest.main()
