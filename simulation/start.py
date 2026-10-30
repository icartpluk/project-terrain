"""Generate the offline demo and open it in the default browser."""
import argparse
from pathlib import Path
import webbrowser

from animate import map_collection, render_html


def start(output, open_browser=True):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(map_collection()), encoding="utf-8")
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
                        default=Path(__file__).resolve().parent.parent / "results" / "animation.html")
    parser.add_argument("--no-open", action="store_true", help="generate without opening a browser")
    args = parser.parse_args()
    try:
        start(args.output, not args.no_open)
    except OSError as error:
        parser.exit(1, f"Could not create the demo: {error}\n")


if __name__ == "__main__":
    main()
