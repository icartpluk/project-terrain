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
  loadRevision++;
  data=editedReplay(rows.map(row=>row.join("")),data.fault_tick);
  liveStop=null;
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

// Map files contain geometry and fault timing only. Recompute all events locally.
function parseMapFile(text) {
  if (text.length > 32768) throw new Error("Map file must be at most 32 KB.");
  let file;
  try { file=JSON.parse(text); } catch { throw new Error("Choose a valid JSON map file."); }
  if (!file || file.version!==1 || !Array.isArray(file.grid))
    throw new Error("Expected a TERRAIN version 1 map file.");
  const grid=file.grid, width=typeof grid[0]==="string"?grid[0].length:0;
  if (grid.length<3 || grid.length>41 || width<3 || width>41 ||
      grid.some(row=>typeof row!=="string" || row.length!==width || /[^#.OSG]/.test(row)))
    throw new Error("Map must be rectangular, 3–41 cells per side, using # . O S G.");
  if (grid[0]!=="#".repeat(width) || grid.at(-1)!=="#".repeat(width) ||
      grid.some(row=>row[0]!=="#" || row.at(-1)!=="#"))
    throw new Error("The map boundary must contain only obstacles (#).");
  const cells=grid.join("");
  if ([...cells].filter(c=>c==="S").length!==1 || [...cells].filter(c=>c==="G").length!==1)
    throw new Error("Map needs exactly one start S and one destination G.");
  if (!Number.isSafeInteger(file.fault_tick) || file.fault_tick<1 || file.fault_tick>1000000)
    throw new Error("Fault tick must be an integer from 1 to 1000000.");
  return editedReplay(grid.slice(),file.fault_tick);
}
function mapFileText() {
  return JSON.stringify({version:1,grid:data.grid,fault_tick:data.fault_tick},null,2)+"\n";
}
el("save-map").onclick=()=>{
  const url=URL.createObjectURL(new Blob([mapFileText()],{type:"application/json"}));
  const link=document.createElement("a");
  link.href=url; link.download="terrain-map.json";
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
  el("edit-message").textContent="Map download requested. Keep terrain-map.json to load this layout later.";
};
el("load-map").onchange=async()=>{
  const input=el("load-map"), file=input.files?.[0];
  if(!file) return;
  input.value="";
  const revision=++loadRevision;
  pause();
  try {
    if(file.size>32768) throw new Error("Map file must be at most 32 KB.");
    const text=await file.text();
    if(revision!==loadRevision) return;
    const loaded=parseMapFile(text);
    pause();
    data=loaded; trial=data.trials[Number(el("scenario").value)]; index=0;
    liveStop=null;
    draw(); drawEditor();
    el("edit-message").textContent="Map loaded. Press Play. Restore map returns to the selected built-in map.";
  } catch(error) {
    if(revision===loadRevision) el("edit-message").textContent="Could not load map: "+error.message;
  } finally {
    if(revision===loadRevision) input.value="";
  }
};
