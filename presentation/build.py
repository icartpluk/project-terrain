"""Build the self-contained operations dashboard from the canonical simulator."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation"))

from sim import GRID, locate, simulate  # noqa: E402

TEMPLATE = Path(__file__).with_name("template.html")
DEFAULT_OUTPUT = Path(__file__).with_name("index.html")
SCENARIOS = ("normal", "link_loss", "estop", "unauthorized")


def simulation_payload(fault_tick=8):
    """Return only deterministic data produced by simulation/sim.py."""
    if type(fault_tick) is not int or fault_tick < 1:
        raise ValueError("fault_tick must be an integer >= 1")
    return {
        "model": "simulation/sim.py · fixed grid · schema v1",
        "grid": list(GRID),
        "start": list(locate("S", GRID)),
        "fault_tick": fault_tick,
        "trials": [simulate(scenario, fault_tick, GRID) for scenario in SCENARIOS],
    }


def render_html(payload):
    """Embed escaped, canonical simulation output in the presentation template."""
    html = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    if html.count("__SIMULATION_DATA__") != 1:
        raise ValueError("dashboard template must contain exactly one simulation-data marker")
    return html.replace("__SIMULATION_DATA__", data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fault-tick", type=int, default=8)
    args = parser.parse_args()
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(simulation_payload(args.fault_tick)), encoding="utf-8")
    print(f"Built deterministic simulation dashboard: {args.output.resolve()}")


if __name__ == "__main__":
    main()
