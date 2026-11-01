"""Build the self-contained operations dashboard from the canonical simulator."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation"))

from animate import map_collection  # noqa: E402

TEMPLATE = Path(__file__).with_name("template.html")
DEFAULT_OUTPUT = Path(__file__).with_name("index.html")
def simulation_payload(fault_tick=8, seed=20261030, maps=20):
    """Return deterministic original and seeded worlds from the Python model."""
    if type(fault_tick) is not int or fault_tick < 1:
        raise ValueError("fault_tick must be an integer >= 1")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(maps) is not int or not 1 <= maps <= 100:
        raise ValueError("maps must be an integer from 1 to 100")
    generated = map_collection(fault_tick=fault_tick, seed=seed, maps=maps)
    worlds = [{key: world[key] for key in
               ("label", "seed", "grid", "start", "fault_tick", "trials")}
              for world in generated["maps"]]
    return {
        "model": "simulation/sim.py · deterministic map bank · schema v1",
        "worlds": worlds,
        "seed_start": seed,
        "seeded_maps": maps,
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
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--maps", type=int, default=20,
                        help="number of seeded environments to embed, from 1 to 100")
    args = parser.parse_args()
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    if not 1 <= args.maps <= 100:
        parser.error("--maps must be between 1 and 100")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(simulation_payload(args.fault_tick, args.seed, args.maps)), encoding="utf-8")
    print(f"Built deterministic simulation dashboard: {args.output.resolve()}")


if __name__ == "__main__":
    main()
