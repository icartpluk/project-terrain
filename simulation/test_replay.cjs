const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || 'results/animation.html', 'utf8');
const data = html.match(/<script id="replay-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const elements = {};
function element(id) {
  return elements[id] ||= {textContent:'', value:'', children:[],
    setAttribute(k,v) { this[k]=v; }, appendChild(n) {this.children.push(n);},
    replaceChildren() {this.children=[];}};
}
element('replay-data').textContent = data;
element('speed').value = '600';
let scheduled = null;
vm.runInNewContext(code, {
  document:{getElementById:element, createElementNS:()=>element('node'+Math.random())},
  setTimeout:fn=>{scheduled=fn;return 1;}, clearTimeout:()=>{scheduled=null;}
});
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
console.log('Playback checks passed: play/pause, step, reset, seek, all three latched stops, and arrival.');
