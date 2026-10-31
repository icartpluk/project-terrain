"""Partial-observation exploration in fictional, inert grid environments."""
from sim import GRID, locate, plan

ALLOWED = set("#.OSG")


def _validate_grid(grid):
    if (not isinstance(grid, (tuple, list)) or len(grid) < 3
            or any(not isinstance(row, str) for row in grid)):
        raise ValueError("grid must be a rectangular map of at least 3 by 3")
    width = len(grid[0])
    if width < 3 or width > 41 or len(grid) > 41:
        raise ValueError("grid dimensions must be between 3 and 41")
    if any(len(row) != width or set(row) - ALLOWED for row in grid):
        raise ValueError("grid must be rectangular and use only # . O S G")
    if (grid[0] != "#" * width or grid[-1] != "#" * width
            or any(row[0] != "#" or row[-1] != "#" for row in grid)):
        raise ValueError("grid boundary must contain only obstacles")
    cells = "".join(grid)
    if cells.count("S") != 1 or cells.count("G") != 1:
        raise ValueError("grid needs exactly one start S and one destination G")


def _validate_changes(grid, changes, max_ticks):
    if not isinstance(changes, (tuple, list)):
        raise ValueError("obstacle_changes must be a list or tuple")
    seen = set()
    normalized = []
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError("each obstacle change must be a mapping")
        tick = change.get("tick")
        position = change.get("position")
        blocked = change.get("blocked")
        if type(tick) is not int or not 1 <= tick <= max_ticks:
            raise ValueError("change tick must be within the simulation")
        if (not isinstance(position, (tuple, list)) or len(position) != 2
                or any(type(value) is not int for value in position)):
            raise ValueError("change position must be an [x, y] integer pair")
        x, y = position
        if not (0 < x < len(grid[0]) - 1 and 0 < y < len(grid) - 1):
            raise ValueError("obstacles may change only in interior cells")
        if grid[y][x] not in (".", "O"):
            raise ValueError("obstacles may change only on traversable cells")
        if type(blocked) is not bool:
            raise ValueError("blocked must be true or false")
        key = (tick, x, y)
        if key in seen:
            raise ValueError("duplicate obstacle change for one tick and cell")
        seen.add(key)
        normalized.append((tick, x, y, blocked))
    return sorted(normalized)


def _observe(truth, observation, position, radius):
    px, py = position
    for y, row in enumerate(truth):
        for x, cell in enumerate(row):
            if abs(x - px) + abs(y - py) <= radius:
                observation[y][x] = cell


def _known_grid(observation):
    # Unknown cells are treated as blocked for route planning.
    return tuple("".join(cell if cell is not None else "#" for cell in row)
                 for row in observation)


def _frontier_path(position, observation, known_grid):
    """Choose the nearest reachable known cell beside at least one unknown cell."""
    candidates = []
    height, width = len(observation), len(observation[0])
    for y, row in enumerate(observation):
        for x, cell in enumerate(row):
            if cell not in (".", "O", "S", "G") or (x, y) == position:
                continue
            has_unknown_neighbor = any(
                0 <= ny < height and 0 <= nx < width
                and observation[ny][nx] is None
                for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1))
            )
            if not has_unknown_neighbor:
                continue
            path = plan(position, (x, y), known_grid)
            if len(path) > 1:
                candidates.append((len(path), x, y, path))
    return min(candidates)[3] if candidates else []


def simulate_partial_observation(grid=GRID, sensor_radius=1,
                                 obstacle_changes=(), max_ticks=None):
    """Explore with a limited Manhattan sensor range and deterministic changes.

    Unknown cells remain unknown and are treated as blocked until observed.
    Scheduled obstacle changes happen before that tick's observation and move.
    Changes apply only to interior floor/marker cells and cannot block the
    robot's current cell. All units are abstract cells and ticks.
    """
    _validate_grid(grid)
    if type(sensor_radius) is not int or not 1 <= sensor_radius <= 10:
        raise ValueError("sensor_radius must be an integer from 1 to 10")
    if max_ticks is None:
        max_ticks = len(grid) * len(grid[0]) * 4
    if type(max_ticks) is not int or max_ticks < 1:
        raise ValueError("max_ticks must be a positive integer")
    changes = _validate_changes(grid, obstacle_changes, max_ticks)

    truth = [list(row) for row in grid]
    original = [list(row) for row in grid]
    observation = [[None for _ in row] for row in grid]
    position = locate("S", grid)
    goal = locate("G", grid)
    _observe(truth, observation, position, sensor_radius)
    initial_observation = ["".join(cell or "?" for cell in row)
                           for row in observation]

    by_tick = {}
    for tick, x, y, blocked in changes:
        by_tick.setdefault(tick, []).append((x, y, blocked))

    events = []
    environment_events = []
    moves = 0
    status = "TICK_LIMIT"
    ticks = 0

    for tick in range(1, max_ticks + 1):
        ticks = tick
        for x, y, blocked in by_tick.get(tick, ()):
            if blocked and position == (x, y):
                raise ValueError("an obstacle change cannot block the current cell")
            truth[y][x] = "#" if blocked else original[y][x]
            environment_events.append({
                "tick": tick,
                "event": "OBSTACLE_APPEARED" if blocked else "OBSTACLE_REMOVED",
                "position": [x, y],
            })

        visible_before = sum(cell is not None for row in observation for cell in row)
        _observe(truth, observation, position, sensor_radius)
        visible_after = sum(cell is not None for row in observation for cell in row)

        if position == goal:
            status = "GOAL_REACHED"
            ticks = tick - 1
            break

        known_grid = _known_grid(observation)
        path = []
        if observation[goal[1]][goal[0]] == "G":
            path = plan(position, goal, known_grid)
        if len(path) < 2:
            path = _frontier_path(position, observation, known_grid)
        if len(path) < 2:
            status = "NO_KNOWN_ROUTE"
            events.append({
                "tick": tick, "event": "NO_KNOWN_ROUTE",
                "position": list(position),
                "newly_observed_cells": visible_after - visible_before,
            })
            break

        next_position = path[1]
        # A one-cell sensor range ensures the next cell is known before entry.
        if observation[next_position[1]][next_position[0]] in (None, "#"):
            raise AssertionError("planner selected a blocked or unobserved cell")
        if truth[next_position[1]][next_position[0]] == "#":
            raise AssertionError("sensor update missed a changed obstacle")

        position = next_position
        moves += 1
        events.append({
            "tick": tick, "event": "MOVE", "position": list(position),
            "newly_observed_cells": visible_after - visible_before,
        })
        if position == goal:
            status = "GOAL_REACHED"
            break

    return {
        "status": status,
        "position": list(position),
        "goal": list(goal),
        "moves": moves,
        "ticks": ticks,
        "sensor_radius_cells": sensor_radius,
        "initial_observation": initial_observation,
        "known_map": ["".join(cell or "?" for cell in row) for row in observation],
        "environment_map": ["".join(row) for row in truth],
        "obstacle_changes": [
            {"tick": tick, "position": [x, y], "blocked": blocked}
            for tick, x, y, blocked in changes
        ],
        "environment_events": environment_events,
        "events": events,
    }
