"""Generate the offline operations dashboard and open it in the default browser."""
import argparse
from pathlib import Path
import sys
import webbrowser

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "presentation"))

from animate import map_collection, render_html as render_replay_html
from build import render_html as render_dashboard_html, simulation_payload


def start(output, open_browser=True, detailed_replay=False):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    html = render_replay_html(map_collection()) if detailed_replay else render_dashboard_html(simulation_payload())
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
    args = parser.parse_args()
    try:
        start(args.output, not args.no_open, args.detailed_replay)
    except OSError as error:
        parser.exit(1, f"Could not create the demo: {error}\n")


if __name__ == "__main__":
    main()
