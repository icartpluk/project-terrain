import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "presentation"))

from build import render_html, simulation_payload  # noqa: E402
from sim import GRID, locate, simulate  # noqa: E402


class PresentationTests(unittest.TestCase):
    def test_dashboard_payload_is_the_canonical_simulation_output(self):
        for fault_tick in (1, 8, 1000):
            payload = simulation_payload(fault_tick)
            self.assertEqual(payload["grid"], list(GRID))
            self.assertEqual(payload["start"], list(locate("S", GRID)))
            self.assertEqual(
                payload["trials"],
                [simulate(name, fault_tick, GRID) for name in
                 ("normal", "link_loss", "estop", "unauthorized")],
            )
            self.assertEqual(payload, simulation_payload(fault_tick))

    def test_committed_dashboard_is_reproducibly_generated_and_uses_embedded_data(self):
        payload = simulation_payload()
        html = render_html(payload)
        dashboard = ROOT / "presentation" / "index.html"
        self.assertEqual(dashboard.read_text(encoding="utf-8"), html)
        embedded = html.split(
            '<script id="simulation-data" type="application/json">', 1
        )[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(embedded), payload)
        self.assertNotIn("__SIMULATION_DATA__", html)
        self.assertNotIn("const path=[", html)
        self.assertNotIn("Trigger link loss", html)

    def test_exporter_writes_deterministic_self_contained_dashboard(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "operations.html"
            subprocess.run(
                [sys.executable, str(ROOT / "presentation" / "build.py"),
                 "--output", str(output)], check=True, capture_output=True, text=True,
            )
            self.assertEqual(output.read_text(encoding="utf-8"), render_html(simulation_payload()))
            invalid = subprocess.run(
                [sys.executable, str(ROOT / "presentation" / "build.py"),
                 "--output", str(output), "--fault-tick", "0"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main()
