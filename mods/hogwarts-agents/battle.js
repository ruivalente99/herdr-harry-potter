import { div, image } from "gpui-kit";
import { h_flex } from "gpui-base";
import { settings, shared, layout } from "herdr";

const SPRITE_DIR = "mods/hogwarts-agents/sprites/hogwarts";
const WEAPON_DIR = `${SPRITE_DIR}/weapons`;
export const SPRITE_SIZE = 36;
const DUEL_SPELLS = new Set(["expelliarmus", "petrificus", "serpensortia", "transfigure", "patronus", "sectumsempra"]);
const RANGED_SPELLS = new Set(["stupefy", "umbrella-spark", "radish-charm"]);
const WEAPONS = {
  voldemort: "dark-curse", harry: "expelliarmus", hermione: "petrificus", ron: "stupefy",
  dumbledore: "phoenix-fire", snape: "sectumsempra", hagrid: "umbrella-spark", mcgonagall: "transfigure",
  sirius: "patronus", draco: "serpensortia", luna: "radish-charm", bellatrix: "crucio",
  dobby: "elf-snap", hedwig: null, dementor: "soul-chill",
};
const NAMES = {
  voldemort: "Lord Voldemort", harry: "Harry Potter", hermione: "Hermione Granger", ron: "Ron Weasley",
  dumbledore: "Albus Dumbledore", snape: "Severus Snape", hagrid: "Rubeus Hagrid", mcgonagall: "Prof. McGonagall",
  sirius: "Sirius Black", draco: "Draco Malfoy", luna: "Luna Lovegood", bellatrix: "Bellatrix Lestrange",
  dobby: "Dobby", hedwig: "Hedwig", dementor: "Dementor",
};
const REALMS = new Set([
  "great-hall", "hogwarts-express", "gryffindor-tower", "slytherin-dungeon",
  "quidditch-pitch", "diagon-alley", "astronomy-tower",
]);
const CONVERSATIONS = [
  { pair: ["voldemort", "harry"], lines: [["voldemort", "The Boy Who Lived... come to debug."], ["harry", "Expelliarmus! And check the stack trace!"]] },
  { pair: ["harry", "draco"], lines: [["draco", "My father will hear about this merge conflict!"], ["harry", "Scared, Potter? No, just fixing your branch, Malfoy."]] },
  { pair: ["hermione", "ron"], lines: [["hermione", "It's Levi-O-sa, not Levio-SA!"], ["ron", "Honestly, you're a nightmare — pass the tests already."]] },
  { pair: ["dumbledore", "snape"], lines: [["dumbledore", "After all this time, Severus?"], ["snape", "Always. Now turn to page 394."]] },
  { pair: ["hagrid", "harry"], lines: [["hagrid", "Yer a wizard, Harry!"], ["harry", "I'm a what? Wait — why is the build on fire?"]] },
  { pair: ["sirius", "bellatrix"], lines: [["bellatrix", "Come on, cousin, you can do better than that!"], ["sirius", "Nice one, James — watch this counter-curse!"]] },
  { pair: ["mcgonagall", "snape"], lines: [["mcgonagall", "I've always wanted to use that spell."], ["snape", "Do try to leave the castle standing, Minerva."]] },
  { pair: ["dobby", "draco"], lines: [["dobby", "Dobby is a free elf!"], ["draco", "You'll pay for that, house-elf!"]] },
  { pair: ["luna", "harry"], lines: [["luna", "Don't worry, you're just as sane as I am."], ["harry", "Honestly, Luna, that actually helps."]] },
  { pair: ["harry", "hedwig"], lines: [["harry", "Deliver this patch note, Hedwig."], ["hedwig", "Hoot! (Already swooping to production.)"]] },
  { pair: ["hermione", "draco"], lines: [["draco", "Think you know every charm in the library?"], ["hermione", "I read Hogwarts: A History. Twice."]] },
  { pair: ["voldemort", "dumbledore"], lines: [["voldemort", "It was foolish to come here tonight, Tom."], ["dumbledore", "I am not worried, Tom. I am with the tests."]] },
  { pair: ["ron", "draco"], lines: [["ron", "Eat slugs, Malfoy!"], ["draco", "Watch where you wave that broken wand, Weasley!"]] },
  { pair: ["dobby", "harry"], lines: [["dobby", "Dobby has come to protect Harry Potter!"], ["harry", "Thanks, Dobby — just please don't seal the barrier again."]] },
];

export function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

