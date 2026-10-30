# Inert grid simulation

A standard-library Python model of a generic robot moving through a fictional underground grid. No hardware, Tesla API, network service, or physics engine is used.

## Watch the animation

From the repository root with Python 3.11 or newer:

```sh
python simulation/animate.py
```

Open `results/animation.html` in a modern web browser by double-clicking it. No packages, server, or internet connection are needed. On Windows, `py` can be used in place of `python` if that is how Python is installed.

Choose **Normal navigation**, **Link loss**, **E-stop**, or **Unauthorized command**, then click **Play**. Use **Pause**, **Step**, **Reset**, the tick slider, and the tick duration selector to inspect the replay. The map shows obstacles, start S, destination G, the traveled path, and robot R. A stopped robot becomes a red `!`, with a persistent **SAFE STOP** banner naming the cause. Text labels distinguish states without relying on color.

The replay uses `sim.py`'s actual recorded events, including its stop-before-move behavior. It never advances beyond the last recorded event. Reset and scenario selection start a new replay; they do not clear a live robot fault.

The fixed map and default fault tick 8 make every export reproducible:

```sh
python simulation/animate.py --fault-tick 3 --output results/early-stop.html
```

Tick 1 stops before the first move. A fault scheduled after arrival is not injected; the display reports GOAL REACHED instead of claiming a safety stop. An unreachable map reports NO ROUTE. This exporter uses the fixed demonstration map; randomized trials remain available through `batch.py`.

## Run tests and reports

```sh
python -m unittest discover -s simulation -v
python simulation/sim.py --output results/baseline
python simulation/batch.py --trials 100 --seed 20261030 --output results/randomized
```

Tests cover recorded replay data, stop positions at first/intermediate/final motion ticks, late faults, unreachable goals, repeatability, HTML export, and CLI validation alongside the existing navigation and batch tests.

CI also checks the JavaScript playback controller with Node.js and a minimal DOM stub (no packages). To run that optional developer check locally after generating the animation: `node simulation/test_replay.cjs`. It covers play/pause, stepping, reset, seeking, all three persistent stops, and arrival. It checks controller behavior; browser rendering still requires a visual check.

See [PROTOTYPE.md](PROTOTYPE.md) and [RANDOMIZED.md](RANDOMIZED.md) for the underlying model and reports. All positions and times are idealized grid cells and ticks; the animation demonstrates software behavior, not physical stopping performance. Only inert objects and generic environments are modeled.

