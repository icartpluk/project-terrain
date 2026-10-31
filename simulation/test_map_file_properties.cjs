// Deterministic map-file parser boundary and malformed-input properties.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const editor = fs.readFileSync(path.join(__dirname, 'editor.js'), 'utf8');
const start = editor.indexOf('function parseMapFile(text) {');
const end = editor.indexOf('\nfunction mapFileText()', start);
assert.ok(start >= 0 && end > start, 'map parser source markers must exist');

const context = vm.createContext({
  editedReplay(grid, faultTick, communicationDelay, stoppingDelay) {
    return {grid: grid.slice(), fault_tick: faultTick,
      communication_delay: communicationDelay, stopping_delay: stoppingDelay};
  }
});
vm.runInContext(editor.slice(start, end) +
  '\nglobalThis.parseMapFileUnderTest = parseMapFile;', context);

function parse(text) {
  context.input = text;
  return JSON.parse(JSON.stringify(vm.runInContext(
    'parseMapFileUnderTest(input)', context)));
}
function encode(value) { return JSON.stringify(value); }
function clone(value) { return JSON.parse(JSON.stringify(value)); }

const base = {version: 1, grid: ['#####', '#S.G#', '#####'], fault_tick: 8};
const largest = Array.from({length: 41}, (_, y) =>
  Array.from({length: 41}, (_, x) =>
    x === 0 || y === 0 || x === 40 || y === 40 ? '#' : '.').join(''));
largest[1] = '#S' + largest[1].slice(2);
largest[39] = largest[39].slice(0, 39) + 'G#';

for (const map of [
  base,
  {...base, communication_delay: 0, stopping_delay: 0},
  {...base, communication_delay: 100, stopping_delay: 100},
  {...base, grid: largest, fault_tick: 1000000}
]) {
  const text = encode(map);
  assert.deepEqual(parse(text), parse(text), 'valid input parsing must be deterministic');
}

const exactlyAtLimit = encode(base) +
  ' '.repeat(32768 - encode(base).length);
assert.equal(exactlyAtLimit.length, 32768);
assert.deepEqual(parse(exactlyAtLimit), parse(encode(base)),
  'a valid file at the documented byte/character limit must parse');
assert.throws(() => parse(exactlyAtLimit + ' '), /32 KB/);

const malformedTexts = [
  '', '{', '{"version":1,', encode(null), encode([]), encode('map'),
  encode({...base}) + ','
];
for (const text of malformedTexts)
  assert.throws(() => parse(text), undefined, 'malformed JSON/root must be rejected');

const invalidMaps = [];
function changed(label, change) {
  const map = clone(base);
  change(map);
  invalidMaps.push({label, text: encode(map)});
}
for (const value of [0, 2, '1', null, true, {}])
  changed('version', map => { map.version = value; });
for (const value of [null, '#####', [], [null], ['###', '#SG#', '####'],
  ['#####', '#S..#', '#####'], ['#####', '#SSG#', '#####'],
  ['#####', '#S.GG', '#####'], ['#####', '#S<G#', '#####'],
  ['.####', '#S.G#', '#####'], Array(42).fill('#'.repeat(42)),
  ['#'.repeat(42), ...Array(3).fill('#S' + '.'.repeat(39) + 'G#'), '#'.repeat(42)]])
  changed('grid shape/content', map => { map.grid = value; });
changed('missing grid', map => { delete map.grid; });
for (const value of [0, -1, 1.5, 1000001, '8', null, true, {}])
  changed('fault tick', map => { map.fault_tick = value; });
for (const field of ['communication_delay', 'stopping_delay'])
  for (const value of [-1, 1.5, 101, '0', null, true, {}])
    changed(field, map => { map[field] = value; });

for (const {label, text} of invalidMaps)
  assert.throws(() => parse(text), undefined, label + ' must be rejected');

console.log('Map parser checks passed: deterministic valid parsing, size boundaries, and ' +
  invalidMaps.length + ' generated malformed-input cases.');
