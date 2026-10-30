"""Idealized delayed fault responses in ticks and cells, not physical dynamics."""
import argparse
import json

from sim import GRID, locate, simulate

REASONS = {"link_loss": "COMMUNICATION_LOSS", "estop": "EMERGENCY_STOP",
           "unauthorized": "UNAUTHORIZED_COMMAND"}


def simulate_timed(scenario="normal", fault_tick=8, grid=GRID,
                   communication_delay=0, stopping_delay=0):
    for name, value in (("communication_delay", communication_delay),
                        ("stopping_delay", stopping_delay)):
        if type(value) is not int or not 0 <= value <= 100:
            raise ValueError(f"{name} must be an integer from 0 to 100")
    baseline = simulate(scenario, fault_tick, grid)
    normal = simulate("normal", fault_tick, grid)
    result = dict(baseline)
    timing = dict(communication_delay_ticks=communication_delay,
                  stopping_delay_ticks=stopping_delay, fault_tick=None,
                  stop_tick=None, latency_ticks=None, moves_after_fault=0)
    result["timing"] = timing
    # Faults are only injected at a reachable motion tick.
    if scenario == "normal" or not baseline["safe_stop"]:
        return result
    detection = 0 if scenario == "estop" else communication_delay
    latency = detection + stopping_delay
    path = [list(locate("S", grid))] + [e["position"] for e in normal["events"]]
    events = [dict(e) for e in normal["events"][:fault_tick-1]]
    position = path[fault_tick-1]
    moves = fault_tick-1
    extra_moves = 0
    for elapsed in range(latency):
        phase = "COMMUNICATION_DELAY" if elapsed < detection else "STOPPING_DELAY"
        moving = moves < len(path)-1
        if moving:
            moves += 1
            extra_moves += 1
            position = path[moves]
        events.append(dict(tick=fault_tick+elapsed, event="MOVE" if moving else "WAIT",
                           position=position, phase=phase, fault_reason=REASONS[scenario]))
    stop_tick = fault_tick+latency
    events.append(dict(tick=stop_tick, event=REASONS[scenario], position=position))
    timing.update(fault_tick=fault_tick, stop_tick=stop_tick,
                  latency_ticks=latency, moves_after_fault=extra_moves)
    result.update(status="SAFE_STOP", safe_stop=True, reached_goal=position==path[-1],
                  moves=moves, final_position=position, events=events)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault-tick", type=int, default=8)
    parser.add_argument("--communication-delay", type=int, default=2)
    parser.add_argument("--stopping-delay", type=int, default=2)
    args = parser.parse_args()
    try:
        results = [simulate_timed(s, args.fault_tick, communication_delay=args.communication_delay,
                                 stopping_delay=args.stopping_delay)
                   for s in ("normal", "link_loss", "estop", "unauthorized")]
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
