# Delay experiment model

This extends the inert grid demo with configurable response delays. It is not a
physics model, measured robot behavior, safety certification or stopping-distance
prediction in meters. A tick is an abstract time step. The playback speed changes
how quickly ticks are displayed, not the model results.

## Try it

1. Generate/open the demo normally.
2. Expand **Communication and stopping delays**.
3. Set communication delay to **2** and stopping delay to **1**, then **Apply delays**.
4. Select **Link loss** and press **Play**. At fault tick 8 the robot enters an
   amber communication phase, then an amber stopping phase, then a red stop.
5. Compare with **E-stop**: it bypasses communication delay, so only 1 stopping
   tick applies. Set both values to 0 to restore the original instant behavior.

Each value accepts whole ticks from 0 to 100. Applying settings starts a fresh
replay. They apply to all scenarios, map edits and live fault buttons. New map
preserves the chosen settings. Save map stores nonzero delay settings as optional
fields in the version 1 JSON format; old files load with both delays set to zero.
Reset replays the currently configured map and scenario.

## Exact assumptions

- Before a fault, the robot moves one cell per tick along the planned route.
- A scheduled fault at tick f happens before that tick's movement. It is injected
  only if f is a reachable motion tick; no route or arrival before f means no
  injection. A live fault starts before the next tick's move.
- Link loss and unauthorized-command scenarios use communication delay as a
  simplified detection/reaction interval. The robot continues its already
  authorized route during that interval. Unauthorized commands never supply a
  new movement target or route.
- E-stop is modeled as a local signal and bypasses communication delay.
- Stopping delay adds ticks of continued movement at the same speed. There is no
  gradual deceleration, inertia, slipping, collision dynamics, sensor noise or
  packet-level communication model.
- After all applicable delay ticks, a stop event latches the position. The model
  follows only open cells on the original route. If it reaches G during the
  delay, it waits there until the stop event; reaching G does not erase an injected
  fault or create movement beyond the route.

For an injected fault:

    delay = communication delay + stopping delay
    E-stop delay = stopping delay
    stop tick = fault tick + applicable delay
    extra cells = min(applicable delay, route cells remaining when fault occurs)

The screen compares predicted total latency and extra cells with an instant stop
(0 ticks, 0 extra cells). The comparison is a model result, including while the
replay is still running. Red SAFE STOP means the model has reached its stationary
end state, not that delayed travel was safe in a real environment.

## Reproduce without the browser

From the repository root:

```sh
python simulation/timing.py --fault-tick 8 --communication-delay 2 --stopping-delay 1
python simulation/animate.py --communication-delay 2 --stopping-delay 1 --output results/delayed.html
python -m unittest discover -s simulation -v
python simulation/animate.py
node simulation/test_replay.cjs
```

The first command prints JSON for all four scenarios, including event phases and
timing metrics. No injected fault is represented by null fault/stop/latency fields
and zero extra cells, not a successful safety response.

The original sim.py and 100-trial batch remain instant-stop baselines. timing.py
uses their route and fault eligibility and adds the delayed response. Browser
edits use the equivalent model. Tests compare complete Python/browser results for
multiple delay combinations, first/intermediate/late faults, connected and
disconnected maps, arrival during delay, plus scheduled and live playback.
