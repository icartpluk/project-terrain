"""Generate the offline operations dashboard and open it in the default browser."""
import argparse
from pathlib import Path
import sys
import webbrowser

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "presentation"))

from animate import map_collection, render_html as render_replay_html
from build import render_html as render_dashboard_html, simulation_payload


def start(output, open_browser=True, detailed_replay=False, seed=20261030, maps=20,
          fault_tick=8):
    """Export reproducible seeded worlds without changing the canonical model."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(maps) is not int or not 1 <= maps <= 100:
        raise ValueError("maps must be an integer from 1 to 100")
    if type(fault_tick) is not int or fault_tick < 1:
        raise ValueError("fault_tick must be an integer >= 1")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if detailed_replay:
        html = render_replay_html(map_collection(
            fault_tick=fault_tick, seed=seed, maps=maps))
    else:
        html = render_dashboard_html(simulation_payload(
            fault_tick=fault_tick, seed=seed, maps=maps))
    output.write_text(html, encoding="utf-8")
    print(f"Your demo is ready: {output}")
    if open_browser:
        try:
            opened = webbrowser.open(output.as_uri())
        except (webbrowser.Error, OSError):
            opened = False
        if not opened:
            print("Open this HTML file manually in your browser.")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).resolve().parent.parent / "results" / "operations-dashboard.html")
    parser.add_argument("--no-open", action="store_true", help="generate without opening a browser")
    parser.add_argument("--detailed-replay", action="store_true",
                        help="open the full-featured grid replay instead of the operations dashboard")
    parser.add_argument("--seed", type=int, default=20261030,
                        help="first deterministic environment seed (default: 20261030)")
    parser.add_argument("--maps", type=int, default=20,
                        help="number of consecutive seeded maps, 1 to 100 (default: 20)")
    parser.add_argument("--fault-tick", type=int, default=8,
                        help="scheduled fault tick, >= 1 (default: 8)")
    args = parser.parse_args()
    if not 1 <= args.maps <= 100:
        parser.error("--maps must be between 1 and 100")
    if args.fault_tick < 1:
        parser.error("--fault-tick must be >= 1")
    try:
        start(args.output, not args.no_open, args.detailed_replay,
              args.seed, args.maps, args.fault_tick)
    except OSError as error:
        parser.exit(1, f"Could not create the demo: {error}\n")


if __name__ == "__main__":
    main()
