// Notification routing tests: never post real banners or launch applications.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = path => readFileSync(resolve(root, path), "utf8");
const notificationSource = read("mods/hogwarts-alerts/main.js");
const source = notificationSource.replace(/^import .*;\n/gm, "")
  .replace("export default class Toast", "return class Toast");
const flush = () => new Promise(resolve => setImmediate(resolve));

function fixture({ platform = "macos", active = false, checking = false, missingWindow = false,
  payload = {}, cast = {}, execute = async () => ({ code: 0, stderr: "" }) } = {}) {
  const state = { executions: [], warnings: [], errors: [], runs: [], closed: [], nodes: [] };
  const element = asset => {
    const node = { asset, calls: [] };
    const proxy = new Proxy(node, { get(target, key) {
      if (key in target) return target[key];
      if (key === "when") return (condition, fn) => condition ? fn(proxy) : proxy;
      return (...args) => { target.calls.push([key, ...args]); return proxy; };
    } });
    state.nodes.push(node);
    return proxy;
  };
  const Toast = new Function("host", `const { View, div, image, v_flex, h_flex, props, closeOverlay, run, theme, shared, exec, window, appHome, checking, console } = host;\n${source}`)({
    View: class {}, div: () => element(), image: element, v_flex: () => element(), h_flex: () => element(),
    props: () => ({ overlay: "toast-test", ...payload }), closeOverlay: id => state.closed.push(id),
    run: (...args) => state.runs.push(args), theme: () => ({ accent: "#123456" }), shared: () => cast,
    exec: (command, args) => { state.executions.push({ command, args }); return execute(command, args); },
    window: () => missingWindow ? null : ({ platform, active }), appHome: () => "/tmp/herdr-test-home",
    checking: () => checking,
    console: { warn: message => state.warnings.push(message), error: message => state.errors.push(message) },
  });
  return { state, view: new Toast() };
}

test("character-aware owl-post banners keep Harry Potter attribution and target Herdr", async () => {
  const { state, view } = fixture({
    cast: { a1: "harry" },
    payload: { title: "pi finished", body: "Task complete", action: { name: "agent.focus", args: { terminal: "a1" } } },
  });
  view.init();
  await flush();
  assert.deepEqual(state.executions[0], {
    command: "terminal-notifier",
    args: ["-title", "Harry Potter caught the Snitch — mischief managed", "-message", "pi · Task complete", "-activate", "dev.herdr.app"],
  });
  view.render({});
  assert(state.nodes.some(node => node.asset === "mods/hogwarts-agents/sprites/hogwarts/harry.svg"));
});

test("safe macOS/Linux/Windows routing never falls back to AppleScript", async () => {
  assert(!/exec\(["'](?:osascript|open)["']/.test(notificationSource));
  const linux = fixture({ platform: "linux", payload: { title: "Done", body: "Ready" } });
  linux.view.init();
  await flush();
  assert.equal(linux.state.executions[0].command, "notify-send");
  const active = fixture({ active: true });
  active.view.init();
  await flush();
  assert.deepEqual(active.state.executions, []);
});