export function heroSprite(hero, status, t) {
  const sprite = image(`${SPRITE_DIR}/${hero}.svg`).w(SPRITE_SIZE).h(SPRITE_SIZE).flex_none();
  if (status !== "blocked" && status !== "done") return sprite;

  const blocked = status === "blocked";
  const color = blocked ? t.blocked : t.done;
  return div().relative().w(SPRITE_SIZE).h(SPRITE_SIZE).flex_none().child(sprite)
    .child(div().absolute().left(0).top(0).size(13).rounded(4)
      .bg(t.popover).border(1).border_color(color)
      .flex().items_center().justify_center().text_size(10).font_bold()
      .text_color(color).child(blocked ? "!" : "✦"));
}

export function battleSquad(members, cast, page = 0, capacity = 4) {
  const eligible = members.filter(agent => Object.hasOwn(NAMES, cast[agent.address]));
  const pages = Math.max(1, Math.ceil(eligible.length / capacity));
  const current = ((page % pages) + pages) % pages;
  return { fighters: eligible.slice(current * capacity, (current + 1) * capacity), page: current, pages, total: eligible.length };
}

export function battleDialogue(fighters, cast, turn = 0) {
  const present = new Set(fighters.map(agent => cast[agent.address]));
  const lines = [];
  const blocked = fighters.find(agent => agent.status === "blocked");
  const done = fighters.find(agent => agent.status === "done");
  if (blocked) lines.push([cast[blocked.address], "Protego! I need backup at the castle!"]);
  else if (done) lines.push([cast[done.address], "Mischief managed. Spell complete!"]);
  lines.push(...CONVERSATIONS.filter(({ pair }) => pair.every(hero => present.has(hero))).flatMap(({ lines }) => lines));
  if (!lines.length && fighters.length) {
    lines.push([cast[fighters[0].address], "Wands at the ready. Next enchantment?"]);
    if (fighters[1]) lines.push([cast[fighters[1].address], "Lumos! Standing by at Hogwarts."]);
  }
  const [speaker, text] = lines[((turn % lines.length) + lines.length) % lines.length] ?? [];
  return { speaker, text };
}

function pulse(element, paused, property, from, to, period) {
  return paused || from === to ? element : element.loop(property, { from, to, period, easing: "ease-in-out" });
}

function miniFighter(agent, hero, x, facing, paused, hasTarget, t) {
  const active = hasTarget && (!agent.status || agent.status === "working");
  const weapon = WEAPONS[hero];
  const duel = DUEL_SPELLS.has(weapon);
  const period = duel ? 1520 : 1180;
  const direction = facing === "right" ? 1 : -1;
  const body = div().relative().left(0).top(0).w(28).h(28)
    .child(image(`${SPRITE_DIR}/${hero}.svg`).w(28).h(28));
  if (active && weapon) {
    const asset = `${weapon}-${facing}`;
    body.child(image(`${WEAPON_DIR}/${asset}.svg`).w(24).h(12).absolute().top(13)
      .left(facing === "right" ? 16 : -12));
    if (hero === "bellatrix") body.child(image(`${WEAPON_DIR}/${asset}.svg`).w(20).h(10)
      .absolute().top(20).left(facing === "right" ? 14 : -6));
  }
  const dx = !active ? 0 : duel ? direction * 5 : direction * -1;
  const dy = active && (hero === "dobby" || hero === "luna") ? -5 : active && hero === "dementor" ? -3 : agent.status === "done" ? -2 : 0;
  return div().id(`fight-${agent.address}`).absolute().left(x).top(4).w(28).h(28)
    .tooltip(`${NAMES[hero]} · ${agent.status ?? "working"}`)
    .child(pulse(pulse(body, paused, "left", 0, dx, period), paused, "top", 0, dy, period))
    .when(agent.status === "blocked" || agent.status === "done", el => el.child(div().absolute().right(-2).top(0)
      .text_size(9).font_bold().text_color(agent.status === "blocked" ? t.blocked : t.done)
      .child(agent.status === "blocked" ? "!" : "✦")));
}

function miniButton(id, text, t, action) {
  return div().id(id).px(5).h(19).rounded(3).flex().items_center().justify_center()
    .text_size(9).text_color(t.muted).cursor_pointer().role("button")
    .accessibility_label(text).hover(el => el.bg(t.hover)).on_click(action).child(text);
}

function speechTail(id, center, t) {
  const tail = div().id(id).absolute().left(center - 4).top(0).w(8).h(8);
  for (const [x, y, width, height, color] of [
    [3, 0, 2, 2, t.border], [2, 2, 4, 2, t.border], [1, 4, 6, 2, t.border], [0, 6, 8, 2, t.border],
    [3, 2, 2, 2, t.popover], [2, 4, 4, 2, t.popover], [1, 6, 6, 2, t.popover],
  ]) tail.child(div().absolute().left(x).top(y).w(width).h(height).bg(color));
  return tail;
}

