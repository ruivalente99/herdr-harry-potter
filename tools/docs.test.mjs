// Local documentation and installer checks: node --test tools/docs.test.mjs
import assert from "node:assert/strict";
import { existsSync, readFileSync, mkdtempSync, mkdirSync, writeFileSync, rmSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = path => readFileSync(resolve(root, path), "utf8");
const readme = read("README.md");
const slug = value => value.toLowerCase().replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-");

function checkLink(target) {
  if (/^https?:\/\//.test(target)) return;
  const [path, anchor] = target.split("#");
  assert(!path || existsSync(resolve(root, path)), `Missing README asset or link: ${target}`);
  if (anchor) {
    const document = path ? read(path) : readme;
    const headings = [...document.matchAll(/^#{1,6} (.+)$/gm)].map(match => slug(match[1]));
    assert(headings.includes(anchor), `Missing README anchor: ${target}`);
  }
}

test("README navigation, images and local links resolve", () => {
  for (const match of readme.matchAll(/(?:src|href)="([^"]+)"/g)) checkLink(match[1]);
  for (const match of readme.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) checkLink(match[1]);
});

test("overview is a self-contained SVG with explicit illustration provenance", () => {
  const art = read("docs/images/overview.svg");
  assert.match(art, /viewBox="0 0 1440 760"/);
  assert.match(art, /Not a screenshot\./);
  assert.match(art, /GRYFFINDOR/);
  assert.match(art, /SLYTHERIN/);
  assert(!/<script|<foreignObject/.test(art));
  const ids = [...art.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, "Duplicate SVG IDs");
});

test("root recipe and preview exist without a duplicate share directory", () => {
  assert(read("RECIPE.md").includes("# Harry Potter for Herdr"));
  assert(read("RECIPE.md").includes("![Harry Potter for Herdr](preview.png)"));
  assert(existsSync(resolve(root, "preview.png")));
  assert(!existsSync(resolve(root, "share")));
});

test("installer works under both /bin/sh and /bin/bash and validates all seven mods", () => {
  for (const shell of ["/bin/sh", "/bin/bash"]) {
    const temp = mkdtempSync(join(tmpdir(), "herdr-hp-install-"));
    try {
      const bin = join(temp, "bin");
      const app = join(temp, "app");
      mkdirSync(bin);
      mkdirSync(join(app, "layouts"), { recursive: true });
      writeFileSync(join(app, "layouts", "doomsday.json"), "keep doomsday untouched");
      writeFileSync(join(bin, "herdr-app"), `#!/bin/sh
case "$1" in
  check) test -f "$2/main.js" && test -f "$2/mod.json" || exit 1 ;;
  do) test "$2" = layout.switch && test "$3" = --name && test "$4" = hogwarts && test -f "$HERDR_APP_HOME/layouts/hogwarts.json" || exit 1 ;;
  *) exit 1 ;;
esac
printf '%s %s\\n' "$1" "$2"
`, { mode: 0o755 });
      const result = spawnSync(shell, [resolve(root, "install.sh")], {
        cwd: root, encoding: "utf8",
        env: { HOME: temp, HERDR_APP_HOME: app, PATH: `${bin}:/usr/bin:/bin` },
      });
      assert.equal(result.status, 0, `${shell}: ${result.stderr}`);
      assert.equal(result.stdout.split("\n").filter(line => line.startsWith("check ")).length, 7);
      assert(result.stdout.trim().endsWith("Harry Potter layout installed and selected."));
      for (const mod of ["agents", "alerts", "status", "systems", "arena", "spell-run", "tabs"]) {
        assert(existsSync(join(app, "mods", `hogwarts-${mod}`, "main.js")), mod);
      }
      assert(existsSync(join(app, "themes/gryffindor.json")));
      assert(existsSync(join(app, "themes/slytherin.json")));
      assert(existsSync(join(app, "backgrounds/realms/slytherin/great-hall.png")));
      assert.equal(readFileSync(join(app, "layouts/doomsday.json"), "utf8"), "keep doomsday untouched");
    } finally {
      rmSync(temp, { recursive: true, force: true });
    }
  }
});
