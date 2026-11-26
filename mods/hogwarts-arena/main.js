import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { closeOverlay, props, theme, spaces, shared, settings, checking, window } from "herdr";
import { arena } from "./scene.js";
import { HEROES, PRESETS, normalizeRoster, frontsFor, exchange } from "./choreography.js";

const REALM_NAMES = {
  "great-hall": "Great Hall",
  "hogwarts-express": "Hogwarts Express",
  "gryffindor-tower": "Gryffindor Tower",
  "slytherin-dungeon": "Slytherin Dungeon",
  "quidditch-pitch": "Quidditch Pitch",
  "diagon-alley": "Diagon Alley",
  "astronomy-tower": "Astronomy Tower",
};

function button(id, text, t, action, selected = false) {
  return div().id(id).h(28).px(10).flex_none().rounded(5).border(1)
    .border_color(selected ? t.accent : t.border).bg(selected ? t.selected : t.raised)
    .text_color(selected ? t.accent : t.foreground).text_size(11).font_medium()
    .flex().items_center().justify_center().cursor_pointer().role("button")
    .accessibility_label(text).hover(el => el.bg(t.hover)).on_click(action).child(text);
}

function bubbleTail(id, side, fill, border) {
  const tail = div().id(id).absolute().top(side === "left" ? 24 : 12).w(8).h(12)
    .when(side === "left", el => el.left(-7)).when(side === "right", el => el.right(-7));
  for (const [x, y, width, height, color] of [
    [0, 5, 2, 2, border], [2, 3, 2, 6, border], [4, 1, 2, 10, border], [6, 0, 2, 12, border],
    [3, 5, 2, 2, fill], [5, 3, 2, 6, fill], [7, 1, 1, 10, fill],
  ]) tail.child(div().absolute().left(side === "left" ? x : 8 - x - width).top(y).w(width).h(height).bg(color));
  return tail;
}

export default class Arena extends View {
  init(_props, cx) {
    const requested = normalizeRoster(props()?.fighters);
    this.scenario = requested.length >= 2 ? "custom" : "trio";
    this.custom = requested.length >= 2 ? requested : [...PRESETS.trio.heroes];
    this.paused = false;
    this.reducedMotion = false;
    this.speed = 1;
    this.turn = 0;
    this.clock = 0;
    this.focus = null;
    if (checking()) return;
    cx.timer.every(2100, cx => {
      if (this.paused || window()?.visible === false || this.roster().length < 2) return;
      this.clock += 2100 * this.speed;
      if (this.clock < 4200) return;
      this.clock = 0;
      this.turn++;
      cx.notify();
    });
  }

  roster() {
    return this.scenario === "custom" ? this.custom : PRESETS[this.scenario].heroes;
  }

  restart() {
    this.turn = 0;
    this.clock = 0;
    this.focus = null;
  }

  chooseScenario(id, cx) {
    if (id === "custom" && this.scenario !== "custom") this.custom = [...this.roster()];
    this.scenario = id;
    this.restart();
    cx.notify();
  }

  toggleHero(hero, cx) {
    if (this.custom.includes(hero)) this.custom = this.custom.filter(id => id !== hero);
    else if (this.custom.length < 8) this.custom = [...this.custom, hero];
    else return;
    this.restart();
    cx.notify();
  }

