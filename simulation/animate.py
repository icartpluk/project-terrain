"""Export the existing inert simulation as a self-contained HTML replay."""
import argparse
import json
from pathlib import Path

from sim import GRID, locate, simulate
from batch import generate_environment
from timing import simulate_timed

SCENARIOS = ("normal", "link_loss", "estop", "unauthorized")


def replay_data(fault_tick=8, grid=GRID, communication_delay=0, stopping_delay=0):
    # Validate even zero-like invalid inputs before deciding which model to use.
    for value in (communication_delay, stopping_delay):
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError("delays must be integers from 0 to 100")
    data = {"grid": list(grid), "start": list(locate("S", grid)),
            "fault_tick": fault_tick,
            "trials": [simulate(s, fault_tick, grid) for s in SCENARIOS]}
    if communication_delay or stopping_delay:
        data.update(communication_delay=communication_delay, stopping_delay=stopping_delay,
                    trials=[simulate_timed(s, fault_tick, grid, communication_delay, stopping_delay)
                            for s in SCENARIOS])
    return data


def map_collection(fault_tick=8, seed=20261030, maps=20, communication_delay=0, stopping_delay=0):
    """Precompute a bounded bank of Python maps and events for offline playback."""
    if not 1 <= maps <= 100:
        raise ValueError("maps must be between 1 and 100")
    worlds = [dict(replay_data(fault_tick, GRID, communication_delay, stopping_delay), label="Original demo", seed=None)]
    for offset in range(maps):
        world_seed = seed + offset
        worlds.append(dict(replay_data(fault_tick, generate_environment(world_seed), communication_delay, stopping_delay),
                           label=f"Seed {world_seed}", seed=world_seed))
    # Preserve the single-map data fields for existing replay-data consumers.
    return dict(worlds[0], maps=worlds)


def render_html(data):
    template = Path(__file__).with_name("replay.html").read_text(encoding="utf-8")
    # Keep embedded data inert even if a future grid contains HTML characters.
    payload = json.dumps(data, sort_keys=True).replace("<", "\\u003c")
    editor = Path(__file__).with_name("editor.js").read_text(encoding="utf-8")
    return template.replace("__EDITOR_CODE__", editor).replace("__REPLAY_DATA__", payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/animation.html"))
    parser.add_argument("--fault-tick", type=int, default=8)
    parser.add_argument("--communication-delay", type=int, default=0)
    parser.add_argument("--stopping-delay", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--maps", type=int, default=20,
                        help="number of seeded maps to embed, from 1 to 100")
    args = parser.parse_args()
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    if not 1 <= args.maps <= 100:
        parser.error("--maps must be between 1 and 100")
    if not all(0 <= n <= 100 for n in (args.communication_delay, args.stopping_delay)):
        parser.error("delays must be from 0 to 100 ticks")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(map_collection(args.fault_tick, args.seed, args.maps,
                                                    args.communication_delay, args.stopping_delay)), encoding="utf-8")
    print(f"Open {args.output.resolve()} in a web browser.")


if __name__ == "__main__":
    main()
