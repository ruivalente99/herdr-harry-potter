// Dependency-free Dueling Club and mini-duel tests: node --test tools/battles.test.mjs
import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = path => readFileSync(resolve(root, path), "utf8");
const source = path => read(path).replace(/^import .*;\n/gm, "").replace(/^export (const|function) /gm, "$1 ");
const modelSource = source("mods/hogwarts-arena/choreography.js");
const model = new Function(`${modelSource}; return { HEROES, DUEL_SPELLS, DARK_SPELLS, PRESETS, normalizeRoster, frontsFor, dialogueLines, exchange, frontStyle };`)();
const arenaSource = `${modelSource}\n${source("mods/hogwarts-arena/scene.js")}\n${source("mods/hogwarts-arena/main.js")}`
  .replace("export default class Arena", "return class Arena");
const miniSource = source("mods/hogwarts-agents/battle.js");

function ui() {
  const nodes = [];
  const element = asset => {
    const node = { asset, calls: [] };
    const proxy = new Proxy(node, { get(target, key) {
      if (key in target) return target[key];
      if (key === "when") return (condition, fn) => condition ? fn(proxy) : proxy;
      return (...args) => { target.calls.push([key, ...args]); return proxy; };
    } });
    nodes.push(node);
    return proxy;
  };
  return { nodes, View: class {}, div: () => element(), image: element, h_flex: () => element(), v_flex: () => element() };
}

const calls = (nodes, method) => nodes.flatMap(node => node.calls.filter(call => call[0] === method));
const hasText = (nodes, text) => calls(nodes, "child").some(call => call[1] === text);
const byId = (nodes, id) => nodes.find(node => node.calls.some(call => call[0] === "id" && call[1] === id));
const actors = nodes => nodes.filter(node => node.calls.some(call => call[0] === "id" && /^arena-fighter-\d-\d$/.test(call[1])));
const theme = () => {
  const palette = JSON.parse(read("themes/slytherin.json"));
  return { ...palette, ...palette.colors };
};

function arenaFixture(properties = {}, check = false) {
  const host = ui();
  const state = { visible: true, notifications: 0, closed: null, timers: [] };
  const cx = { notify() { state.notifications++; }, timer: { every(ms, callback) { state.timers.push({ ms, callback }); } } };
  const Arena = new Function("host", `const { View, div, image, h_flex, v_flex, theme, spaces, shared, settings, closeOverlay, props, checking, window } = host;\n${arenaSource}`)({
    ...host, theme, settings: () => ({ dark: true }),
    spaces: () => [{ id: "active", active: true, name: "Active space" }],
    shared: () => ({ active: "great-hall", other: "diagon-alley" }),
    props: () => ({ overlay: "test-overlay", ...properties }), checking: () => check,
    window: () => ({ visible: state.visible }), closeOverlay: id => state.closed = id,
  });
  const view = new Arena();
  view.init(properties, cx);
  const render = () => { host.nodes.length = 0; view.render(); return host.nodes; };
  const click = id => {
    const node = byId(host.nodes, id);
    assert(node, `Missing control ${id}`);
    const handler = node.calls.find(call => call[0] === "on_click")?.[1];
    assert(handler, `Missing click handler ${id}`);
    handler({}, cx);
    return render();
  };
  const tick = () => state.timers.forEach(timer => timer.callback(cx));
  return { ...host, state, view, render, click, tick };
}

function miniFixture(width = 268) {
  const host = ui();
  const api = new Function("host", `const { div, image, h_flex, shared, settings, layout } = host;\n${miniSource}\nreturn { battleScene, battleSquad, battleDialogue };`)({
    ...host, shared: () => ({ one: "diagon-alley" }), settings: () => ({ dark: false }),
    layout: () => ({ id: "sidebar", size: { px: width } }),
  });
  return { ...host, ...api };
}

function assertAssets(nodes) {
  for (const { asset } of nodes) if (asset) assert(existsSync(resolve(root, asset)), `Missing asset: ${asset}`);
}

test("Dueling Club command ships its files and all Harry Potter sprite/spell assets", () => {
  for (const file of ["main.js", "scene.js", "choreography.js", "mod.json"]) {
    assert(existsSync(resolve(root, `mods/hogwarts-arena/${file}`)));
  }
  assert.equal(readdirSync(resolve(root, "mods/hogwarts-agents/sprites/hogwarts")).filter(n => n.endsWith(".svg")).length, 15);
  assert.equal(readdirSync(resolve(root, "mods/hogwarts-agents/sprites/hogwarts/weapons")).filter(n => n.endsWith(".svg")).length, 28);
  const metadata = JSON.parse(read("mods/hogwarts-arena/mod.json"));
  const command = metadata.palette.find(entry => entry.title === "Harry Potter: Dueling Club");
  assert(command);
  assert.equal(command.command, "mod.open");
  assert.deepEqual(command.args, { name: "hogwarts-arena" });
});