  render() {
    const t = theme();
    const dark = settings().dark !== false;
    const space = spaces().find(s => s.active);
    const assigned = shared("hogwarts.realms")?.[props()?.space ?? space?.id];
    const realm = Object.hasOwn(REALM_NAMES, assigned) ? assigned : null;
    const roster = this.roster();
    const fronts = frontsFor(roster);
    const channel = this.focus == null ? roster : fronts[this.focus] ?? roster;
    const line = exchange(channel, this.turn);
    const previous = this.turn > 0 ? exchange(channel, this.turn - 1) : null;
    const options = { roster, focus: this.focus, paused: this.paused, reducedMotion: this.reducedMotion, speed: this.speed };
    const heroes = Object.entries(HEROES);
    const chip = ([hero, profile]) => {
      const position = this.custom.indexOf(hero);
      const selected = position >= 0;
      return div().id(`arena-pick-${hero}`).w(76).h(32).flex_none().rounded(4).border(1)
        .border_color(selected ? t.accent : t.border).bg(selected ? t.selected : t.raised)
        .flex().items_center().gap(2).px(3).cursor_pointer().role("button")
        .accessibility_label(`${selected ? "Remove" : "Add"} ${profile.name}`)
        .tooltip(selected ? `${position + 1}. ${profile.name} · click to remove`
          : this.custom.length === 8 ? "Eight wizards selected. Remove one to make room." : `Add ${profile.name}`)
        .when(!selected && this.custom.length === 8, el => el.opacity(0.45))
        .hover(el => el.bg(t.hover)).on_click((_event, cx) => this.toggleHero(hero, cx))
        .child(image(`mods/hogwarts-agents/sprites/hogwarts/${hero}.svg`).w(24).h(24).flex_none())
        .child(div().min_w(0).truncate().text_size(9).text_color(selected ? t.accent : t.muted)
          .child(`${selected ? `${position + 1} ` : ""}${profile.name}`));
    };

    return v_flex().size_full().p(16).gap(10).rounded(8).bg(t.popover).text_color(t.foreground)
      .child(h_flex().h(42).flex_none().items_center().gap(12)
        .child(v_flex().flex_1().gap(3)
          .child(div().text_size(19).font_bold().child("Harry Potter · Dueling Club"))
          .child(div().text_size(11).text_color(t.dim).truncate()
            .child([REALM_NAMES[realm] ?? "Great Hall", "Cosmetic practice · no real agent actions"].join(" · "))))
        .child(div().px(9).py(4).rounded(4).text_size(10).font_semibold()
          .bg(t.raised).text_color(this.paused ? t.dim : t.done).child(this.paused ? "PAUSED" : "LIVE")))
      .child(v_flex().id("arena-content").flex_1().min_h(0).gap(10).overflow_y_scrollbar()
        .child(h_flex().h(30).flex_none().gap(5).items_center()
          .children([...Object.entries(PRESETS).map(([id, preset]) => button(`arena-mode-${id}`, preset.name, t,
            (_event, cx) => this.chooseScenario(id, cx), this.scenario === id)),
          button("arena-mode-custom", "Custom", t, (_event, cx) => this.chooseScenario("custom", cx), this.scenario === "custom")])
          .child(div().flex_1())
          .children([0.5, 1, 2].map(speed => button(`arena-speed-${speed}`, `${speed}×`, t, (_event, cx) => {
            this.speed = speed;
            this.clock = 0;
            cx.notify();
          }, this.speed === speed))))
        .when(this.scenario === "custom", el => el.child(v_flex().flex_none().gap(4)
          .child(div().text_size(10).text_color(t.dim)
            .child(`${this.custom.length}/8 wizards · pick 2–8 · selection order defines pairs · an odd wizard stays on standby`))
          .child(h_flex().gap(4).children(heroes.slice(0, 8).map(chip)))
          .child(h_flex().gap(4).children(heroes.slice(8).map(chip)))))
        .child(h_flex().justify_center().flex_none()
          .child(arena(options, realm, t, dark, REALM_NAMES, (index, cx) => {
            this.focus = this.focus === index ? null : index;
            this.turn = 0;
            this.clock = 0;
            cx.notify();
          })))
        .child(v_flex().id("arena-comms").h(previous ? 110 : 64).flex_none().px(3).gap(6)
          .when(Boolean(line), el => el.child(h_flex().h(64).flex_none().items_center().gap(12)
            .child(image(`mods/hogwarts-agents/sprites/hogwarts/${line.speaker}.svg`).w(36).h(36).flex_none())
            .child(v_flex().id("arena-speech-current").relative().h(60).flex_1().min_w(0).justify_center()
              .px(12).py(6).gap(3).rounded(10).border(1).border_color(t.border).bg(t.surface)
              .accessibility_label(`${HEROES[line.speaker].name} says: ${line.text}`)
              .child(div().text_size(9).font_semibold().text_color(t.accent)
                .child(`${HEROES[line.speaker].name} · ${this.focus == null ? "Club" : `Duel ${this.focus + 1}`}`))
              .child(div().text_size(12).text_color(t.foreground).truncate().tooltip(line.text).child(line.text))
              .child(bubbleTail("arena-tail-current", "left", t.surface, t.border)))))
          .when(Boolean(previous), el => el.child(h_flex().h(40).flex_none().pl(48).items_center().gap(12)
            .child(v_flex().id("arena-speech-previous").relative().h(36).flex_1().min_w(0)
              .px(10).py(3).gap(1).rounded(9).border(1).border_color(t.border).bg(t.raised)
              .accessibility_label(`Previously, ${HEROES[previous.speaker].name} said: ${previous.text}`)
              .child(div().text_size(8).font_semibold().text_color(t.dim).child(`${HEROES[previous.speaker].name} · Previously`))
              .child(div().text_size(10).text_color(t.muted).truncate().tooltip(previous.text).child(previous.text))
              .child(bubbleTail("arena-tail-previous", "right", t.raised, t.border)))
            .child(image(`mods/hogwarts-agents/sprites/hogwarts/${previous.speaker}.svg`).w(28).h(28).flex_none())))
          .when(!line, el => el.child(div().text_size(11).text_color(t.muted).child("Select your wizards to open a duel.")))))
      .child(h_flex().h(30).flex_none().gap(5).items_center()
        .child(div().flex_1().text_size(10).text_color(t.dim)
          .child(`${roster.length} wizards · ${fronts.length} duels · Esc to close`))
        .child(button("arena-motion", this.reducedMotion ? "Motion: reduced" : "Motion: full", t, (_event, cx) => {
          this.reducedMotion = !this.reducedMotion;
          cx.notify();
        }))
        .child(button("arena-next", "Next line", t, (_event, cx) => {
          this.turn++;
          this.clock = 0;
          cx.notify();
        }))
        .child(button("arena-restart", "Replay", t, (_event, cx) => {
          this.restart();
          cx.notify();
        }))
        .child(button("arena-pause", this.paused ? "Resume" : "Pause", t, (_event, cx) => {
          this.paused = !this.paused;
          this.clock = 0;
          cx.notify();
        }))
        .child(button("arena-close", "Close", t, () => closeOverlay(props().overlay))));
  }
}
