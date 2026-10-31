const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || 'results/animation.html', 'utf8');
const data = html.match(/<script id="replay-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const elements = {};
function element(id) {
  return elements[id] ||= {textContent:'', value:'', children:[], style:{}, focus(){}, click(){}, remove(){},
    setAttribute(k,v) { this[k]=v; }, appendChild(n) {this.children.push(n);},
    replaceChildren() {this.children=[];}};
}
element('replay-data').textContent = data;
element('speed').value = '600';
let scheduled = null, focusedElement=null;
let savedBlob, revoked=false;
const context = vm.createContext({
  Blob,
  URL:{createObjectURL(blob){savedBlob=blob;return 'blob:test';},revokeObjectURL(){revoked=true;}},
  document:{body:element('body'),getElementById:element, createElement:()=>element('option'+Math.random()),
    createElementNS:()=>element('node'+Math.random())},
  setTimeout:fn=>{scheduled=fn;return 1;}, clearTimeout:()=>{scheduled=null;}
});
vm.runInContext(code, context);
assert.equal(element('status').textContent, 'READY');
const partialStart = element('partial-map').textContent;
assert.match(partialStart, /\?/);
assert.match(element('partial-status').textContent, /Tick 0/);
assert.equal(element('partial-step').disabled, false);
assert.equal(element('partial-reset').disabled, undefined);
element('partial-step').onclick();
assert.notEqual(element('partial-map').textContent, partialStart);
assert.match(element('partial-status').textContent, /Tick 1/);
while (!element('partial-step').disabled) element('partial-step').onclick();
assert.match(element('partial-status').textContent, /GOAL REACHED/);
element('partial-reset').onclick();
assert.equal(element('partial-map').textContent, partialStart);
assert.match(element('partial-status').textContent, /Tick 0/);
const partialPayload = JSON.parse(vm.runInContext('JSON.stringify(payload.partial_observation)',context));
assert.deepEqual(Object.keys(partialPayload).sort(),['frames','moves','sensor_radius_cells','status']);
element('play').onclick();
assert.equal(element('play').textContent, 'Pause');
scheduled();
assert.equal(element('status').textContent, 'MOVING');
element('play').onclick();
assert.equal(scheduled, null);
for (const [choice, cause] of [[1,'LINK LOSS'],[2,'E-STOP'],[3,'UNAUTHORIZED COMMAND']]) {
  element('scenario').value=String(choice); element('scenario').onchange();
  for(let i=0;i<8;i++) element('step').onclick();
  assert.equal(element('status').textContent, 'SAFE STOP — '+cause);
  assert.equal(element('play').disabled, true);
  const detail=element('detail').textContent;
  element('step').onclick();
  assert.equal(element('detail').textContent, detail);
  element('reset').onclick();
  assert.equal(element('status').textContent, 'READY');
  element('seek').value='8'; element('seek').oninput();
  assert.equal(element('status').textContent, 'SAFE STOP — '+cause);
}
element('scenario').value='0'; element('scenario').onchange();
element('play').onclick();
while(scheduled) scheduled();
assert.equal(element('status').textContent, 'GOAL REACHED');
assert.equal(element('play').disabled,true);
assert.equal(element('play').textContent,'Play');
const bank = JSON.parse(data).maps;
assert.ok(bank.length > 2);
element('play').onclick();
element('new-map').onclick();
assert.equal(scheduled, null);
assert.equal(Number(element('world').value), 1);
assert.match(element('map-info').textContent, new RegExp(String(bank[1].seed)));
for (let i=1;i<bank.length;i++) {
  element('world').value=String(i); element('world').onchange();
  for (let scenario=0;scenario<4;scenario++) {
    element('scenario').value=String(scenario); element('scenario').onchange();
    const expected=bank[i].trials[scenario];
    if (expected.status==='NO_ROUTE') {
      assert.equal(element('status').textContent,'NO ROUTE');
      assert.equal(element('play').disabled,true);
    } else {
      assert.equal(element('status').textContent,'READY');
      element('play').onclick();
      while(scheduled) scheduled();
      assert.ok(element('detail').textContent.includes('Position ('+expected.final_position.join(', ')+')'));
      assert.equal(element('status').textContent, expected.safe_stop
        ? 'SAFE STOP — '+({link_loss:'LINK LOSS',estop:'E-STOP',unauthorized:'UNAUTHORIZED COMMAND'})[expected.scenario]
        : 'GOAL REACHED');
    }
  }
}
element('new-map').onclick();
assert.equal(Number(element('world').value),1);
element('world').value='0'; element('world').onchange();
assert.equal(Number(element('world').value),0);
assert.equal(element('status').textContent,'READY');
console.log('Map checks passed: selection, timer cancellation, bank wraparound, every seeded scenario, and unreachable maps.');
console.log('Playback checks passed: play/pause, step, reset, seek, all three latched stops, and arrival.');

// Verify the browser planner/safety model against Python, including edited grids.
const {spawnSync}=require('node:child_process');
const fixtures=bank.map(w=>w.grid);
fixtures.push(["#####","#S.G#","#####"],["#####","#S#G#","#####"],
  ["######","#S...#","#.#G.#","######"]);
const python=spawnSync(process.env.PYTHON || 'python', ['-c',
  'import sys,json; sys.path.insert(0,"simulation"); from sim import simulate; grids=json.load(sys.stdin); print(json.dumps([[simulate(s,t,g) for s in ("normal","link_loss","estop","unauthorized")] for g in grids for t in (1,8,1000)]))'],
  {input:JSON.stringify(fixtures),encoding:'utf8'});
assert.equal(python.status,0,python.stderr);
const partialPython=spawnSync(process.env.PYTHON || 'python',['-c',
  'import json,sys; sys.path.insert(0,"simulation"); from partial_observation import simulate_partial_observation; r=simulate_partial_observation(("#########","#.......#","#S.###.G#","#.......#","#########"),sensor_radius=1,obstacle_changes=[{"tick":2,"position":[2,1],"blocked":True}]); print(json.dumps({"frames":r["frames"],"moves":r["moves"],"sensor_radius_cells":r["sensor_radius_cells"],"status":r["status"]}))'],
  {encoding:'utf8'});
assert.equal(partialPython.status,0,partialPython.stderr);
assert.deepEqual(partialPayload,JSON.parse(partialPython.stdout));
assert.equal(partialPayload.frames.at(-1).event,'MOVE');
assert.ok(partialPayload.frames.some(frame=>frame.known_map.some(row=>row.includes('#')&&row.includes('?'))));
console.log('Partial-observation checks passed: Python parity, hidden map data, initial unknown cells, step/reset and completion state.');
const expected=JSON.parse(python.stdout);
let fixtureIndex=0;
for(const grid of fixtures) for(const tick of [1,8,1000]) {
  const actual=vm.runInContext('editedReplay('+JSON.stringify(grid)+','+tick+').trials',context);
  assert.deepEqual(JSON.parse(JSON.stringify(actual)),expected[fixtureIndex++]);
}
element('scenario').value='0'; element('scenario').onchange();
element('edit-tool').value='obstacle';
const width=bank[0].grid[0].length;
const clickCell=(x,y)=>element('editor').children[y*width+x].onclick();
assert.equal(element('editor').children[0].disabled,true);
assert.equal(element('editor').children[width+1].disabled,true);
element('play').onclick();
clickCell(2,1);
assert.equal(scheduled,null);
assert.equal(element('editor').children[width+2].textContent,'#');
assert.equal(element('map-info').textContent,'Custom map (unsaved)');
assert.equal(element('seek').value,0);
clickCell(2,1);
assert.equal(element('editor').children[width+2].textContent,'·');
element('edit-tool').value='goal';
clickCell(2,1);
element('play').onclick(); while(scheduled) scheduled();
assert.equal(element('status').textContent,'GOAL REACHED');
assert.ok(element('detail').textContent.includes('Position (2, 1)'));
element('edit-tool').value='obstacle';
clickCell(2,1);
assert.match(element('edit-message').textContent,/Move the destination/);
clickCell(1,2); // Block the other exit.
element('edit-tool').value='goal'; clickCell(3,1);
element('edit-tool').value='obstacle'; clickCell(2,1);
assert.equal(element('status').textContent,'NO ROUTE');
assert.equal(element('play').disabled,true);
element('restore-map').onclick();
assert.equal(element('status').textContent,'READY');
assert.equal(element('editor').children[width+2].textContent,'·');
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(worlds)',context)),bank);
console.log('Editor checks passed: Python parity, obstacles, destination, no route, cancellation and restore.');

for(const [button,reason] of [['live-link','LINK LOSS'],['live-estop','E-STOP'],
                            ['live-unauthorized','UNAUTHORIZED COMMAND']]) {
  for(const moves of [0,1,bank[0].trials[0].events.length-1]) {
    element('scenario').value='0'; element('scenario').onchange();
    assert.equal(element(button).disabled,true);
    element('play').onclick();
    for(let i=0;i<moves;i++) scheduled();
    const stale=scheduled;
    const beforePosition=vm.runInContext('JSON.stringify(index ? trial.events[index-1].position : data.start)',context);
    assert.equal(element(button).disabled,false);
    element(button).onclick();
    assert.equal(scheduled,null);
    assert.equal(element('status').textContent,'SAFE STOP — '+reason);
    assert.equal(element('play').disabled,true);
    assert.equal(element('step').disabled,true);
    assert.equal(element('seek').disabled,true);
    assert.equal(vm.runInContext('JSON.stringify(liveStop.position)',context),beforePosition);
    const detail=element('detail').textContent;
    element('play').onclick(); element('step').onclick();
    element('seek').value='0'; element('seek').oninput();
    stale();
    element('live-estop').onclick();
    assert.equal(element('detail').textContent,detail);
    assert.equal(element('status').textContent,'SAFE STOP — '+reason);
    element('reset').onclick();
    assert.equal(element('status').textContent,'READY');
    assert.equal(element('play').disabled,false);
    assert.equal(element('seek').disabled,false);
  }
}
// Completed and paused runs cannot be relabeled as live stops.
element('play').onclick(); while(scheduled) scheduled();
element('live-link').onclick();
assert.equal(element('status').textContent,'GOAL REACHED');
element('reset').onclick(); element('play').onclick(); element('play').onclick();
element('live-estop').onclick();
assert.equal(element('status').textContent,'READY');
assert.equal(element('live-estop').disabled,true);
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(worlds)',context)),bank);
console.log('Live-stop checks passed: all causes, first/intermediate/final positions, latch, stale callbacks, reset and disabled states.');

element('scenario').value='0'; element('scenario').onchange();
element('play').onclick(); scheduled(); element('play').onclick();
assert.equal(element('status').textContent,'PAUSED');
const neighbor=element('editor').children[width+3];
neighbor.focus=()=>{focusedElement=neighbor;};
let prevented=false;
element('editor').children[width+2].onkeydown({key:'ArrowRight',preventDefault(){prevented=true;}});
assert.equal(prevented,true);
assert.equal(focusedElement,neighbor);
element('reset').onclick();

const timedFixtures=[...fixtures.slice(0,3),...fixtures.slice(-3)];
const timedReference=spawnSync(process.env.PYTHON || 'python',['-c',
  'import sys,json; sys.path.insert(0,"simulation"); from timing import simulate_timed; grids=json.load(sys.stdin); print(json.dumps([[simulate_timed(s,t,g,c,b) for s in ("normal","link_loss","estop","unauthorized")] for g in grids for t in (1,3,1000) for c,b in ((0,0),(2,1),(0,2),(3,0))]))'],
  {input:JSON.stringify(timedFixtures),encoding:'utf8',maxBuffer:4*1024*1024});
assert.equal(timedReference.status,0,timedReference.stderr);
let timedIndex=0;
const timedExpected=JSON.parse(timedReference.stdout);
for(const grid of timedFixtures) for(const tick of [1,3,1000])
  for(const [communication,stopping] of [[0,0],[2,1],[0,2],[3,0]]) {
    const actual=vm.runInContext('timedWorld(editedReplay('+JSON.stringify(grid)+','+tick+'),'+communication+','+stopping+').trials',context);
    assert.deepEqual(JSON.parse(JSON.stringify(actual)),timedExpected[timedIndex++]);
  }
const applyDelays=(c,s)=>{
  element('communication-delay').value=String(c); element('stopping-delay').value=String(s);
  element('apply-delays').onclick();
};
for(const [choice,reason,latency] of [[1,'LINK LOSS',3],[2,'E-STOP',1],[3,'UNAUTHORIZED COMMAND',3]]) {
  applyDelays(2,1);
  element('scenario').value=String(choice); element('scenario').onchange();
  element('play').onclick();
  for(let i=0;i<8;i++) scheduled();
  assert.match(element('status').textContent, /DELAY/);
  assert.equal(element('status').className,'pending');
  while(scheduled) scheduled();
  assert.equal(element('status').textContent,'SAFE STOP — '+reason);
  assert.match(element('delay-comparison').textContent,new RegExp(latency+' ticks, '+latency+' extra cells'));
}
for(const [button,reason,latency] of [['live-link','LINK LOSS',3],['live-estop','E-STOP',1],
                                     ['live-unauthorized','UNAUTHORIZED COMMAND',3]]) {
  element('scenario').value='0'; element('scenario').onchange();
  element('play').onclick(); scheduled();
  element(button).onclick();
  assert.equal(element('seek').disabled,true);
  scheduled();
  assert.match(element('status').textContent,/DELAY/);
  const pendingPosition=vm.runInContext('JSON.stringify(trial.events[index-1].position)',context);
  element('play').onclick(); // Pause and resume the response.
  element('step').onclick();
  assert.notEqual(element('status').textContent,'GOAL REACHED');
  if(!element('play').disabled) { element('play').onclick(); while(scheduled) scheduled(); }
  assert.equal(element('status').textContent,'SAFE STOP — '+reason);
  assert.match(element('delay-comparison').textContent,new RegExp(latency+' ticks, '+latency+' extra cells'));
  const stopped=element('detail').textContent;
  element('step').onclick(); assert.equal(element('detail').textContent,stopped);
  element('reset').onclick();
  assert.equal(element('status').textContent,'READY');
}
const delayedSave=vm.runInContext('mapFileText()',context);
assert.equal(JSON.parse(delayedSave).communication_delay,2);
assert.equal(JSON.parse(delayedSave).stopping_delay,1);
assert.equal(vm.runInContext('parseMapFile('+JSON.stringify(delayedSave)+').communication_delay',context),2);
element('new-map').onclick();
assert.equal(vm.runInContext('data.communication_delay',context),2);
element('world').value='0'; element('world').onchange();
assert.equal(vm.runInContext('data.stopping_delay',context),1);
for(const value of [-1,101,1.5,null,"2",true]) {
  const bad=JSON.stringify({...JSON.parse(delayedSave),communication_delay:value});
  assert.throws(()=>vm.runInContext('parseMapFile('+JSON.stringify(bad)+')',context),/whole ticks/);
}
applyDelays(-1,0);
assert.match(element('edit-message').textContent,/whole ticks/);
applyDelays(0,0);
element('scenario').value='0'; element('scenario').onchange();
console.log('Timing checks passed: Python parity, scheduled/live phases, distances, E-stop bypass, delay persistence and zero defaults.');

(async()=>{
  element('edit-tool').value='obstacle'; clickCell(2,1);
  element('save-map').onclick();
  const text=await savedBlob.text(), saved=JSON.parse(text);
  assert.equal(saved.version,1);
  assert.equal(saved.grid[1][2],'#');
  assert.equal(saved.fault_tick,8);
  assert.deepEqual(Object.keys(saved).sort(),['fault_tick','grid','version']);
  scheduled(); scheduled=null;
  assert.equal(revoked,true);
  element('restore-map').onclick();
  const load=async(text,size=Buffer.byteLength(text))=>{
    element('load-map').files=[{size,text:async()=>text}];
    await element('load-map').onchange();
  };
  await load(text);
  assert.equal(element('editor').children[width+2].textContent,'#');
  assert.equal(element('seek').value,0);
  assert.equal(vm.runInContext('mapFileText()',context),text);
  // Bad inputs must not replace the current geometry, events or playback tick.
  const before=vm.runInContext('JSON.stringify(data)',context);
  const invalid=[
    'bad JSON', 'null', JSON.stringify({...saved,version:2}),
    JSON.stringify({...saved,grid:['###','#S#','###']}),
    JSON.stringify({...saved,grid:['#####','#SSG#','#####']}),
    JSON.stringify({...saved,grid:['#####','#S.G#','####']}),
    JSON.stringify({...saved,grid:['#####','#S<G#','#####']}),
    JSON.stringify({...saved,grid:['.####','#S.G#','#####']}),
    ...[0,1.5,1000001,'8'].map(fault_tick=>JSON.stringify({...saved,fault_tick})),
    JSON.stringify({...saved,grid:Array(42).fill('#'.repeat(42))})
  ];
  for(const bad of invalid) {
    await load(bad);
    assert.match(element('edit-message').textContent,/Could not load map/);
    assert.equal(vm.runInContext('JSON.stringify(data)',context),before);
    assert.equal(element('load-map').value,'');
  }
  await load(text,32769);
  assert.match(element('edit-message').textContent,/32 KB/);
  const blocked=JSON.stringify({version:1,grid:['#####','#S#G#','#####'],fault_tick:1});
  element('play').onclick();
  await load(blocked);
  assert.equal(scheduled,null);
  assert.equal(element('status').textContent,'NO ROUTE');
  assert.equal(element('play').disabled,true);
  // A slow file read must not overwrite a newer map selection.
  let resolveRead;
  element('load-map').files=[{size:10,text:()=>new Promise(resolve=>{resolveRead=resolve;})}];
  const pending=element('load-map').onchange();
  element('restore-map').onclick();
  resolveRead(blocked); await pending;
  assert.equal(element('status').textContent,'READY');
  assert.equal(element('map-info').textContent,'Original demo');
  console.log('Save/load checks passed: round trip, download cleanup, invalid files, no route, and stale reads.');
})().catch(error=>{console.error(error);process.exitCode=1;});
