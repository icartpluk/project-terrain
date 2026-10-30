const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || 'results/animation.html', 'utf8');
const data = html.match(/<script id="replay-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const elements = {};
function element(id) {
  return elements[id] ||= {textContent:'', value:'', children:[], style:{}, focus(){},
    setAttribute(k,v) { this[k]=v; }, appendChild(n) {this.children.push(n);},
    replaceChildren() {this.children=[];}};
}
element('replay-data').textContent = data;
element('speed').value = '600';
let scheduled = null;
const context = vm.createContext({
  document:{getElementById:element, createElement:()=>element('option'+Math.random()),
    createElementNS:()=>element('node'+Math.random())},
  setTimeout:fn=>{scheduled=fn;return 1;}, clearTimeout:()=>{scheduled=null;}
});
vm.runInContext(code, context);
assert.equal(element('status').textContent, 'READY');
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
