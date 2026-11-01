const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const dataText = html.match(/<script id="simulation-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const payload = JSON.parse(dataText);
const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];

function element(id) {
  return {
    id, children: [], listeners: {}, style: {}, className: "", textContent: "", disabled: false,
    classList: {add() {}},
    append(...nodes) { this.children.push(...nodes); },
    replaceChildren(...nodes) { this.children = nodes; },
    addEventListener(name, callback) { this.listeners[name] = callback; },
  };
}

const elements = new Map();
const document = {
  getElementById(id) {
    if (id === "simulation-data") return {textContent: dataText};
    if (!elements.has(id)) elements.set(id, element(id));
    return elements.get(id);
  },
  createElement: tag => element(tag),
};
vm.runInNewContext(script, {document, clearInterval, setInterval}, {timeout: 1000});

const get = id => elements.get(id);
assert.equal(get("scenario").children.length, 4);
assert.equal(get("world").children.length, payload.worlds.length);
assert.equal(get("events").children.length, payload.worlds[0].trials[0].events.length);
assert.equal(get("map").children.length, payload.worlds[0].grid.length * payload.worlds[0].grid[0].length);
assert.equal(get("status-line").textContent, "READY");

get("world").value = "1";
get("world").listeners.change();
assert.equal(get("map").children.length, payload.worlds[1].grid.length * payload.worlds[1].grid[0].length);
assert.ok(get("provenance").textContent.includes(`seed ${payload.worlds[1].seed}`));
get("world").value = "0";
get("world").listeners.change();

get("scenario").value = "1";
get("scenario").listeners.change();
const trial = payload.worlds[0].trials[1];
assert.equal(get("events").children.length, trial.events.length);
for (let i = 0; i < trial.events.length; i++) get("step").listeners.click();
assert.equal(get("status-line").textContent, "SAFE STOP · COMMUNICATION LOSS");
assert.equal(String(get("tick-value").textContent), String(trial.events.at(-1).tick));
assert.equal(get("position").textContent, trial.final_position.join(", "));
assert.equal(get("play").disabled, true);

get("reset").listeners.click();
assert.equal(get("tick-value").textContent, "0");
assert.equal(get("status-line").textContent, "READY");
console.log("Dashboard playback checks passed: seeded environment selection, recorded stop, reset and telemetry.");
