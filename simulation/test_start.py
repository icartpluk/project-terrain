import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import webbrowser

from start import start


class StartTests(unittest.TestCase):
    def test_default_generates_dashboard_and_opens_file_uri_with_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "folder with spaces" / "demo.html"
            with patch("start.webbrowser.open", return_value=True) as browser:
                result = start(target)
            self.assertTrue(result.is_file())
            browser.assert_called_once_with(target.resolve().as_uri())
            html = result.read_text(encoding="utf-8")
            payload = html.split('<script id="simulation-data" type="application/json">')[1].split("</script>")[0]
            self.assertEqual(len(json.loads(payload)["trials"]), 4)
            self.assertIn("Operations view", html)
            self.assertNotIn("__SIMULATION_DATA__", html)

    def test_detailed_replay_remains_available_on_request(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "detailed.html"
            start(target, open_browser=False, detailed_replay=True)
            html = target.read_text(encoding="utf-8")
            payload = html.split('<script id="replay-data" type="application/json">')[1].split("</script>")[0]
            self.assertEqual(len(json.loads(payload)["maps"]), 21)
            self.assertNotIn("__EDITOR_CODE__", html)

    def test_browser_failure_preserves_usable_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "demo.html"
            for failure in (False, webbrowser.Error("unavailable"), OSError("unavailable")):
                with patch("start.webbrowser.open", side_effect=failure if isinstance(failure, Exception) else None,
                           return_value=False), patch("builtins.print") as messages:
                    start(target)
                self.assertTrue(target.is_file())
                self.assertTrue(any("manually" in str(call) for call in messages.call_args_list))

    def test_cli_generates_without_browser_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "demo.html"
            subprocess.run([sys.executable, str(Path(__file__).with_name("start.py").resolve()),
                            "--no-open", "--output", str(target)],
                           cwd=directory, check=True, capture_output=True)
            self.assertTrue(target.is_file())
            html = target.read_text(encoding="utf-8")
            self.assertIn('<script id="simulation-data" type="application/json">', html)

    def test_cli_keeps_detailed_replay_as_an_explicit_option(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "detailed.html"
            subprocess.run(
                [sys.executable, str(Path(__file__).with_name("start.py").resolve()),
                 "--no-open", "--detailed-replay", "--output", str(target)],
                cwd=directory, check=True, capture_output=True,
            )
            html = target.read_text(encoding="utf-8")
            payload = html.split('<script id="replay-data" type="application/json">')[1].split("</script>")[0]
            self.assertEqual(len(json.loads(payload)["maps"]), 21)


if __name__ == "__main__":
    unittest.main()
