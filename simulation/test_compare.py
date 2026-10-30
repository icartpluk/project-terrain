import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from compare import compare, write_reports


class ComparisonTests(unittest.TestCase):
    def test_route_relative_faults_cap_travel_without_shortening_latency(self):
        grid = ("########", "#S....G#", "########")
        with patch("compare.generate_environment", return_value=grid):
            report = compare(count=1, fault_tick=99, delays=((2, 1),),
                             placements=("last", "middle", "first", "last"))
        self.assertEqual(report["config"]["placements"], ["first", "middle", "last"])
        rows = [r for r in report["trials"] if r["scenario"] == "link_loss" and r["communication_delay"] == 2]
        self.assertEqual([r["scheduled_fault_tick"] for r in rows], [1, 3, 5])
        self.assertEqual([r["remaining_cells"] for r in rows], [5, 3, 1])
        self.assertEqual([r["extra_cells"] for r in rows], [3, 3, 1])
        self.assertEqual([r["latency_ticks"] for r in rows], [3, 3, 3])
        self.assertEqual([r["goal_at_stop"] for r in rows], [False, True, True])
        self.assertEqual([r["fault_position"] for r in rows], [[1, 1], [3, 1], [5, 1]])
        self.assertEqual(len(report["summary"]), 18)

    def test_short_and_blocked_routes_keep_placement_denominators_separate(self):
        grids = [("####", "#SG#", "####"), ("#####", "#S#G#", "#####")]
        with patch("compare.generate_environment", side_effect=grids):
            report = compare(count=2, fault_tick=99, placements=("fixed", "first", "middle", "last"))
        for row in report["summary"]:
            self.assertEqual(row["no_route"], 1)
            self.assertEqual(row["injected"], 0 if row["placement"] == "fixed" else 1)
            self.assertEqual(row["fault_after_arrival"], 1 if row["placement"] == "fixed" else 0)
        for trial in report["trials"]:
            if trial["fault_injected"]:
                self.assertEqual(trial["remaining_cells"], 1)
                self.assertLessEqual(trial["extra_cells"], 1)

    def test_paired_maps_and_honest_denominators(self):
        grids = [("########", "#S....G#", "########"),
                 ("#####", "#S#G#", "#####"), ("####", "#SG#", "####")]
        with patch("compare.generate_environment", side_effect=grids):
            report = compare(count=3, seed=42, fault_tick=2, delays=((2, 1),))
        self.assertEqual(len(report["trials"]), 18)
        self.assertEqual([w["seed"] for w in report["worlds"]], [42, 43, 44])
        for row in report["summary"]:
            self.assertEqual((row["maps"], row["injected"], row["no_route"], row["fault_after_arrival"]),
                             (3, 1, 1, 1))
            expected = (0 if row["communication_delay"] == 0 else
                        1 if row["scenario"] == "estop" else 3)
            self.assertEqual(row["mean_extra_cells"], expected)
            self.assertEqual(row["max_extra_cells"], expected)
            self.assertEqual(row["mean_latency_ticks"], expected)
        moving = [r for r in report["trials"] if r["environment_seed"] == 42]
        self.assertTrue(all(r["fault_position"] == [2, 1] for r in moving))
        self.assertEqual({tuple(r["stop_position"]) for r in moving}, {(2, 1), (3, 1), (5, 1)})
        excluded = [r for r in report["trials"] if not r["fault_injected"]]
        self.assertTrue(all(r["extra_cells"] is None and r["latency_ticks"] is None for r in excluded))

    def test_no_injections_have_null_means_not_perfect_responses(self):
        with patch("compare.generate_environment", return_value=("#####", "#S#G#", "#####")):
            report = compare(count=1)
        for row in report["summary"]:
            self.assertIsNone(row["mean_latency_ticks"])
            self.assertIsNone(row["mean_extra_cells"])
            self.assertIsNone(row["max_extra_cells"])
            self.assertEqual(row["injected"], 0)
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, directory)
            self.assertIn("—", (Path(directory)/"report.html").read_text(encoding="utf-8"))

    def test_reproducibility_and_baseline_deduplication(self):
        first = compare(count=3, delays=((2, 1), (0, 0), (2, 1)))
        second = compare(count=3, delays=((0, 0), (2, 1)))
        self.assertEqual(first, second)
        self.assertEqual(first["config"]["delays"], [[0, 0], [2, 1]])
        self.assertEqual(len(first["trials"]), 18)

    def test_csv_json_and_cli(self):
        script = str(Path(__file__).with_name("compare.py"))
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, script, "--maps", "2", "--delays", "2:1",
                            "--output", directory], check=True, capture_output=True)
            output = Path(directory)
            report = json.loads((output/"comparison.json").read_text(encoding="utf-8"))
            with (output/"summary.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 6)
            self.assertEqual([int(r["injected"]) for r in rows],
                             [r["injected"] for r in report["summary"]])
            with (output/"trials.csv").open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 12)
            html = (output/"report.html").read_text(encoding="utf-8")
            self.assertIn("first seed 20261030", html)
            self.assertIn('href="summary.csv"', html)
            for args in (["--maps", "0"], ["--delays", "bad"], ["--delays", "2:101"], ["--placements", "unknown"]):
                invalid = subprocess.run([sys.executable, script, *args], capture_output=True)
                self.assertNotEqual(invalid.returncode, 0)

    def test_invalid_configuration(self):
        for kwargs in (dict(count=0), dict(count=1001), dict(count=True), dict(seed="42"),
                       dict(fault_tick=0), dict(fault_tick=1.5), dict(delays=[]),
                       dict(delays=[(2,)]), dict(delays=[(-1, 0)]), dict(delays=[(True, 0)]),
                       dict(placements=[]), dict(placements=["unknown"])):
            with self.assertRaises(ValueError):
                compare(**kwargs)


if __name__ == "__main__":
    unittest.main()
