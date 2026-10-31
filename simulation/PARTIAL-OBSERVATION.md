# Partial observations and changing obstacles

This prototype adds limited-range sensing to the existing fictional grid model. The robot begins with only the cells within a configured Manhattan radius observed. Unseen cells are shown as `?` and treated as blocked for route planning. The robot moves to a reachable frontier, observes again, and replans. It never enters a cell before the simulated sensor has observed it as traversable.

Obstacle changes are deterministic scenario events: an interior floor cell becomes blocked or returns to its original floor/marker state at a specified tick. The change is applied before that tick's observation and movement. If the next route is blocked, the planner uses the latest known map to select another route. The model rejects a scenario that would block the cell the simulated robot currently occupies.

## Reproduce

```sh
python -m unittest discover -s simulation -v
```

The tests cover unknown cells, repeatability, rerouting around a newly observed obstacle, unreachable known routes, and invalid sensor/event configurations.

## Limits

This is a deterministic software model. It does not represent camera images, sensor physics, localization error, physical obstacle motion, collision dynamics, robot hardware, or real time. The event schedule is provided by the test scenario; it is not inferred from the environment. Results show only the behavior implemented here.
