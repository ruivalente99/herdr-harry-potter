// Standard-library regression checks: node --test tools/themes.test.mjs
import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = path => readFileSync(resolve(root, path), "utf8");
const json = path => JSON.parse(read(path));
const sides = ["gryffindor", "slytherin"];
const palettes = sides.map(side => json(`themes/${side}.json`));
const realmsSource = read("mods/hogwarts-systems/realms.js").replace(/^export /gm, "");
const { REALMS, realmBackground } = new Function(`${realmsSource}; return { REALMS, realmBackground };`)();
const castingSource = read("mods/hogwarts-agents/casting.js").replace(/^export function /gm, "function ");
const { pickHero, repairCast } = new Function(`${castingSource}; return { pickHero, repairCast };`)();
const stripImports = source => source.replace(/^import .*;\n/gm, "");
const findLayoutNode = (node, id) => node.id === id ? node
  : (node.children ?? []).map(child => findLayoutNode(child, id)).find(Boolean);

function contrast(a, b) {
  const luminance = hex => {
    const channels = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
      .map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
    return channels.reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0);
  };
  const [low, high] = [luminance(a), luminance(b)].sort((x, y) => x - y);
  return (high + 0.05) / (low + 0.05);
}

function ui() {
  const nodes = [];
  function element(asset) {
    const node = { asset, calls: [] };
    const proxy = new Proxy(node, { get(target, key) {
      if (key in target) return target[key];
      if (key === "when") return (condition, fn) => condition ? fn(proxy) : proxy;
      return (...args) => { target.calls.push([key, ...args]); return proxy; };
    } });
    nodes.push(node);
    return proxy;
  }
  return { nodes, View: class {}, div: () => element(), image: element, svg: element,
    h_flex: () => element(), v_flex: () => element() };
}

function nativeTheme(palette) {
  return { ...palette, ...palette.colors,
    ...Object.fromEntries(palette.ansi.map((color, i) => [`ansi${i}`, color])) };
}

function checkColors(nodes, palette) {
  const allowed = new Set([palette.background, palette.foreground, ...palette.ansi,
    ...Object.values(palette.colors), `${palette.colors.done}1f`, "#fff3cf"]);
  for (const node of nodes) {
    for (const [method, color] of node.calls) {
      if (["bg", "text_color", "border_color"].includes(method)) {
        assert(allowed.has(color), `Unscoped ${method} color: ${color}`);
      }
    }
  }
}