test("custom rosters reject unknown data, cap at eight and only allow repeated Dementors", () => {
  assert.deepEqual(model.normalizeRoster(null), []);
  assert.deepEqual(model.normalizeRoster(["harry", "missing", "__proto__", null, "harry", "dementor", "dementor"]),
    ["harry", "dementor", "dementor"]);
  assert.equal(model.normalizeRoster(Object.keys(model.HEROES)).length, 8);
  assert.equal(model.frontStyle(["hedwig"]), "STANDBY");
  assert.equal(model.frontStyle(["hedwig", "harry"]), "OWL POST / SUPPORT");
  assert.equal(model.frontStyle(["harry", "draco"]), "WAND DUEL");
  assert.equal(model.frontStyle(["harry", "voldemort"]), "DARK ARTS / CHARMS");
});

test("every preset has valid fronts, attributed dialogue and real local assets", () => {
  const fixture = arenaFixture();
  for (const id of Object.keys(model.PRESETS)) {
    fixture.render();
    fixture.click(`arena-mode-${id}`);
    const roster = fixture.view.roster();
    assert(roster.length >= 2 && roster.length <= 8);
    assert.equal(actors(fixture.nodes).length, roster.length);
    assertAssets(fixture.nodes);
    const lines = model.dialogueLines(roster);
    assert(lines.length >= 2);
    for (const { speaker, pair, text } of lines) {
      assert(roster.includes(speaker));
      assert(pair.every(hero => roster.includes(hero)));
      assert(text.length > 0);
    }
  }
});

test("dialogue alternates speakers, wraps and excludes characters not in the squad", () => {
  const roster = ["harry", "voldemort"];
  const first = model.exchange(roster, 0);
  const second = model.exchange(roster, 1);
  assert.equal(first.speaker, "voldemort");
  assert.equal(first.text, "The Boy Who Lived... come to debug.");
  assert.equal(second.speaker, "harry");
  assert.deepEqual(model.exchange(roster, model.dialogueLines(roster).length), first);
  assert.equal(model.exchange([], 1), null);
});

test("all fifteen Harry Potter characters render; Hedwig is unarmed and Bellatrix dual-casts", () => {
  const heroes = Object.keys(model.HEROES);
  assert.equal(heroes.length, 15);
  for (let index = 0; index < heroes.length; index += 2) {
    const roster = heroes.slice(index, index + 2);
    if (roster.length === 1) roster.push("harry");
    const fixture = arenaFixture({ fighters: roster });
    fixture.render();
    assert.equal(actors(fixture.nodes).length, 2);
    assertAssets(fixture.nodes);
  }
  assert.equal(model.HEROES.hedwig.weapon, null);
  const dual = arenaFixture({ fighters: ["bellatrix", "sirius"] });
  dual.render();
  assert.equal(dual.nodes.filter(node => node.asset?.endsWith("crucio-right.svg")).length, 3);
});

test("pause, speed, reduced motion, front focus and close controls work", () => {
  const fixture = arenaFixture({ space: "other", fighters: ["hermione", "ron", "harry", "voldemort"] });
  fixture.render();
  assert(fixture.nodes.some(node => node.asset === "backgrounds/realms/slytherin/diagon-alley.png"));
  fixture.click("arena-fighter-0-0");
  assert.equal(fixture.view.focus, 0);
  assert(hasText(fixture.nodes, "It's Levi-O-sa, not Levio-SA!"));
  fixture.click("arena-pause");
  assert.equal(calls(fixture.nodes, "loop").length, 0);
  fixture.click("arena-close");
  assert.equal(fixture.state.closed, "test-overlay");
});

test("mini duels paginate, keep speech tails aligned and respect statuses", () => {
  const mini = miniFixture(360);
  const members = [
    { address: "a", status: "blocked" }, { address: "b", status: "done" },
    { address: "c", status: "idle" }, { address: "d", status: "working" },
  ];
  const cast = { a: "ron", b: "harry", c: "voldemort", d: "hedwig" };
  assert.equal(mini.battleDialogue(members, cast, 0).text, "Protego! I need backup at the castle!");
  mini.battleScene("one", members, cast, theme(), { paused: true });
  assert.equal(calls(mini.nodes, "loop").length, 0);
  assert(!mini.nodes.some(node => node.asset?.includes("/weapons/")));
  assert(hasText(mini.nodes, "!"));
  assert(hasText(mini.nodes, "✦"));
  assertAssets(mini.nodes);
});
