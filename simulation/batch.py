"""Seeded fictional tunnel trials; standard-library-only, idealized grid model."""
import argparse
import csv
import json
import random
from pathlib import Path

from sim import locate, plan, simulate

SCENARIOS = ("normal", "link_loss", "estop", "unauthorized")


def generate_environment(seed, width=21, height=17, obstacle_density=0.28):
    """Random training rooms/passages. Foam blocks (#) may disconnect a route.

    O is an inert foam marker: traversable, with no manipulation modeled.
    No route is carved after generation, so unreachable goals remain failures.
    """
    if width < 5 or height < 5:
        raise ValueError("width and height must be >= 5")
    if not 0 <= obstacle_density <= 1:
        raise ValueError("obstacle_density must be between 0 and 1")
    rng = random.Random(seed)
    rows = [["#"] * width for _ in range(height)]
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            rows[y][x] = "#" if rng.random() < obstacle_density else "."
    free = [(x, y) for y in range(1, height - 1)
            for x in range(1, width - 1) if rows[y][x] == "."]
    for x, y in rng.sample(free, min(5, len(free))):
        rows[y][x] = "O"
    rows[1][1] = "S"
    rows[-2][-2] = "G"
    return tuple("".join(row) for row in rows)


def run_trials(count=100, seed=20261030):
    if count < 1:
        raise ValueError("count must be >= 1")
    results = []
    for index in range(count):
        environment_seed = seed + index
        grid = generate_environment(environment_seed)
        scenario = SCENARIOS[index % len(SCENARIOS)]
        path = plan(locate("S", grid), locate("G", grid), grid)
        # Inject only at a reachable motion tick, including before the first
        # and final moves. Unreachable routes cannot exercise moving faults.
        fault_tick = (random.Random(environment_seed ^ 0xBAD5EED)
                      .randint(1, len(path) - 1)) if path else 1
        result = simulate(scenario, fault_tick, grid)
        injected = any(e["event"] != "MOVE" for e in result["events"])
        response = None
        if injected:
            event = result["events"][-1]
            expected_position = list(path[fault_tick - 1])
            response = (result["safe_stop"]
                        and result["moves"] == fault_tick - 1
                        and result["final_position"] == expected_position
                        and event["tick"] == fault_tick)
        result.update(
            trial=index + 1, environment_seed=environment_seed,
            environment=list(grid), fault_tick=fault_tick if scenario != "normal" else None,
            fault_injected=injected, fault_response_pass=response,
            navigation_distance=result["moves"], distance_unit="grid_cell",
            stop_latency_ticks=0 if injected else None,
        )
        results.append(result)
    return results


def summarize(results):
    summaries = []
    for scenario in ("all",) + SCENARIOS:
        group = [r for r in results if scenario == "all" or r["scenario"] == scenario]
        if not group:
            continue
        injected = [r for r in group if r["fault_injected"]]
        summaries.append(dict(
            scenario=scenario, trials=len(group),
            goals_reached=sum(r["reached_goal"] for r in group),
            success_rate=sum(r["reached_goal"] for r in group) / len(group),
            no_route=sum(r["status"] == "NO_ROUTE" for r in group),
            mean_navigation_distance=sum(r["navigation_distance"] for r in group) / len(group),
            fault_injections=len(injected),
            fault_response_passes=sum(r["fault_response_pass"] for r in injected),
            fault_response_rate=(sum(r["fault_response_pass"] for r in injected) / len(injected)
                                 if injected else None),
        ))
    return summaries


def write_reports(results, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    fields = ("trial", "environment_seed", "scenario", "status", "reached_goal",
              "navigation_distance", "distance_unit", "planned_steps", "fault_tick",
              "fault_injected", "safe_stop", "stop_latency_ticks", "fault_response_pass")
    with (output / "trials.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    summary = summarize(results)
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (output / "trials.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261030)
    parser.add_argument("--output", default="results")
    args = parser.parse_args()
    if args.trials < 1:
        parser.error("--trials must be >= 1")
    results = run_trials(args.trials, args.seed)
    write_reports(results, args.output)
    print(json.dumps(summarize(results), indent=2))


if __name__ == "__main__":
    main()
