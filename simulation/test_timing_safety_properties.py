"""Safety-property regression cases for the inert delayed-fault model."""
import unittest

from sim import locate, simulate
from timing import simulate_timed


class TimedSafetyPropertyTests(unittest.TestCase):
    # Short deterministic fixture: four moves, with no obstacles or randomness.
    grid = ("#######", "#S...G#", "#######")
    scenarios = {
        "link_loss": "COMMUNICATION_LOSS",
        "estop": "EMERGENCY_STOP",
        "unauthorized": "UNAUTHORIZED_COMMAND",
    }

    def test_fault_at_each_motion_tick_preserves_stop_and_path_invariants(self):
        baseline = simulate("normal", grid=self.grid)
        path = [list(locate("S", self.grid))]
        path.extend(event["position"] for event in baseline["events"])
        steps = baseline["planned_steps"]

        # Include zero, asymmetric, and maximum supported delay combinations.
        delays = ((0, 0), (1, 0), (0, 2), (3, 2), (100, 100))
        for scenario, reason in self.scenarios.items():
            for fault_tick in range(1, steps + 1):
                for communication_delay, stopping_delay in delays:
                    with self.subTest(
                        scenario=scenario,
                        fault_tick=fault_tick,
                        communication_delay=communication_delay,
                        stopping_delay=stopping_delay,
                    ):
                        result = simulate_timed(
                            scenario,
                            fault_tick,
                            self.grid,
                            communication_delay,
                            stopping_delay,
                        )
                        timing = result["timing"]
                        detection = 0 if scenario == "estop" else communication_delay
                        latency = detection + stopping_delay
                        expected_moves = min(
                            steps, fault_tick - 1 + latency
                        )

                        self.assertTrue(result["safe_stop"])
                        self.assertEqual(result["status"], "SAFE_STOP")
                        self.assertEqual(timing["fault_tick"], fault_tick)
                        self.assertEqual(timing["latency_ticks"], latency)
                        self.assertEqual(
                            timing["moves_after_fault"],
                            expected_moves - (fault_tick - 1),
                        )
                        self.assertEqual(result["moves"], expected_moves)
                        self.assertEqual(
                            result["final_position"], path[expected_moves]
                        )
                        self.assertEqual(result["events"][-1]["event"], reason)
                        self.assertEqual(
                            result["events"][-1]["tick"],
                            fault_tick + latency,
                        )
                        self.assertEqual(
                            result["events"][-1]["position"],
                            result["final_position"],
                        )

    def test_estop_ignores_maximum_communication_delay(self):
        result = simulate_timed(
            "estop", 1, self.grid, communication_delay=100, stopping_delay=0
        )

        self.assertEqual(result["timing"]["latency_ticks"], 0)
        self.assertEqual(result["timing"]["moves_after_fault"], 0)
        self.assertEqual(result["moves"], 0)
        self.assertEqual(result["final_position"], [1, 1])
        self.assertEqual(result["events"][-1]["event"], "EMERGENCY_STOP")

    def test_one_move_route_can_reach_goal_during_delay_but_remains_faulted(self):
        one_move_grid = ("#####", "#SG.#", "#####")
        result = simulate_timed(
            "link_loss",
            1,
            one_move_grid,
            communication_delay=1,
            stopping_delay=1,
        )

        self.assertTrue(result["safe_stop"])
        self.assertTrue(result["reached_goal"])
        self.assertEqual(result["status"], "SAFE_STOP")
        self.assertEqual(result["timing"]["moves_after_fault"], 1)
        self.assertEqual(result["events"][-1]["event"], "COMMUNICATION_LOSS")

    def test_fault_after_arrival_is_not_reported_as_injected(self):
        result = simulate_timed(
            "link_loss", 5, self.grid, communication_delay=100,
            stopping_delay=100,
        )

        self.assertEqual(result["status"], "GOAL_REACHED")
        self.assertFalse(result["safe_stop"])
        self.assertIsNone(result["timing"]["fault_tick"])
        self.assertEqual(result["timing"]["moves_after_fault"], 0)

    def test_maximum_delay_waits_at_goal_without_overshoot_and_is_repeatable(self):
        first = simulate_timed(
            "unauthorized", 1, self.grid, communication_delay=100,
            stopping_delay=100,
        )
        second = simulate_timed(
            "unauthorized", 1, self.grid, communication_delay=100,
            stopping_delay=100,
        )

        self.assertEqual(first, second)
        self.assertEqual(first["timing"]["latency_ticks"], 200)
        self.assertEqual(first["timing"]["moves_after_fault"], 4)
        self.assertEqual(first["moves"], 4)
        self.assertEqual(first["final_position"], [5, 1])
        self.assertTrue(first["reached_goal"])
        self.assertTrue(first["safe_stop"])
        self.assertEqual(first["events"][-1]["tick"], 201)
        self.assertEqual(
            sum(event["event"] == "WAIT" for event in first["events"]), 196
        )


if __name__ == "__main__":
    unittest.main()
