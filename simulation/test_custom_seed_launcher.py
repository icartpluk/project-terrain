"""Regression checks for reproducible custom-seed launch options."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from start import start


class CustomSeedLauncherTests(unittest.TestCase):
    def payload(self, path, detailed=False):
        html = path.read_text(encoding="utf-8")
        marker = ('<script id="replay-data" type="application/json">'
                  if detailed else '<script id="simulation-data" type="application/json">')
        return json.loads(html.split(marker, 1)[1].split("</script>", 1)[0])

    def test_custom_seed_bank_reproducible_in_both_views(self):
        with tempfile.TemporaryDirectory() as folder:
            for detailed in (False, True):
                first = Path(folder) / "first.html"
                second = Path(folder) / "second.html"
                start(first, False, detailed, seed=42, maps=3, fault_tick=2)
                start(second, False, detailed, seed=42, maps=3, fault_tick=2)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                data = self.payload(first, detailed)
                worlds = data["maps"] if detailed else data["worlds"]
                self.assertEqual(len(worlds), 4)
                self.assertEqual([w["seed"] for w in worlds[1:]], [42, 43, 44])
                self.assertTrue(all(w["fault_tick"] == 2 for w in worlds))

    def test_invalid_options_do_not_write_output(self):
        with tempfile.TemporaryDirectory() as folder:
            for opts in ({"maps": 0}, {"maps": 101}, {"fault_tick": 0},
                         {"seed": True}, {"maps": 1.5}):
                target = Path(folder) / "invalid.html"
                with self.assertRaises(ValueError):
                    start(target, False, **opts)
                self.assertFalse(target.exists())

    def test_cli_custom_seed_and_rejects_bad_map_count(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "custom.html"
            script = str(Path(__file__).with_name("start.py").resolve())
            subprocess.run([sys.executable, script, "--no-open", "--seed", "42",
                            "--maps", "2", "--fault-tick", "3", "--output",
                            str(target)], check=True, capture_output=True)
            worlds = self.payload(target)["worlds"]
            self.assertEqual([w["seed"] for w in worlds[1:]], [42, 43])
            self.assertEqual(worlds[1]["fault_tick"], 3)
            bad = subprocess.run([sys.executable, script, "--no-open",
                                  "--maps", "101", "--output", str(target)],
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("--maps", bad.stderr)


if __name__ == "__main__":
    unittest.main()