export function battleScene(space, members, cast, t, options = {}) {
  const { paused = false, page = 0, turn = 0, onPause, onPage, onOpen } = options;
  const sidebarWidth = find(layout(), "sidebar")?.size?.px ?? 268;
  const columns = sidebarWidth >= 340 ? 2 : 1;
  const squad = battleSquad(members, cast, page, columns * 4);
  const fronts = Math.ceil(squad.fighters.length / 2);
  const rows = Math.ceil(fronts / columns);
  const width = Math.max(120, sidebarWidth - 46);
  const laneWidth = width / columns;
  const { speaker, text } = battleDialogue(squad.fighters, cast, turn);
  const realm = shared("hogwarts.realms")?.[space];
  const speakerIndex = Math.max(0, squad.fighters.findIndex(agent => cast[agent.address] === speaker));
  const speakerPair = Math.floor(speakerIndex / 2);
  const solo = speakerPair * 2 + 1 >= squad.fighters.length;
  const tailCenter = Math.max(12, Math.min(width - 12,
    1 + speakerPair % columns * laneWidth + laneWidth / 2 + (solo ? 0 : speakerIndex % 2 ? 28 : -28)));
  const height = 20 + rows * 36 + (text ? 42 : 0) + (onOpen ? 21 : 0);
  const stage = div().id(`fight-${space}`).relative().flex().flex_col().overflow_hidden()
    .h(height + 2).mx(5).my(3).flex_none().rounded(6).bg(t.raised).border(1).border_color(t.border);
  const field = div().id(`fight-field-${space}`).relative().h(20 + rows * 36).flex_none().overflow_hidden();
  if (REALMS.has(realm)) {
    stage.child(image(`backgrounds/realms/${settings().dark === false ? "gryffindor" : "slytherin"}/${realm}.png`)
      .absolute().left(0).top(0).w_full().h(Math.max(height, sidebarWidth * 9 / 16)).opacity(0.25));
  }
  field.child(div().absolute().left(6).right(6).top(4).text_size(8).font_semibold().text_color(t.dim)
    .child(`${paused ? "PAUSED" : "DUELING"} / ${fronts} FRONTS · ${squad.fighters.length}/${squad.total} WIZARDS`));
  for (let index = 0; index < fronts; index++) {
    const pair = squad.fighters.slice(index * 2, index * 2 + 2);
    const lane = div().id(`fight-${space}-front-${index}`).absolute()
      .left(6 + index % columns * laneWidth).top(20 + Math.floor(index / columns) * 36).w(laneWidth).h(36);
    pair.forEach((agent, slot) => {
      const x = pair.length === 1 ? laneWidth / 2 - 14 : laneWidth / 2 + (slot ? 14 : -42);
      lane.child(miniFighter(agent, cast[agent.address], x, slot ? "left" : "right", paused, pair.length === 2, t));
    });
    const attacking = pair.some(agent => (!agent.status || agent.status === "working") && WEAPONS[cast[agent.address]]);
    const ranged = pair.some(agent => (!agent.status || agent.status === "working")
      && RANGED_SPELLS.has(WEAPONS[cast[agent.address]]));
    if (pair.length === 2 && ranged) lane.child(pulse(div().absolute().left(laneWidth / 2 - 9).top(18)
      .w(18).h(2).bg(t.accent), paused, "opacity", 0.1, 0.9, 1180));
    if (pair.length === 2 && attacking) {
      lane.child(pulse(div().absolute().left(laneWidth / 2 - 3).top(15).size(7)
        .text_size(10).text_color(t.working).child("✦"), paused, "opacity", 0, 1, 1520));
    }
    field.child(lane);
  }
  stage.child(field);
  if (text) stage.child(div().id(`fight-comms-${space}`).relative().mx(5).mt(2).h(40).flex_none().overflow_hidden()
    .tooltip(`${NAMES[speaker]}: ${text}`).accessibility_label(`${NAMES[speaker]} says: ${text}`)
    .child(div().id(`fight-bubble-${space}`).absolute().left(0).right(0).top(6).h(34)
      .px(7).py(2).rounded(8).border(1).border_color(t.border).bg(t.popover)
      .child(div().text_size(8).font_semibold().text_color(t.accent).child(NAMES[speaker]))
      .child(div().text_size(10).text_color(t.foreground).truncate().child(text)))
    .child(speechTail(`fight-tail-${space}`, tailCenter, t)));
  if (onOpen) stage.child(h_flex().relative().mx(4).mt(1).h(20).flex_none().items_center().gap(2)
    .child(miniButton(`fight-pause-${space}`, paused ? "Resume" : "Pause", t, onPause))
    .when(squad.pages > 1, el => el.child(miniButton(`fight-squad-${space}`, `Squad ${squad.page + 1}/${squad.pages} ›`, t, onPage)))
    .child(div().flex_1())
    .child(miniButton(`fight-open-${space}`, "Expand ↗", t, () => onOpen(squad.fighters))));
  return stage;
}
