# Project TERRAIN — runnable inert simulation

This is a **small Python grid-world demonstration**, not a Tesla Optimus simulator or a validated robotics safety controller. It models generic navigation and idealized fault handling in a fictional underground maze. It contains no nuclear material or real-site model.

## Run

Python 3.9+; no third-party packages.

```bash
cd simulation
python sim.py --output results
python -m unittest -v test_sim.py
```

Outputs: `results/summary.csv` and `results/trials.json`. Default fault injection is at tick 8; change with `--fault-tick N`.

## Local baseline test results

Four unit tests passed in a local execution of the prototype. In the default fictional maze, the normal run reached its goal in **17 moves**. Each of three injected scenarios—communication loss, emergency stop, and unauthorized command—stopped after **7 moves** before the eighth move.

These results demonstrate only the Python model's programmed logic. They do **not** establish robot reliability, physical stopping time, cyber resilience, or nuclear-recovery feasibility.

## Next engineering steps

Add randomized inert maps, multi-run statistics, independent safety-state modeling, simulated delays, and benchmark comparisons with alternative robot platforms. Preserve all failures and document assumptions.
