"""Export the existing inert simulation as a self-contained HTML replay."""
import argparse
import json
from pathlib import Path

from sim import GRID, locate, simulate

SCENARIOS = ("normal", "link_loss", "estop", "unauthorized")


def replay_data(fault_tick=8, grid=GRID):
    return {"grid": list(grid), "start": list(locate("S", grid)),
            "fault_tick": fault_tick,
            "trials": [simulate(s, fault_tick, grid) for s in SCENARIOS]}


def render_html(data):
    template = Path(__file__).with_name("replay.html").read_text(encoding="utf-8")
    # Keep embedded data inert even if a future grid contains HTML characters.
    payload = json.dumps(data, sort_keys=True).replace("<", "\\u003c")
    return template.replace("__REPLAY_DATA__", payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/animation.html"))
    parser.add_argument("--fault-tick", type=int, default=8)
    args = parser.parse_args()
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(replay_data(args.fault_tick)), encoding="utf-8")
    print(f"Open {args.output.resolve()} in a web browser.")


if __name__ == "__main__":
    main()
