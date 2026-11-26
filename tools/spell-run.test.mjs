import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const read = path => readFileSync(resolve(root, path), "utf8");
const strip = source => source.replace(/^import .*;\n/gm, "").replace(/^export /gm, "");
const modelSource = `${strip(read("mods/hogwarts-spell-run/decks.js"))}\n${strip(read("mods/hogwarts-spell-run/game.js"))}`;
const model = new Function(`${modelSource}\nreturn { DECKS, BUFFS, HEIGHT, WIDTH, STEP_MS, TICK_MS, cyclePayload, deckFor, powerFor, blastCells, placeLine, enemyRoster, trainingFor, normalizeProfile, nextLevel, movePlayer, newGame, placeBomb, tick };`)();
const { DECKS, BUFFS, HEIGHT, WIDTH, STEP_MS, cyclePayload, deckFor, powerFor, blastCells, placeLine, enemyRoster, trainingFor, normalizeProfile, nextLevel, movePlayer, newGame, placeBomb, tick } = model;
const sceneSource = strip(read("mods/hogwarts-spell-run/scene.js"));
const uiSource = strip(read("mods/hogwarts-spell-run/ui.js"));
const mainSource = strip(read("mods/hogwarts-spell-run/main.js")).replace("default class SpellRun", "class SpellRun");
const { fitTile, walkFrame } = new Function(`${modelSource}\n${sceneSource}\nreturn { fitTile, walkFrame };`)();

function files(path) {
  return readdirSync(resolve(root, path), { withFileTypes: true }).flatMap(item =>
    item.isDirectory() ? files(`${path}/${item.name}`) : [`${path}/${item.name}`]);
}

function harness({ overlay = false, focus = false, storage = new Map(), checkingRun = false } = {}) {
  const state = {
    storage, writes: 0, reads: 0,
    nodes: [], timers: [], focused: focus, visible: true, closed: [], commands: [], opened: [],
    ownProps: overlay ? { overlay: "game-overlay" } : { panel: "panel", stack: "panel-body", child: "spell-run" },
    tree: { id: "root", children: [{ id: "panel", hidden: false, children: [{ id: "panel-body", active: "spell-run" }] }] },
    cast: { first: "hermione", second: "dobby" },
    agents: [{ address: "first", space: "space-1", focused: true, status: "working", program: { name: "Pi" } },
      { address: "second", space: "space-1", focused: false, status: "idle", program: { name: "Claude Code" } }],
  };
  function element(asset) {
    const node = { asset, calls: [], kids: [] };
    const proxy = new Proxy(node, { get(target, key) {
      if (key in target) return target[key];
      if (key === "when") return (condition, fn) => condition ? fn(proxy) : proxy;
      if (key === "child") return child => { target.kids.push(child); return proxy; };
      if (key === "children") return children => { target.kids.push(...children); return proxy; };
      return (...args) => { target.calls.push([key, ...args]); return proxy; };
    } });
    state.nodes.push(node);
    return proxy;
  }
  const t = new Proxy({}, { get: () => "#abcdef" });
  const cx = {
    notify() {}, stop_propagation() {},
    focus_handle: () => ({ focus() { state.focused = true; }, is_focused: () => state.focused }),
    timer: { every(ms, callback) { state.timers.push({ ms, callback }); } },
  };
  const host = {
    View: class {}, div: () => element(), image: element, h_flex: () => element(), v_flex: () => element(),
    agents: () => state.agents, spaces: () => [{ id: "space-1", active: true }],
    shared: key => key === "hogwarts-agents.cast" ? state.cast : { "space-1": "great-hall" },
    theme: () => t, checking: () => checkingRun, props: () => state.ownProps,
    settings: () => ({ zoom: 1.2 }), window: () => ({ visible: state.visible }), layout: () => state.tree,
    closeOverlay: id => state.closed.push(id), run: (...args) => state.commands.push(args), openOverlay: args => state.opened.push(args),
    localStorage: {
      getItem: key => { state.reads++; return state.storage.get(key) ?? null; },
      setItem: (key, value) => { state.writes++; state.storage.set(key, value); },
    },
  };
  const SpellRun = new Function("host", `const { ${Object.keys(host).join(", ")} } = host;\n${modelSource}\n${sceneSource}\n${uiSource}\n${mainSource}\nreturn SpellRun;`)(host);
  const view = new SpellRun();
  view.init({}, cx);
  const render = () => { state.nodes = []; return view.render(); };
  const node = id => state.nodes.find(node => node.calls.some(call => call[0] === "id" && call[1] === id));
  const handler = (id, method) => {
    const found = node(id);
    assert(found, `Missing node: ${id}`);
    const call = found.calls.find(call => call[0] === method);
    assert(call, `Missing ${method} on ${id}`);
    return call.at(-1);
  };
  const click = id => handler(id, "on_click")({}, cx);
  const key = (key, extra = {}) => view.keyDown({ key, modifiers: {}, ...extra }, cx);
  const advanceMs = ms => { for (let i = 0; i < ms; i += state.timers[0].ms) state.timers[0].callback(cx); };
  const advance = (count = 1) => advanceMs(count * 80);
  return { state, view, cx, render, node, handler, click, key, advance, advanceMs };
}

