"""Project TERRAIN: inert, deterministic grid navigation and safety demo."""
import argparse, csv, heapq, json
from pathlib import Path

GRID = (
    "############",
    "#S...#.....#",
    "#.##.#.###.#",
    "#....#...#.#",
    "####.###.#.#",
    "#........#.#",
    "#.######.#.#",
    "#..........#",
    "#.########.#",
    "#.........G#",
    "############",
)

def locate(symbol, grid=GRID):
    return next((x,y) for y,row in enumerate(grid) for x,ch in enumerate(row) if ch == symbol)

def neighbors(p, grid=GRID):
    x,y=p
    for q in ((x+1,y),(x,y+1),(x-1,y),(x,y-1)):
        if 0 <= q[1] < len(grid) and 0 <= q[0] < len(grid[q[1]]) and grid[q[1]][q[0]] != "#":
            yield q

def plan(start, goal, grid=GRID):
    queue=[(0,start)]
    distance={start:0}
    previous={}
    while queue:
        d,node=heapq.heappop(queue)
        if d != distance[node]: continue
        if node == goal:
            path=[node]
            while node in previous:
                node=previous[node]
                path.append(node)
            return path[::-1]
        for other in neighbors(node, grid):
            if d+1 < distance.get(other,float("inf")):
                distance[other]=d+1
                previous[other]=node
                heapq.heappush(queue,(d+1,other))
    return []

def simulate(scenario="normal", fault_tick=8, grid=GRID):
    if fault_tick < 1:
        raise ValueError("fault_tick must be >= 1")
    if scenario not in ("normal","link_loss","estop","unauthorized"):
        raise ValueError("Unknown scenario")
    path=plan(locate("S",grid),locate("G",grid),grid)
    if not path:
        return {"scenario":scenario,"status":"NO_ROUTE","reached_goal":False,
                "moves":0,"planned_steps":0,"final_position":list(locate("S",grid)),
                "safe_stop":False,"events":[]}
    position=path[0]
    events=[]
    moves=0
    status="RUNNING"
    for tick in range(1,len(path)):
        if scenario != "normal" and tick == fault_tick:
            reason={"link_loss":"COMMUNICATION_LOSS","estop":"EMERGENCY_STOP","unauthorized":"UNAUTHORIZED_COMMAND"}[scenario]
            status="SAFE_STOP"
            events.append({"tick":tick,"event":reason,"position":list(position)})
            break
        position=path[tick]
        moves+=1
        events.append({"tick":tick,"event":"MOVE","position":list(position)})
    else:
        status="GOAL_REACHED"
    return {"scenario":scenario,"status":status,"reached_goal":position==locate("G",grid),
            "moves":moves,"planned_steps":len(path)-1,"final_position":list(position),
            "safe_stop":status=="SAFE_STOP","events":events}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="results")
    parser.add_argument("--fault-tick",type=int,default=8)
    args=parser.parse_args()
    if args.fault_tick < 1: parser.error("--fault-tick must be >= 1")
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    results=[simulate(s,args.fault_tick) for s in ("normal","link_loss","estop","unauthorized")]
    (out/"trials.json").write_text(json.dumps(results,indent=2)+"\n")
    with (out/"summary.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["scenario","status","reached_goal","moves","planned_steps","safe_stop"])
        writer.writeheader()
        for r in results: writer.writerow({k:r[k] for k in writer.fieldnames})
    for r in results:
        print(f"{r['scenario']:13} {r['status']:12} moves={r['moves']:2} goal={r['reached_goal']}")

if __name__=="__main__":
    main()

