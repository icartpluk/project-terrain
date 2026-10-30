import unittest
from sim import simulate
from timing import simulate_timed
from animate import map_collection


class TimingTests(unittest.TestCase):
    grid = ("########", "#S....G#", "########")

    def test_zero_delays_preserve_existing_behavior(self):
        for scenario in ("normal", "link_loss", "estop", "unauthorized"):
            for tick in (1, 3, 5, 6):
                result = simulate_timed(scenario, tick, self.grid)
                result.pop("timing")
                self.assertEqual(result, simulate(scenario, tick, self.grid))

    def test_known_distance_and_latency(self):
        result = simulate_timed("link_loss", 2, self.grid, 2, 1)
        self.assertEqual(result["final_position"], [5, 1])
        self.assertEqual(result["moves"], 4)
        self.assertEqual(result["timing"]["moves_after_fault"], 3)
        self.assertEqual(result["timing"]["stop_tick"], 5)
        self.assertEqual([e.get("phase") for e in result["events"]],
                         [None, "COMMUNICATION_DELAY", "COMMUNICATION_DELAY", "STOPPING_DELAY", None])

    def test_estop_bypasses_communication_delay(self):
        result = simulate_timed("estop", 2, self.grid, 9, 1)
        self.assertEqual(result["timing"]["latency_ticks"], 1)
        self.assertEqual(result["timing"]["moves_after_fault"], 1)
        self.assertEqual(result["final_position"], [3, 1])

    def test_arrival_during_delay_waits_for_stop_without_overshoot(self):
        result = simulate_timed("unauthorized", 5, self.grid, 2, 2)
        self.assertTrue(result["safe_stop"])
        self.assertTrue(result["reached_goal"])
        self.assertEqual(result["final_position"], [6, 1])
        self.assertEqual(result["timing"]["moves_after_fault"], 1)
        self.assertEqual(result["events"][-1]["tick"], 9)
        self.assertEqual([e["event"] for e in result["events"][-5:-1]],
                         ["MOVE", "WAIT", "WAIT", "WAIT"])

    def test_no_route_and_late_fault_do_not_claim_stop(self):
        for grid, tick in ((self.grid, 6), (("#####", "#S#G#", "#####"), 1)):
            result = simulate_timed("link_loss", tick, grid, 2, 2)
            self.assertFalse(result["safe_stop"])
            self.assertIsNone(result["timing"]["fault_tick"])
            self.assertEqual(result["timing"]["moves_after_fault"], 0)

    def test_invalid_delays(self):
        for value in (-1, 101, 1.5, True, "2"):
            for field in ("communication_delay", "stopping_delay"):
                with self.assertRaises(ValueError):
                    simulate_timed(**{field: value})

    def test_exported_maps_use_timed_python_results(self):
        bank = map_collection(maps=2, communication_delay=2, stopping_delay=1)
        for world in bank["maps"]:
            self.assertEqual(world["communication_delay"], 2)
            for result in world["trials"]:
                self.assertEqual(result, simulate_timed(result["scenario"], 8, world["grid"], 2, 1))
