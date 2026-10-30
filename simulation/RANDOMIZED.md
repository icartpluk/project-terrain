# Randomized fictional underground trials

This extends the fixed-maze prototype; the existing documentation and baseline
report remain historical records. Python 3.9+ and the standard library suffice.

From the repository root:

```bash
python -m unittest discover -s simulation -v
python simulation/batch.py --trials 100 --seed 20261030 --output simulation/reports/randomized-100
```

The original four-scenario CLI remains available as `python simulation/sim.py`.

## Model and reproducibility

Each trial creates a fictional 21-by-17 bounded training grid using its recorded
integer environment seed (base seed plus zero-based trial index). Interior cells
are blocked independently with probability 0.28. Walls represent abstract tunnel
boundaries or harmless foam blocks. Up to five traversable O cells represent
inert foam markers. S and G mark opposite interior corners. No real facility,
hazardous object, robot hardware, sensing, or manipulation is modeled.

The existing shortest-path planner uses complete map knowledge and four cardinal
unit moves. Distance is in grid cells, with no assumed physical scale. Routes are
not repaired: disconnected goals are reported as NO_ROUTE with zero distance.
The JSON retains every generated map, seed, motion event, and fault event.

Scenarios cycle through normal, link_loss, estop, and unauthorized, giving 25
trials per scenario by default. Each fault scenario with a route receives one
seeded random fault tick between the first and last planned moves, inclusive.
The controller stops before the move at that tick and stays stopped for the rest
of the trial. Communication loss models complete command-link interruption.
Emergency stop and unauthorized-command rejection retain the prototype logic.
There is no automatic restart.

## Report definitions

- trials.csv: one row per attempted trial, with seed, scenario, completion,
  distance, planned steps, fault tick, injection flag, and fault-response result.
- summary.csv: all-trial and per-scenario totals, goal success rates, no-route
  counts, mean traveled distances, injection counts, and fault-response rates.
- trials.json: full maps, telemetry events, and per-trial results.

Success rate means goals reached divided by all attempts in that group, including
unreachable maps. A deliberate safe stop is not goal completion. Mean distance
includes zero-distance failures and interrupted runs. Fault-response rate uses
only actually injected faults; no-route attempts cannot exercise moving faults
and have blank response/latency fields. Normal trials also leave these blank.
A response passes when SAFE_STOP occurs at the trigger tick, with exactly
tick-minus-one moves and the expected preceding position. Zero tick stop latency
is an idealized discrete-model assumption, not measured physical performance.

## Recorded 100-trial run

Seed 20261030: 14/100 goals reached (14%); normal trials 14/25 (56%).
43 maps had no route. Mean traveled distance was 11.43 grid cells.
All 43 injected faults stopped before motion: 14 communication interruptions,
13 emergency stops, and 16 unauthorized commands. Fault response was 43/43
(100%) among exercised injections. The remaining fault attempts were unreachable.

These results verify programmed grid behavior only. They do not establish
physical navigation capability, real stopping latency, or real-world reliability.