test("one Hogwarts layout, exactly two theme palettes with identical roles", () => {
  assert.deepEqual(readdirSync(resolve(root, "themes")).filter(p => p.endsWith(".json")).sort(), sides.map(side => `${side}.json`).sort());
  assert.deepEqual(readdirSync(resolve(root, "layouts")).filter(p => p.endsWith(".json")), ["hogwarts.json"]);
  const layout = json("layouts/hogwarts.json");
  const panel = findLayoutNode(layout, "panel-body");
  assert.deepEqual(panel.children.map(child => child.id), ["files", "changes", "spell-run"]);
  assert.deepEqual(panel.children.map(child => child.title), ["Files", "Changes", "Spell Run"]);
  assert.equal(panel.active, "files");
  assert.equal(panel.header, undefined);
  assert.equal(findLayoutNode(layout, "tabs").content.mod, "hogwarts-tabs");
  assert.match(read("mods/hogwarts-tabs/main.js"), /panelButton\("spell-run", "Spell Run"/);
  assert.match(read("mods/hogwarts-tabs/main.js"), /enabled\.includes\("spell-run"\)/);
  assert(json("mods/hogwarts-tabs/mod.json").palette.some(entry => entry.command === "hogwarts-tabs.toggle-spell-run"));
  assert.deepEqual(layout.theme, { light: "gryffindor", dark: "slytherin" });
  assert(layout.terminal_opacity >= 0.85 && layout.terminal_opacity < 1);
  assert(existsSync(resolve(root, layout.preview)));
  assert(!/undefined|NaN|fill="null"/.test(read("layouts/hogwarts.svg")));
  assert.deepEqual(Object.keys(palettes[0].colors).sort(), Object.keys(palettes[1].colors).sort());
  for (const palette of palettes) {
    assert.equal(palette.ansi.length, 16);
    for (const value of [palette.background, palette.foreground, palette.selection, palette.cursor,
      ...palette.ansi, ...Object.values(palette.colors)]) assert.match(value, /^#[0-9a-f]{6}$/);
    assert(contrast(palette.colors.solid, palette.colors.solid_foreground) >= 4.5);
  }
});

test("interface text and semantic states meet 4.5:1 on all main surfaces", () => {
  for (const palette of palettes) {
    for (const role of ["foreground", "muted", "dim", "accent", "working", "blocked", "done"]) {
      for (const surface of ["chrome", "surface", "popover", "raised", "selected"]) {
        const foreground = palette[role] ?? palette.colors[role];
        const ratio = contrast(foreground, palette.colors[surface]);
        assert(ratio >= 4.5, `${role}/${surface}: ${ratio.toFixed(2)}:1`);
      }
    }
  }
});

test("all realm backgrounds have both appearances; unknown realms have no path", () => {
  assert.equal(REALMS.length, 7);
  for (const dark of [true, false]) {
    for (const realm of REALMS) {
      const path = realmBackground(realm, dark).image;
      assert(existsSync(resolve(root, path)), path);
      const png = readFileSync(resolve(root, path));
      assert.equal(png.subarray(1, 4).toString(), "PNG");
      assert.equal(png.readUInt32BE(16), 640);
      assert.equal(png.readUInt32BE(20), 360);
    }
  }
  assert.equal(realmBackground("missing"), null);
});

test("character roster has all generated sprites and only Dementors repeat", () => {
  const heroes = ["harry", "hermione", "ron", "dumbledore", "snape", "hagrid", "mcgonagall",
    "sirius", "draco", "luna", "bellatrix", "dobby", "hedwig", "dementor", "voldemort"];
  assert.equal(heroes.length, 15);
  for (const hero of heroes) {
    assert(existsSync(resolve(root, `mods/hogwarts-agents/sprites/hogwarts/${hero}.svg`)), hero);
  }
  const pool = ["harry", "hermione", "dementor"];
  const roster = [];
  for (let i = 0; i < pool.length + 4; i++) roster.push(pickHero(pool, roster, () => 0.5));
  const repeats = roster.filter((hero, index) => roster.indexOf(hero) !== index);
  assert(repeats.length > 0);
  assert(repeats.every(hero => hero === "dementor"));

  const saved = { first: "harry", duplicate: "harry", dA: "dementor", dB: "dementor", removed: "voldemort" };
  assert(repairCast(pool, saved));
  assert.deepEqual(saved, { first: "harry", dA: "dementor", dB: "dementor" });
});

test("character artwork preserves the transparent pixel grid and display size", () => {
  const directory = "mods/hogwarts-agents/sprites/hogwarts";
  const characters = readdirSync(resolve(root, directory)).filter(name => name.endsWith(".svg"));
  assert.equal(characters.length, 15);
  for (const name of characters) {
    const source = read(`${directory}/${name}`);
    assert.match(source, /viewBox="0 0 32 32" width="36" height="36" shape-rendering="crispEdges"/);
    assert.match(source, /<title>[^<]+ — pixel art<\/title>/);
    const pixels = [...source.matchAll(/<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)" fill="(#[0-9a-f]{6})"\/>/g)];
    assert(pixels.length > 0, name);
    assert.equal(pixels.length, (source.match(/<rect\b/g) ?? []).length, name);
    assert(pixels.some(pixel => pixel[5] === "#11151f"), `${name}: missing shared outline`);
    let coverage = 0;
    for (const [, sx, sy, sw, sh] of pixels) {
      const [x, y, width, height] = [sx, sy, sw, sh].map(Number);
      assert(width > 0 && x + width <= 32 && y < 32, `${name}: outside pixel grid`);
      assert.equal(height, 1, `${name}: expected horizontal pixel runs`);
      coverage += width;
    }
    assert(coverage < 32 * 32, `${name}: transparent background required`);
  }
});

test("Dueling Club follows both palettes, renders four fronts and preserves pause/close controls", () => {
  const modelSource = stripImports(read("mods/hogwarts-arena/choreography.js")).replace(/^export /gm, "");
  const sceneSource = stripImports(read("mods/hogwarts-arena/scene.js")).replace(/^export /gm, "");
  const source = `${modelSource}\n${sceneSource}\n${stripImports(read("mods/hogwarts-arena/main.js"))}`
    .replace("export default class Arena", "return class Arena");
  for (const [index, palette] of palettes.entries()) {
    const host = ui();
    let closed = null;
    const Arena = new Function("host", `const { View, div, image, h_flex, v_flex, theme, spaces, shared, settings, closeOverlay, props, checking, window } = host;\n${source}`)({
      ...host, theme: () => nativeTheme(palette), settings: () => ({ dark: index === 1 }),
      spaces: () => [{ id: "one", name: "Test", active: true }],
      shared: () => ({ one: "great-hall" }), props: () => ({ overlay: "arena-test" }),
      closeOverlay: id => closed = id, checking: () => true, window: () => ({ visible: true }),
    });
    const arena = new Arena();
    arena.init();
    arena.render();
    const expected = `backgrounds/realms/${sides[index]}/great-hall.png`;
    assert(host.nodes.some(n => n.asset === expected));
    assert.equal(host.nodes.filter(n => n.calls.some(c => c[0] === "id" && /^arena-fighter-\d-\d$/.test(c[1]))).length, 8);
    checkColors(host.nodes, palette);
    const click = id => host.nodes.find(n => n.calls.some(c => c[0] === "id" && c[1] === id))
      .calls.find(c => c[0] === "on_click")[1]({}, { notify() {} });
    click("arena-close");
    assert.equal(closed, "arena-test");
    click("arena-pause");
    host.nodes.length = 0;
    arena.render();
    assert(!host.nodes.some(n => n.calls.some(c => c[0] === "loop")));
    checkColors(host.nodes, palette);
  }
});

test("mini duels use their own realm and palette", () => {
  const source = stripImports(read("mods/hogwarts-agents/battle.js"))
    .replace(/^export (function|const) /gm, "$1 ");
  for (const [index, palette] of palettes.entries()) {
    const host = ui();
    const battle = new Function("host", `const { div, image, h_flex, shared, settings, layout } = host;\n${source}\nreturn battleScene;`)({
      ...host, shared: () => ({ active: "great-hall", other: "quidditch-pitch" }),
      settings: () => ({ dark: index === 1 }), layout: () => ({ id: "sidebar", size: { px: 360 } }),
    });
    battle("other", [{ address: "a" }, { address: "b" }], { a: "harry", b: "voldemort" }, nativeTheme(palette));
    assert(host.nodes.some(n => n.asset === `backgrounds/realms/${sides[index]}/quidditch-pitch.png`));
    assert(host.nodes.some(n => n.calls.some(c => c[0] === "child" && c[1] === "The Boy Who Lived... come to debug.")));
    checkColors(host.nodes, palette);

    for (const [first, second, quote] of [
      ["harry", "draco", "My father will hear about this merge conflict!"],
      ["hermione", "ron", "It's Levi-O-sa, not Levio-SA!"],
      ["dumbledore", "snape", "After all this time, Severus?"],
    ]) {
      host.nodes.length = 0;
      battle("other", [{ address: "a" }, { address: "b" }], { a: first, b: second }, nativeTheme(palette));
      assert(host.nodes.some(n => n.calls.some(c => c[0] === "child" && c[1] === quote)));
    }
  }
});

function realmFixture() {
  const state = {
    name: "hogwarts", dark: true, checking: false,
    spaces: [{ id: "one", active: true }, { id: "two", active: false }],
    realms: { one: "great-hall", two: "quidditch-pitch" },
    layout: { id: "root", background: { image: "old.png" }, children: [{ id: "sidebar", size: { px: 360 } }] },
    settingsFile: JSON.stringify({ zoom: 1.2, sounds: { enabled: false } }), commands: [], tasks: [],
  };
  const source = stripImports(read("mods/hogwarts-systems/main.js"))
    .replace(/^export function /gm, "function ").replace("export default class Spaces", "return class Spaces");
  const Spaces = new Function("host", `const { View, shared, setShared, spaces, layout, checking, settings, run, appHome, readTextFile, writeTextFile } = host;\n${realmsSource}\n${source}`)({
    View: class {}, spaces: () => state.spaces, layout: () => state.layout,
    checking: () => state.checking, settings: () => ({ dark: state.dark }),
    shared: key => key === "layout" ? state.name : state.realms,
    setShared: (_key, value) => state.realms = value,
    appHome: () => "/herdr-test", readTextFile: async () => state.settingsFile,
    writeTextFile: async (path, text, expected) => {
      assert.equal(path, "/herdr-test/settings.json");
      assert.equal(expected, state.settingsFile);
      state.settingsFile = text;
    },
    run: (command, args) => {
      state.commands.push([command, args]);
      if (command === "layout.set") state.layout = args.layout;
    },
  });
  return { state, view: new Spaces(), cx: { spawn(fn) { state.tasks.push(fn); } },
    async flush() { while (state.tasks.length) await state.tasks.shift()({ sleep: async () => {} }); } };
}

test("side commands change appearance and palette without dropping unrelated settings", async () => {
  const { state, view } = realmFixture();
  for (const side of ["light", "dark"]) {
    await view.setSide(side);
    assert.deepEqual(JSON.parse(state.settingsFile), { zoom: 1.2, sounds: { enabled: false }, appearance: side });
    assert.deepEqual(state.commands.at(-1), ["app.theme", { name: side === "light" ? "gryffindor" : "slytherin" }]);
  }
});

test("background updates are deferred, fresh, idempotent and limited to Hogwarts layout", async () => {
  const { state, view, cx, flush } = realmFixture();
  view.syncBackground(state.spaces, cx);
  view.syncBackground(state.spaces, cx);
  assert.equal(state.tasks.length, 1);
  state.spaces[0].active = false;
  state.spaces[1].active = true;
  state.dark = false;
  await flush();
  assert.equal(state.layout.background.image, "backgrounds/realms/gryffindor/quidditch-pitch.png");
  view.syncBackground(state.spaces, cx);
  await flush();
  assert.equal(state.commands.length, 1);
  state.layout.background.image = "custom.png";
  view.syncBackground(state.spaces, cx);
  state.name = "main";
  await flush();
  assert.equal(state.layout.background.image, "custom.png");
});
