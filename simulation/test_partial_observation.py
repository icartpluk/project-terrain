import unittest

from partial_observation import simulate_partial_observation


class PartialObservationTests(unittest.TestCase):
    corridor = ("#########", "#S.....G#", "#########")

    def test_initial_view_marks_unseen_cells_and_exploration_reaches_goal(self):
        result = simulate_partial_observation(self.corridor, sensor_radius=1)
        self.assertEqual(result["status"], "GOAL_REACHED")
        self.assertEqual(result["initial_observation"][1][3], "?")
        self.assertEqual(result["position"], [7, 1])
        self.assertEqual(result["known_map"][1], "#S.....G?")
        self.assertTrue(all(event["newly_observed_cells"] >= 0
                            for event in result["events"]))

    def test_seeded_behavior_is_deterministic(self):
        changes = [{"tick": 2, "position": [2, 1], "blocked": True}]
        first = simulate_partial_observation(
            self.branching_map, sensor_radius=1, obstacle_changes=changes)
        second = simulate_partial_observation(
            self.branching_map, sensor_radius=1, obstacle_changes=changes)
        self.assertEqual(first, second)

    branching_map = (
        "#########",
        "#.......#",
        "#S.###.G#",
        "#.......#",
        "#########",
    )

    def test_newly_observed_obstacle_causes_replan_before_entry(self):
        changed_cell = [2, 1]
        result = simulate_partial_observation(
            self.branching_map, sensor_radius=1,
            obstacle_changes=[{"tick": 2, "position": changed_cell,
                               "blocked": True}],
        )
        self.assertEqual(result["status"], "GOAL_REACHED")
        self.assertIn(
            {"tick": 2, "event": "OBSTACLE_APPEARED", "position": changed_cell},
            result["environment_events"],
        )
        self.assertNotIn(changed_cell, [
            event["position"] for event in result["events"]
            if event["event"] == "MOVE"
        ])
        self.assertEqual(result["environment_map"][1][2], "#")
        self.assertEqual(result["position"], [7, 2])

    def test_disconnected_observed_map_reports_no_known_route(self):
        grid = ("#####", "#S#G#", "#####")
        result = simulate_partial_observation(grid)
        self.assertEqual(result["status"], "NO_KNOWN_ROUTE")
        self.assertEqual(result["moves"], 0)
        self.assertEqual(result["position"], [1, 1])

    def test_invalid_sensor_and_environment_schedules_are_rejected(self):
        for radius in (0, -1, 1.5, True, 11):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                simulate_partial_observation(self.corridor, sensor_radius=radius)
        bad_schedules = (
            [{"tick": 0, "position": [2, 1], "blocked": True}],
            [{"tick": 1, "position": [0, 1], "blocked": True}],
            [{"tick": 1, "position": [2, 1], "blocked": 1}],
            [{"tick": 1, "position": [1, 1], "blocked": True}],
            [{"tick": 1, "position": [2, 1], "blocked": True},
             {"tick": 1, "position": [2, 1], "blocked": False}],
        )
        for schedule in bad_schedules:
            with self.subTest(schedule=schedule), self.assertRaises(ValueError):
                simulate_partial_observation(self.corridor, obstacle_changes=schedule)

    def test_dynamic_obstacle_cannot_block_current_cell(self):
        with self.assertRaisesRegex(ValueError, "current cell"):
            simulate_partial_observation(
                self.corridor,
                obstacle_changes=[{"tick": 2, "position": [2, 1],
                                   "blocked": True}],
            )


if __name__ == "__main__":
    unittest.main()
