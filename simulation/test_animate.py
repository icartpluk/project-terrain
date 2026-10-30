import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from animate import map_collection, render_html, replay_data
from batch import generate_environment
from sim import locate, plan, simulate


class AnimationTests(unittest.TestCase):
    def test_seeded_maps_match_existing_generator_and_safety_events(self):
        bank = map_collection(seed=42, maps=4)
        self.assertEqual(bank, map_collection(seed=42, maps=4))
        self.assertEqual(len(bank["maps"]), 5)
        for offset, world in enumerate(bank["maps"][1:]):
            grid = generate_environment(42 + offset)
            self.assertEqual(world["seed"], 42 + offset)
            self.assertEqual(world["grid"], list(grid))
            for trial in world["trials"]:
                self.assertEqual(trial, simulate(trial["scenario"], 8, grid))
        self.assertNotEqual(bank["maps"][1]["grid"], bank["maps"][2]["grid"])
        for count in (0, 101):
            with self.assertRaises(ValueError):
                map_collection(maps=count)

    def test_reproducible_replay_matches_simulation(self):
        data = replay_data()
        self.assertEqual(data, replay_data())
        self.assertEqual(data["start"], list(locate("S")))
        for trial in data["trials"]:
            self.assertEqual(trial, simulate(trial["scenario"]))
        self.assertEqual(data["trials"][0]["final_position"], list(locate("G")))

    def test_stop_frames_never_move_after_fault(self):
        path = plan(locate("S"), locate("G"))
        for tick in (1, 8, len(path) - 1):
            for trial in replay_data(tick)["trials"][1:]:
                self.assertEqual(trial["status"], "SAFE_STOP")
                self.assertEqual(trial["events"][-1]["position"], list(path[tick-1]))
                self.assertEqual(trial["events"][-1]["tick"], tick)
                self.assertEqual(len(trial["events"]), tick)
                self.assertEqual(trial["moves"], tick-1)

    def test_unreachable_map_and_late_fault(self):
        grid = ("#####", "#S#G#", "#####")
        self.assertTrue(all(t["status"] == "NO_ROUTE" and not t["events"]
                            for t in replay_data(grid=grid)["trials"]))
        self.assertTrue(all(t["status"] == "GOAL_REACHED"
                            for t in replay_data(1000)["trials"]))
        with self.assertRaises(ValueError):
            replay_data(0)

    def test_cli_embeds_complete_data_and_rejects_invalid_tick(self):
        script = str(Path(__file__).with_name("animate.py"))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "animation.html"
            subprocess.run([sys.executable, script, "--output", str(target)],
                           check=True, capture_output=True)
            html = target.read_text(encoding="utf-8")
            payload = html.split('<script id="replay-data" type="application/json">')[1].split('</script>')[0]
            self.assertEqual(json.loads(payload), map_collection())
            self.assertNotIn("__REPLAY_DATA__", html)
            self.assertNotIn('<script src=', html)
            invalid = subprocess.run([sys.executable, script, "--fault-tick", "0"], capture_output=True)
            self.assertNotEqual(invalid.returncode, 0)
            subprocess.run([sys.executable, script, "--seed", "42", "--maps", "2",
                            "--output", str(target)], check=True, capture_output=True)
            html = target.read_text(encoding="utf-8")
            payload = html.split('<script id="replay-data" type="application/json">')[1].split('</script>')[0]
            self.assertEqual(json.loads(payload), map_collection(seed=42, maps=2))
            invalid = subprocess.run([sys.executable, script, "--maps", "0"], capture_output=True)
            self.assertNotEqual(invalid.returncode, 0)

    def test_embedded_data_cannot_close_script(self):
        self.assertIn('\\u003c/script>', render_html({"grid": ["</script>"]}))


if __name__ == "__main__":
    unittest.main()
