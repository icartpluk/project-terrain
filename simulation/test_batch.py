import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path

from batch import generate_environment, run_trials, summarize
from sim import locate, plan, simulate


class BatchTests(unittest.TestCase):
    def test_seeded_worlds_and_boundaries(self):
        self.assertEqual(generate_environment(42), generate_environment(42))
        self.assertNotEqual(generate_environment(42), generate_environment(43))
        for seed in range(20):
            grid = generate_environment(seed)
            self.assertEqual(set(grid[0] + grid[-1]), {"#"})
            self.assertTrue(all(row[0] == row[-1] == "#" for row in grid))
            self.assertEqual("".join(grid).count("S"), 1)
            self.assertEqual("".join(grid).count("G"), 1)
            self.assertLessEqual(set("".join(grid)), set("#.OSG"))

    def test_planner_against_independent_breadth_first_search(self):
        for seed in range(20):
            grid = generate_environment(seed)
            start, goal = locate("S", grid), locate("G", grid)
            queue = deque([(start, 0)])
            seen = {start}
            expected = None
            while queue:
                (x, y), distance = queue.popleft()
                if (x, y) == goal:
                    expected = distance
                    break
                for nx, ny in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                    if (0 <= ny < len(grid) and 0 <= nx < len(grid[ny])
                            and grid[ny][nx] != "#" and (nx, ny) not in seen):
                        seen.add((nx, ny))
                        queue.append(((nx, ny), distance + 1))
            path = plan(start, goal, grid)
            self.assertEqual(len(path)-1 if path else None, expected)
            for a, b in zip(path, path[1:]):
                self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]), 1)
                self.assertNotEqual(grid[b[1]][b[0]], "#")

    def test_no_route_is_reported(self):
        grid = generate_environment(1, obstacle_density=1)
        for scenario in ("normal", "link_loss", "estop", "unauthorized"):
            result = simulate(scenario, 1, grid)
            self.assertEqual(result["status"], "NO_ROUTE")
            self.assertEqual(result["moves"], 0)
            self.assertFalse(result["safe_stop"])

    def test_faults_first_final_and_after_arrival(self):
        grid = ("#####", "#S.G#", "#####")
        for scenario in ("link_loss", "estop", "unauthorized"):
            for tick in (1, 2):
                result = simulate(scenario, tick, grid)
                self.assertTrue(result["safe_stop"])
                self.assertEqual(result["moves"], tick-1)
                self.assertFalse(result["reached_goal"])
                self.assertEqual(result["events"][-1]["tick"], tick)
            self.assertTrue(simulate(scenario, 3, grid)["reached_goal"])
        with self.assertRaises(ValueError):
            simulate(fault_tick=0)

    def test_batch_reproducibility_and_fault_denominators(self):
        results = run_trials()
        self.assertEqual(results, run_trials())
        self.assertEqual(len(results), 100)
        self.assertEqual(len({r["environment_seed"] for r in results}), 100)
        for summary in summarize(results)[1:]:
            self.assertEqual(summary["trials"], 25)
        for scenario in ("link_loss", "estop", "unauthorized"):
            injected = [r for r in results if r["scenario"] == scenario and r["fault_injected"]]
            self.assertTrue(injected)
            self.assertTrue(all(r["fault_response_pass"] for r in injected))
        unreachable = [r for r in results if r["status"] == "NO_ROUTE"]
        self.assertTrue(unreachable)
        self.assertTrue(all(r["fault_response_pass"] is None for r in unreachable))
        total = summarize(results)[0]
        self.assertEqual(total["success_rate"], sum(r["reached_goal"] for r in results)/100)
        self.assertEqual(total["fault_injections"], sum(r["fault_injected"] for r in results))

    def test_reports_and_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(Path(__file__).with_name("batch.py")),
                            "--output", directory], check=True, capture_output=True)
            output = Path(directory)
            with (output/"trials.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 100)
            raw = json.loads((output/"trials.json").read_text(encoding="utf-8"))
            self.assertEqual([int(r["navigation_distance"]) for r in rows],
                             [r["moves"] for r in raw])
            with (output/"summary.csv").open(encoding="utf-8", newline="") as stream:
                summary = list(csv.DictReader(stream))
            self.assertEqual(int(summary[0]["trials"]), 100)
            self.assertEqual(float(summary[0]["success_rate"]), summarize(raw)[0]["success_rate"])

    def test_invalid_configuration(self):
        for kwargs in (dict(width=4), dict(height=3), dict(obstacle_density=-.1),
                       dict(obstacle_density=1.1)):
            with self.assertRaises(ValueError):
                generate_environment(1, **kwargs)
        with self.assertRaises(ValueError):
            run_trials(0)


if __name__ == "__main__":
    unittest.main()
