# Architecture

This project is a standalone Harry Potter layout for Herdr using the `hogwarts-*` mod namespace so it installs cleanly alongside other community layouts. All assets are generated locally with Python's standard library; no runtime network requests are made.

## Layout & Modules

- **`layouts/hogwarts.json`** — Composes the workspace with `gryffindor` (light) and `slytherin` (dark) themes.
- **`hogwarts-systems`** — Spaces list with 7 stable Wizarding World locations (`hogwarts.realms`), Git status, and appearance commands (`hogwarts-systems.light` / `hogwarts-systems.dark`).
- **`hogwarts-agents`** — Agent cards with 15 unique Harry Potter characters (`hogwarts-agents.cast`, only Dementors repeat, Voldemort joins on dark mode), terminal model/context parsing, and per-space mini duels.
- **`hogwarts-alerts`** — Character-aware owl-post in-app alerts and safe macOS (`terminal-notifier`) / Linux (`notify-send`) banners.
- **`hogwarts-status`** — Footer status counts and app dock badge.
- **`hogwarts-arena`** — Dueling Club overlay (`choreography.js`, `scene.js`, `main.js`) with up to 4 simultaneous spell fronts.
- **`hogwarts-tabs`** — Top tab bar with the **Spell Run** panel button and `hogwarts-tabs.toggle-spell-run` command (`hogwarts.spell-run`).
- **`hogwarts-spell-run`** — Bomberman-style arcade game (`decks.js`, `game.js`, `scene.js`, `ui.js`, `main.js`) across 8 Hogwarts rooms with 60 four-direction walking atlases and per-agent persistence (`wizard-progress`, `thinking-only`).

## Shared Engine (`herdr-common`)

All seven mod engines, `layouts/hogwarts.json`, `install.sh`, and the regression test suite are maintained centrally in the sibling [`herdr-common`](../herdr-common) library and synced from [`pack.config.mjs`](../pack.config.mjs). Edit labels, wizards, spells, quotes, realms, or Spell Run rooms in `pack.config.mjs`, then run:

```sh
npm run sync
```

## Verification

```sh
node --test tools/*.test.mjs
npm run check:sync
for m in mods/hogwarts-*; do herdr-app check "$m"; done
```
