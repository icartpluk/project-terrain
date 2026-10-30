import unittest
from sim import GRID, locate, plan, simulate

class SimulationTests(unittest.TestCase):
    def test_path_is_valid(self):
        path=plan(locate("S"),locate("G"))
        self.assertGreater(len(path),1)
        for a,b in zip(path,path[1:]):
            self.assertEqual(abs(a[0]-b[0])+abs(a[1]-b[1]),1)
            self.assertNotEqual(GRID[b[1]][b[0]],"#")

    def test_normal_arrives(self):
        r=simulate("normal")
        self.assertEqual(r["status"],"GOAL_REACHED")
        self.assertTrue(r["reached_goal"])

    def test_faults_stop_before_moving(self):
        for scenario in ("link_loss","estop","unauthorized"):
            with self.subTest(scenario=scenario):
                r=simulate(scenario,3)
                self.assertEqual(r["status"],"SAFE_STOP")
                self.assertEqual(r["moves"],2)
                self.assertFalse(r["reached_goal"])
                self.assertEqual(r["events"][-1]["tick"],3)

    def test_invalid_scenario(self):
        with self.assertRaises(ValueError): simulate("unknown")

if __name__=="__main__":
    unittest.main()
