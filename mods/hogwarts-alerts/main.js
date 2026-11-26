import { View, div, image } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { props, closeOverlay, run, theme, shared, exec, window, appHome, checking } from "herdr";

// Shared character assignments from the Hogwarts Agents mod.
const CAST_KEY = "hogwarts-agents.cast";
const HERO_ICON_SIZE = 28;
const AGENT_TOAST = /^(.+) (finished|needs you)$/;
const QUEST = {
  finished: { pose: "done", line: "managed the mischief" },
  "needs you": { pose: "blocked", line: "sent an owl for help" },
};
const HERO_NAMES = {
  voldemort: "Lord Voldemort",
  harry: "Harry Potter",
  hermione: "Hermione Granger",
  ron: "Ron Weasley",
  dumbledore: "Albus Dumbledore",
  snape: "Severus Snape",
  hagrid: "Rubeus Hagrid",
  mcgonagall: "Prof. McGonagall",
  sirius: "Sirius Black",
  draco: "Draco Malfoy",
  luna: "Luna Lovegood",
  bellatrix: "Bellatrix Lestrange",
  dobby: "Dobby",
  hedwig: "Hedwig",
  dementor: "Dementor",
};
const HERO_LINES = {
  voldemort: {
    done: (name) => `${name} declares the dark enchantment complete`,
    blocked: (name) => `${name} summons you immediately`,
  },
  harry: {
    done: (name) => `${name} caught the Snitch — mischief managed`,
    blocked: (name) => `${name} needs backup at Hogwarts`,
  },
  hermione: {
    done: (name) => `${name} passed every test with an Outstanding`,
    blocked: (name) => `${name} found an edge case in the library`,
  },
  ron: {
    done: (name) => `${name} won the wizard's chess match`,
    blocked: (name) => `${name}'s wand backfired — needs a hand`,
  },
  dumbledore: {
    done: (name) => `${name} awards ten points to Gryffindor`,
    blocked: (name) => `${name} requests a word in the headmaster's office`,
  },
  snape: {
    done: (name) => `${name} brews a flawless potion... obviously`,
    blocked: (name) => `${name} demands your attention on page 394`,
  },
  hagrid: {
    done: (name) => `${name} tamed the task — shouldn't have said that`,
    blocked: (name) => `${name} needs a hand by the hut`,
  },
  mcgonagall: {
    done: (name) => `${name} completed the transfiguration neatly`,
    blocked: (name) => `${name} expects you in the classroom immediately`,
  },
  sirius: {
    done: (name) => `${name} cleared the task — Padfoot signing off`,
    blocked: (name) => `${name} calls for the Order of the Phoenix`,
  },
  draco: {
    done: (name) => `${name} finished — as expected of Slytherin`,
    blocked: (name) => `${name} warns his father will hear about this`,
  },
  luna: {
    done: (name) => `${name} cleared away the Wrackspurts`,
    blocked: (name) => `${name} spotted a Nargle blocking the path`,
  },
  bellatrix: {
    done: (name) => `${name} cackles — the hex is complete`,
    blocked: (name) => `${name} demands a duel right now`,
  },
  dobby: {
    done: (name) => `${name} finished the task — Dobby is a free elf!`,
    blocked: (name) => `${name} warns Harry Potter of danger`,
  },
  hedwig: {
    done: (name) => `${name} delivered the owl post safely`,
    blocked: (name) => `${name} is tapping urgently at the window`,
  },
  dementor: {
    done: (name) => `${name} glides away — sector quiet`,
    blocked: (name) => `${name} brings a sudden chill — cast Expecto Patronum`,
  },
};

const HERDR_BUNDLE = "dev.herdr.app";

function reportFailure(tool) {
  return (r) => { if (r.code !== 0) console.error(`System notification failed (${tool} ${r.code}): ${r.stderr}`); };
}

