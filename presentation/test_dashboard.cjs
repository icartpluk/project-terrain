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
assert.equal(get("events").children.length, payload.trials[0].events.length);
assert.equal(get("status-line").textContent, "READY");

get("scenario").value = "1";
get("scenario").listeners.change();
assert.equal(get("events").children.length, payload.trials[1].events.length);
for (let i = 0; i < payload.trials[1].events.length; i++) get("step").listeners.click();
assert.equal(get("status-line").textContent, "SAFE STOP · COMMUNICATION LOSS");
assert.equal(String(get("tick-value").textContent), String(payload.trials[1].events.at(-1).tick));
assert.equal(get("position").textContent, payload.trials[1].final_position.join(", "));
assert.equal(get("play").disabled, true);

get("reset").listeners.click();
assert.equal(get("tick-value").textContent, "0");
assert.equal(get("status-line").textContent, "READY");
console.log("Dashboard playback checks passed: scenario selection, recorded stop, reset and telemetry.");
