"""Compare fault-response delays on identical seeded grids; no extra packages."""
import argparse
import csv
from html import escape
import json
from pathlib import Path

from batch import generate_environment
from timing import REASONS, simulate_timed
from sim import locate, plan

DEFAULT_DELAYS = ((0, 0), (2, 1), (4, 2))
PLACEMENTS = ("fixed", "first", "middle", "last")


def compare(count=100, seed=20261030, fault_tick=8, delays=DEFAULT_DELAYS, placements=("fixed",)):
    if type(count) is not int or not 1 <= count <= 1000:
        raise ValueError("maps must be an integer from 1 to 1000")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(fault_tick) is not int or not 1 <= fault_tick <= 1000000:
        raise ValueError("fault tick must be an integer from 1 to 1000000")
    pairs = list(delays)
    if not 1 <= len(pairs) <= 20:
        raise ValueError("provide 1 to 20 delay pairs")
    for pair in pairs:
        if len(pair) != 2 or any(type(n) is not int or not 0 <= n <= 100 for n in pair):
            raise ValueError("each delay pair needs two whole ticks from 0 to 100")
    pairs = sorted({(0, 0), *(tuple(pair) for pair in pairs)})
    if not placements or any(p not in PLACEMENTS for p in placements):
        raise ValueError("placements must contain fixed, first, middle or last")
    placements = [p for p in PLACEMENTS if p in placements]
    worlds, trials = [], []
    for offset in range(count):
        environment_seed = seed+offset
        grid = generate_environment(environment_seed)
        path = plan(locate("S", grid), locate("G", grid), grid)
        steps = max(0, len(path)-1)
        worlds.append(dict(seed=environment_seed, grid=list(grid), planned_steps=steps))
        for placement in placements:
            tick = {"fixed": fault_tick, "first": 1,
                    "middle": max(1, (steps+1)//2), "last": max(1, steps)}[placement]
            for scenario in REASONS:
                baseline = simulate_timed(scenario, tick, grid)
                for communication, stopping in pairs:
                    result = (baseline if (communication, stopping) == (0, 0) else
                              simulate_timed(scenario, tick, grid, communication, stopping))
                    timing = result["timing"]
                    injected = timing["fault_tick"] is not None
                    trials.append(dict(environment_seed=environment_seed, placement=placement, scenario=scenario,
                        communication_delay=communication, stopping_delay=stopping,
                        status=result["status"], fault_injected=injected,
                        exclusion=("no_route" if result["status"] == "NO_ROUTE" else
                                   "fault_after_arrival" if not injected else None),
                        scheduled_fault_tick=tick, fault_tick=timing["fault_tick"], stop_tick=timing["stop_tick"],
                        remaining_cells=steps-tick+1 if injected else None,
                        latency_ticks=timing["latency_ticks"],
                        extra_cells=timing["moves_after_fault"] if injected else None,
                        fault_position=baseline["final_position"] if injected else None,
                        stop_position=result["final_position"],
                        goal_at_stop=result["reached_goal"] if injected else None))
    summary = []
    for placement in placements:
        for scenario in REASONS:
            for communication, stopping in pairs:
                group = [r for r in trials if (r["placement"], r["scenario"], r["communication_delay"], r["stopping_delay"])
                         == (placement, scenario, communication, stopping)]
                injected = [r for r in group if r["fault_injected"]]
                summary.append(dict(placement=placement, scenario=scenario, communication_delay=communication,
                    stopping_delay=stopping, maps=len(group), injected=len(injected),
                    no_route=sum(r["exclusion"] == "no_route" for r in group),
                    fault_after_arrival=sum(r["exclusion"] == "fault_after_arrival" for r in group),
                    mean_latency_ticks=(sum(r["latency_ticks"] for r in injected)/len(injected) if injected else None),
                    mean_extra_cells=(sum(r["extra_cells"] for r in injected)/len(injected) if injected else None),
                    max_extra_cells=max((r["extra_cells"] for r in injected), default=None),
                    goal_at_stop=sum(r["goal_at_stop"] for r in injected)))
    return dict(config=dict(maps=count, seed=seed, fault_tick=fault_tick, placements=placements, delays=[list(p) for p in pairs]),
                worlds=worlds, trials=trials, summary=summary)


def write_reports(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name in ("trials", "summary"):
        with (output/f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(report[name][0]))
            writer.writeheader()
            for row in report[name]:
                writer.writerow({key: json.dumps(value) if isinstance(value, list) else value
                                 for key, value in row.items()})
    (output/"comparison.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    columns = (
        ("placement", "Fault placement"), ("scenario", "Scenario"), ("communication_delay", "Comm. ticks"),
        ("stopping_delay", "Stopping ticks"), ("maps", "Maps"),
        ("injected", "Faults injected"), ("no_route", "No route"),
        ("fault_after_arrival", "Fault after arrival"), ("mean_latency_ticks", "Mean latency (ticks)"),
        ("mean_extra_cells", "Mean extra cells"), ("max_extra_cells", "Max extra cells"),
        ("goal_at_stop", "At goal when stopped"))
    headings = "".join(f'<th scope="col">{label}</th>' for _, label in columns)
    rows = []
    for row in report["summary"]:
        values = []
        for key, _ in columns:
            value = row[key]
            display = "—" if value is None else f"{value:.2f}" if isinstance(value, float) else str(value)
            values.append("<td>"+escape(display)+"</td>")
        rows.append("<tr>"+"".join(values)+"</tr>")
    config = report["config"]
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TERRAIN response-delay comparison</title>
<style>
body {{font:16px system-ui,sans-serif;margin:24px;background:#111b24;color:#ecf3f8;line-height:1.5}}
main {{max-width:1200px;margin:auto}} .scroll {{overflow-x:auto}} table {{border-collapse:collapse;width:100%}}
th,td {{padding:10px;border:1px solid #536371;text-align:left}} th {{background:#203c4a}}
tr:nth-child(even) {{background:#202f3b}} a {{color:#75d6ff}} :focus-visible {{outline:3px solid #ffd66e}}
</style><main><h1>Response-delay comparison</h1>
<p>{config["maps"]} identical seeded maps per setting · first seed {config["seed"]} · fault tick {config["fault_tick"]}.</p>
<p>Placements: {escape(", ".join(config["placements"]))}. The fixed placement uses the fault tick above.
First, middle and last use each route's first, middle and final motion ticks.
Smaller extra travel near G reflects the route ending, not a faster stop response.</p>
<p>The 0 + 0 rows are the instant-stop baseline. Means and maxima include only injected faults.
No-route and after-arrival cases are excluded and counted separately. A dash means no faults were injected.</p>
<p>E-stop bypasses communication delay. Extra travel is capped by the route endpoint; the robot waits
at G if it arrives before its stop event. At goal when stopped is not a safety success rate.</p>
<div class="scroll" tabindex="0" role="region" aria-label="Scrollable comparison table">
<table><caption>Idealized ticks and grid cells; not physical stopping performance</caption>
<thead><tr>{headings}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p><a href="summary.csv">Summary CSV</a> · <a href="trials.csv">Individual trials CSV</a> ·
<a href="comparison.json">Configuration, maps and results (JSON)</a></p>
<p>This deterministic report compares model assumptions, not real robot safety. Playback speed does not affect these results.
Keep the report files together if you move this folder.</p></main></html>"""
    (output/"report.html").write_text(page, encoding="utf-8")


def parse_delays(text):
    try:
        return [tuple(int(n) for n in pair.split(":")) for pair in text.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("use pairs such as 0:0,2:1,4:2")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--fault-tick", type=int, default=8)
    parser.add_argument("--placements", default="fixed",
                        help="comma-separated fixed,first,middle,last (default: fixed)")
    parser.add_argument("--delays", type=parse_delays, default=DEFAULT_DELAYS,
                        help="communication:stopping pairs, e.g. 0:0,2:1,4:2")
    parser.add_argument("--output", type=Path, default=Path("results/delay-comparison"))
    args = parser.parse_args()
    try:
        report = compare(args.maps, args.seed, args.fault_tick, args.delays, args.placements.split(","))
    except ValueError as error:
        parser.error(str(error))
    write_reports(report, args.output)
    print(f'Open {(args.output/"report.html").resolve()}')
    print(f'{len(report["trials"])} comparisons; {len(report["summary"])} summary rows.')


if __name__ == "__main__":
    main()