function postToMacos(title, body, image) {
  const picture = image ? ["-contentImage", `${appHome()}/${image}`] : [];
  exec("terminal-notifier", ["-title", title, "-message", body || " ", "-activate", HERDR_BUNDLE, ...picture]).then(
    reportFailure("terminal-notifier"),
    (e) => console.warn(`Native macOS banner unavailable: ${e}. In-app alerts remain available. Install terminal-notifier (brew install terminal-notifier) to enable system banners.`),
  );
}

function postToLinux(title, body, image) {
  const icon = image ? ["-i", `${appHome()}/${image}`] : [];
  exec("notify-send", ["-a", "Herdr", ...icon, title, body]).then(
    reportFailure("notify-send"),
    (e) => console.error(`System notification failed (is notify-send installed?): ${e}`),
  );
}

function postToSystem(platform, title, body, image) {
  if (platform === "macos") postToMacos(title, body, image);
  if (platform === "linux") postToLinux(title, body, image);
}

function heroOf(p) {
  const event = AGENT_TOAST.exec(p.title ?? "");
  const terminal = p.action?.name === "agent.focus" ? p.action.args?.terminal : null;
  const hero = terminal ? shared(CAST_KEY)?.[terminal] : null;
  if (!event || !hero || !HERO_NAMES[hero]) return null;
  const { pose, line } = QUEST[event[2]];
  const name = HERO_NAMES[hero];
  return {
    title: HERO_LINES[hero]?.[pose](name) ?? `${name} ${line}`,
    body: p.body ? `${event[1]} · ${p.body}` : event[1],
    icon: `mods/hogwarts-agents/sprites/hogwarts/${hero}.svg`,
    banner: null,
  };
}

const DOT = { error: "blocked", warning: "working", success: "done", info: "accent" };

export default class Toast extends View {
  init() {
    const w = window();
    if (checking() || !w || w.active) return;
    const raw = props() ?? {};
    const p = { ...raw, ...heroOf(raw) };
    postToSystem(w.platform, p.title ?? "Herdr", p.body ?? "", p.banner);
  }

  render(cx) {
    const t = theme();
    const raw = props() ?? {};
    const p = { ...raw, ...heroOf(raw) };
    const iconSize = p.icon === raw.icon ? 18 : HERO_ICON_SIZE;
    const login = /^([a-z0-9][a-z0-9_.-]{0,31}) needs login; run hc machine login \1$/.exec(p.body ?? "");
    const command = login ? `hc machine login ${login[1]}` : null;
    return h_flex()
      .id("toast")
      .size_full()
      .px(18)
      .gap(12)
      .items_center()
      .bg(t.popover)
      .cursor_pointer()
      .hover((s) => s.bg(t.hover))
      .on_click(() => {
        if (p.action?.name) run(p.action.name, p.action.args ?? {});
        closeOverlay(p.overlay);
      })
      .child(p.icon ? image(p.icon).w(iconSize).h(iconSize).flex_none() : div().size(8).rounded(4).flex_none().bg(t[DOT[p.level] ?? "accent"]))
      .child(
        v_flex()
          .flex_1()
          .overflow_hidden()
          .child(div().truncate().font_semibold().text_size(13).text_color(t.foreground).child(login ? `${login[1]} needs a login: run` : p.title ?? ""))
          .when(!login && Boolean(p.body), (el) => el.child(div().truncate().text_size(12).text_color(t.muted).child(p.body ?? "")))
          .when(Boolean(login), (el) => el.child(h_flex().gap(8).items_center()
            .child(div().flex_1().min_w(0).truncate().tooltip(command).text_size(12).text_color(t.muted).child(command))
            .child(div().id("toast-login-copy").flex_none().px(6).py(3).rounded(4).bg(t.raised)
              .text_size(12).text_color(t.foreground).cursor_pointer().hover(s => s.bg(t.hover))
              .on_click((_e, cx) => { cx.stop_propagation(); cx.write_to_clipboard(command); this.copied = true; cx.notify(); })
              .child(this.copied ? "Copied" : "Copy")))),
      );
  }
}