test("Spell Run mod wires its palette command and layout panel", () => {
  const metadata = JSON.parse(read("mods/hogwarts-spell-run/mod.json"));
  assert.equal(metadata.palette[0].args.name, "hogwarts-spell-run");
  const tree = JSON.parse(read("layouts/hogwarts.json"));
  const game = tree.children[1].children[1].children[1].children[0].children.find(node => node.id === "spell-run");
  assert.deepEqual(game.content.props, { panel: "panel", stack: "panel-body", child: "spell-run" });
});

test("art is reproducible local pixel geometry with 60 distinct gait frames", () => {
  const paths = files("mods/hogwarts-spell-run/art");
  const destination = mkdtempSync(resolve(tmpdir(), "spell-run-art-"));
  try {
    const built = spawnSync("python3", [resolve(root, "tools/build-spell-run-art.py"), "--output", destination], { encoding: "utf8" });
    assert.equal(built.status, 0, built.stderr);
    const relative = path => path.slice("mods/hogwarts-spell-run/art/".length);
    assert.deepEqual(files(destination).map(path => path.slice(destination.length + 1)), paths.map(relative));
    for (const path of paths) assert.equal(read(resolve(destination, relative(path))), read(path), path);
  } finally {
    rmSync(destination, { recursive: true, force: true });
  }
  const actors = files("mods/hogwarts-spell-run/art/actors");
  assert.equal(actors.length, 60);
  for (const path of actors) {
    const source = read(path);
    assert.match(source, /viewBox="0 0 96 32"/);
    const frames = [[], [], []];
    for (const [, sx, sy, sw, sh, color] of source.matchAll(/<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="([^"]+)"/g)) {
      const x = Number(sx), width = Number(sw);
      for (let dx = 0; dx < width; dx++) frames[Math.floor((x + dx) / 32)].push([((x + dx) % 32), +sy, +sh, color]);
    }
    assert.notDeepEqual(frames[0], frames[1], path);
    assert.notDeepEqual(frames[1], frames[2], path);
  }
});

test("eight Hogwarts rooms have distinct layouts, props, reachable tiles and unique characters", () => {
  assert.equal(DECKS.length, 8);
  assert.equal(new Set(DECKS.map(deck => deck.layout.join(""))).size, 8);
  assert.equal(new Set(DECKS.map(deck => deck.prop)).size, 8);
  const heroes = ["voldemort", "harry", "hermione", "ron", "dumbledore", "snape", "hagrid",
    "mcgonagall", "sirius", "draco", "luna", "bellatrix", "dobby", "hedwig", "dementor"];
  for (const hero of heroes) {
    for (let level = 1; level <= 8; level++) {
      const cast = [hero, ...enemyRoster(hero, 20, level)];
      const named = cast.filter(id => id !== "dementor");
      assert.equal(new Set(named).size, named.length);
    }
  }
  for (let level = 1; level <= 8; level++) {
    const game = newGame({ level });
    const seen = new Set(["1,1"]), queue = [{ x: 1, y: 1 }];
    for (const point of queue) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const x = point.x + dx, y = point.y + dy, key = `${x},${y}`;
      if (game.board[y]?.[x] == null || game.board[y][x] === "#" || seen.has(key)) continue;
      seen.add(key); queue.push({ x, y });
    }
    for (let y = 0; y < HEIGHT; y++) for (let x = 0; x < WIDTH; x++) {
      if (game.board[y][x] !== "#") assert(seen.has(`${x},${y}`));
    }
  }
});

test("cauldrons, blasts, upgrades, Fiendfyre, Time-Turner echo and Thinking-only gating work", () => {
  const game = newGame({ xp: 2400, level: 8, payload: "echo" });
  game.board[1].fill(".", 1, WIDTH - 1);
  for (let y = 1; y < HEIGHT - 1; y++) game.board[y][1] = ".";
  game.enemies = [{ id: 0, hero: "dementor", x: 3, y: 1 }];
  assert(placeBomb(game));
  game.bombs[0].fuse = 1;
  game.player = { x: 3, y: 3 };
  tick(game, 1);
  assert.equal(game.enemies.length, 0);
  assert.equal(game.echoes.length, 1);
  assert.equal(game.status, "playing");
  tick(game, 1000);
  assert.equal(game.status, "won");

  assert.equal(cyclePayload(newGame({ xp: 2400, level: 8 })), true);
  assert.equal(powerFor(newGame({ xp: 2200, level: 8 })).range, 5);
  assert.equal(powerFor(newGame({ xp: 1800, level: 7 })).stepMs, 120);
  assert.equal(trainingFor(2200).title, "Headmaster");

  const app = harness({ storage: new Map([["thinking-only", "true"]]) });
  app.state.agents[0].status = "idle";
  app.key("enter"); app.advance(4);
  assert.equal(app.view.started, false);
  app.state.agents[0].status = "working";
  app.key("enter"); app.key("space"); app.advance();
  assert.equal(app.view.started, true);
  assert.equal(app.view.game.bombs.length, 1);
  app.render();
  assert(app.state.nodes.some(n => n.asset?.includes("cauldron-")));
  assert(app.state.nodes.some(n => n.asset?.includes("actors/hermione-down")));
  assert.equal(fitTile(344, 440, 1) % 2, 0);
  assert.equal(walkFrame({ moving: false, movedAt: 0 }, 0, false), 0);
});
