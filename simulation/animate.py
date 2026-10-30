"""Export the existing inert simulation as a self-contained HTML replay."""
import argparse
import json
from pathlib import Path

from sim import GRID, locate, simulate
from batch import generate_environment

SCENARIOS = ("normal", "link_loss", "estop", "unauthorized")


def replay_data(fault_tick=8, grid=GRID):
    return {"grid": list(grid), "start": list(locate("S", grid)),
            "fault_tick": fault_tick,
            "trials": [simulate(s, fault_tick, grid) for s in SCENARIOS]}


def map_collection(fault_tick=8, seed=20261030, maps=20):
    """Precompute a bounded bank of Python maps and events for offline playback."""
    if not 1 <= maps <= 100:
        raise ValueError("maps must be between 1 and 100")
    worlds = [dict(replay_data(fault_tick), label="Original demo", seed=None)]
    for offset in range(maps):
        world_seed = seed + offset
        worlds.append(dict(replay_data(fault_tick, generate_environment(world_seed)),
                           label=f"Seed {world_seed}", seed=world_seed))
    # Preserve the single-map data fields for existing replay-data consumers.
    return dict(worlds[0], maps=worlds)


def render_html(data):
    template = Path(__file__).with_name("replay.html").read_text(encoding="utf-8")
    # Keep embedded data inert even if a future grid contains HTML characters.
    payload = json.dumps(data, sort_keys=True).replace("<", "\\u003c")
    return template.replace("__REPLAY_DATA__", payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/animation.html"))
    parser.add_argument("--fault-tick", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--maps", type=int, default=20,
                        help="number of seeded maps to embed, from 1 to 100")
    args = parser.parse_args()
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    if not 1 <= args.maps <= 100:
        parser.error("--maps must be between 1 and 100")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(map_collection(args.fault_tick, args.seed, args.maps)), encoding="utf-8")
    print(f"Open {args.output.resolve()} in a web browser.")


if __name__ == "__main__":
    main()
