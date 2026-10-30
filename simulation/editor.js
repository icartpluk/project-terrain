// Match sim.py's Dijkstra ordering: distance, x, then y.
// Offline edits use this browser model; exported maps retain Python events.
function editedReplay(grid, faultTick) {
  const locate = symbol => {
    for (let y=0;y<grid.length;y++) for (let x=0;x<grid[y].length;x++)
      if (grid[y][x] === symbol) return [x,y];
  };
  const start=locate("S"), goal=locate("G"), key=p=>p.join(",");
  const queue=[[0,...start]], distance=new Map([[key(start),0]]), previous=new Map();
  let path=[];
  while(queue.length) {
    queue.sort((a,b)=>a[0]-b[0] || a[1]-b[1] || a[2]-b[2]);
    const [d,x,y]=queue.shift(), node=[x,y];
    if (d !== distance.get(key(node))) continue;
    if (key(node) === key(goal)) {
      path=[node];
      while(previous.has(key(path[0]))) path.unshift(previous.get(key(path[0])));
      break;
    }
    for (const other of [[x+1,y],[x,y+1],[x-1,y],[x,y-1]]) {
      const [nx,ny]=other;
      if (ny<0 || ny>=grid.length || nx<0 || nx>=grid[ny].length || grid[ny][nx]==="#") continue;
      if (d+1 < (distance.get(key(other)) ?? Infinity)) {
        distance.set(key(other),d+1); previous.set(key(other),node);
        queue.push([d+1,nx,ny]);
      }
    }
  }
  const trials=["normal","link_loss","estop","unauthorized"].map(scenario=>{
    let position=start, moves=0, status=path.length?"GOAL_REACHED":"NO_ROUTE";
    const events=[];
    for(let tick=1;tick<path.length;tick++) {
      if(scenario!=="normal" && tick===faultTick) {
        status="SAFE_STOP";
        events.push({tick,event:{link_loss:"COMMUNICATION_LOSS",estop:"EMERGENCY_STOP",unauthorized:"UNAUTHORIZED_COMMAND"}[scenario],position});
        break;
      }
      position=path[tick]; moves++;
      events.push({tick,event:"MOVE",position});
    }
    return {scenario,status,reached_goal:key(position)===key(goal),moves,
      planned_steps:Math.max(0,path.length-1),final_position:position,safe_stop:status==="SAFE_STOP",events};
  });
  return {grid,start,fault_tick:faultTick,trials,edited:true,seed:null};
}
function editCell(x,y) {
  const cell=data.grid[y][x], rows=data.grid.map(row=>[...row]);
  if(x===0 || y===0 || y===rows.length-1 || x===rows[y].length-1 || cell==="S") return;
  if(el("edit-tool").value==="goal") {
    for(const row of rows) for(let i=0;i<row.length;i++) if(row[i]==="G") row[i]=".";
    rows[y][x]="G";
  } else {
    if(cell==="G") {
      el("edit-message").textContent="Move the destination before placing an obstacle there.";
      return;
    }
    rows[y][x]=cell==="#"?".":"#";
  }
  pause();
  data=editedReplay(rows.map(row=>row.join("")),data.fault_tick);
  trial=data.trials[Number(el("scenario").value)]; index=0;
  el("edit-message").textContent="Map updated. Choose a scenario and press Play. Edits are not saved.";
  draw(); drawEditor();
  el("editor").children[y*rows[0].length+x]?.focus();
}
function drawEditor() {
  const editor=el("editor");
  editor.replaceChildren();
  editor.style.gridTemplateColumns=`repeat(${data.grid[0].length}, 1fr)`;
  data.grid.forEach((row,y)=>[...row].forEach((cell,x)=>{
    const button=document.createElement("button");
    button.type="button"; button.textContent=cell==="."?"·":cell;
    button.className=cell==="#"?"wall":"";
    button.disabled=x===0 || y===0 || y===data.grid.length-1 || x===row.length-1 || cell==="S";
    button.setAttribute("aria-label",`Cell ${x}, ${y}: ${{".":"open","#":"obstacle",S:"start",G:"destination",O:"foam marker"}[cell]}`);
    button.onclick=()=>editCell(x,y);
    editor.appendChild(button);
  }));
}
el("restore-map").onclick=()=>changeWorld(worldIndex);
