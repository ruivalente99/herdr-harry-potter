// Pure training data: no host calls, real agent commands or random render-time state.
// Harry Potter & Wizarding World cast for the Dueling Club.
export const DUEL_SPELLS = new Set(["expelliarmus", "petrificus", "serpensortia", "transfigure", "patronus", "sectumsempra"]);
export const DARK_SPELLS = new Set(["dark-curse", "phoenix-fire", "crucio", "elf-snap", "soul-chill"]);

export const HEROES = {
  harry: { name: "Harry Potter", weapon: "expelliarmus", style: "duelist", line: "Expelliarmus! Ready when you are." },
  voldemort: { name: "Lord Voldemort", weapon: "dark-curse", style: "heavy", line: "There is no good and evil, only power — and passing tests." },
  hermione: { name: "Hermione", weapon: "petrificus", style: "duelist", line: "I've memorized every counter-curse in the library." },
  ron: { name: "Ron Weasley", weapon: "stupefy", style: "shooter", line: "Bloody hell — alright, let's do this." },
  dumbledore: { name: "Dumbledore", weapon: "phoenix-fire", style: "heavy", line: "Happiness can be found even in the darkest stack trace." },
  snape: { name: "Snape", weapon: "sectumsempra", style: "duelist", line: "Turn to page 394. Show me your guard." },
  hagrid: { name: "Hagrid", weapon: "umbrella-spark", style: "heavy", line: "I shouldn't have cast that. I should NOT have cast that." },
  mcgonagall: { name: "McGonagall", weapon: "transfigure", style: "duelist", line: "Wands ready. Maintain proper dueling posture!" },
  sirius: { name: "Sirius Black", weapon: "patronus", style: "duelist", line: "Expecto Patronum! Let's make this quick." },
  draco: { name: "Draco Malfoy", weapon: "serpensortia", style: "duelist", line: "Scared, Potter? You wish." },
  luna: { name: "Luna Lovegood", weapon: "radish-charm", style: "acrobat", line: "Your head is full of Wrackspurts — hold still!" },
  bellatrix: { name: "Bellatrix", weapon: "crucio", style: "dual", line: "Itty bitty baby wizard — show me what you've got!" },
  dobby: { name: "Dobby", weapon: "elf-snap", style: "acrobat", line: "Dobby never meant to kill — only maim or seriously refactor!" },
  hedwig: { name: "Hedwig", weapon: null, style: "support", line: "Hoot! (Watching calmly from the owlery perch.)" },
  dementor: { name: "Dementor", weapon: "soul-chill", style: "force", line: "*A sudden frost sweeps across the Dueling Club.*" },
};

export const PRESETS = {
  trio: { name: "Golden Trio", heroes: ["harry", "voldemort", "hermione", "bellatrix", "ron", "draco", "dumbledore", "snape"] },
  hogwarts: { name: "Hogwarts", heroes: ["harry", "voldemort", "mcgonagall", "snape", "hagrid", "dementor"] },
  order: { name: "Order", heroes: ["sirius", "bellatrix", "dumbledore", "voldemort", "luna", "dementor"] },
  allies: { name: "Allies", heroes: ["harry", "hedwig", "dobby", "draco", "luna", "hermione", "ron", "hagrid"] },
};

const CONVERSATIONS = [
  { pair: ["voldemort", "harry"], lines: [["voldemort", "The Boy Who Lived... come to debug."], ["harry", "Expelliarmus! And check the stack trace!"], ["voldemort", "Avada Kedavra!"]] },
  { pair: ["harry", "draco"], lines: [["draco", "My father will hear about this merge conflict!"], ["harry", "Scared, Potter? No, just fixing your branch, Malfoy."], ["draco", "Serpensortia!"]] },
  { pair: ["hermione", "ron"], lines: [["hermione", "It's Levi-O-sa, not Levio-SA!"], ["ron", "Honestly, you're a nightmare — pass the tests already."], ["hermione", "At least someone read Hogwarts: A History."]] },
  { pair: ["dumbledore", "snape"], lines: [["dumbledore", "After all this time, Severus?"], ["snape", "Always. Now turn to page 394."], ["dumbledore", "Ten points to Slytherin for punctuality."]] },
  { pair: ["hagrid", "harry"], lines: [["hagrid", "Yer a wizard, Harry!"], ["harry", "I'm a what? Wait — why is the build on fire?"], ["hagrid", "Shouldn't have said that."]] },
  { pair: ["sirius", "bellatrix"], lines: [["bellatrix", "Come on, cousin, you can do better than that!"], ["sirius", "Nice one, James — watch this counter-curse!"], ["bellatrix", "Crucio!"]] },
  { pair: ["mcgonagall", "snape"], lines: [["mcgonagall", "I've always wanted to use that spell."], ["snape", "Do try to leave the castle standing, Minerva."]] },
  { pair: ["dobby", "draco"], lines: [["dobby", "Dobby is a free elf!"], ["draco", "You'll pay for that, house-elf!"], ["dobby", "Master has given Dobby a clean deploy!"]] },
  { pair: ["luna", "harry"], lines: [["luna", "Don't worry, you're just as sane as I am."], ["harry", "Honestly, Luna, that actually helps."]] },
  { pair: ["harry", "hedwig"], lines: [["harry", "Deliver this patch note, Hedwig."], ["hedwig", "Hoot! (Already swooping to production.)"]] },
  { pair: ["hermione", "draco"], lines: [["draco", "Think you know every charm in the library?"], ["hermione", "I read Hogwarts: A History. Twice."]] },
  { pair: ["voldemort", "dumbledore"], lines: [["voldemort", "It was foolish to come here tonight, Tom."], ["dumbledore", "I am not worried, Tom. I am with the tests."]] },
  { pair: ["ron", "draco"], lines: [["ron", "Eat slugs, Malfoy!"], ["draco", "Watch where you wave that broken wand, Weasley!"]] },
  { pair: ["dobby", "harry"], lines: [["dobby", "Dobby has come to protect Harry Potter!"], ["harry", "Thanks, Dobby — just please don't seal the barrier again."]] },
  { pair: ["sirius", "dementor"], lines: [["sirius", "Expecto Patronum! Back to Azkaban!"], ["dementor", "*Retreats behind a silver stag of light.*"]] },
  { pair: ["hagrid", "dementor"], lines: [["hagrid", "Clear off! No Dementors near my pumpkins!"], ["dementor", "*Shudders at the pink umbrella.*"]] },
];

export function normalizeRoster(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  return value.filter(hero => {
    if (typeof hero !== "string" || !Object.hasOwn(HEROES, hero)) return false;
    if (seen.has(hero) && hero !== "dementor") return false;
    seen.add(hero);
    return true;
  }).slice(0, 8);
}

export function frontsFor(roster) {
  const heroes = normalizeRoster(roster);
  return Array.from({ length: Math.ceil(heroes.length / 2) }, (_, index) => heroes.slice(index * 2, index * 2 + 2));
}

export function dialogueLines(roster) {
  const heroes = normalizeRoster(roster);
  const present = new Set(heroes);
  const lines = CONVERSATIONS.filter(({ pair }) => pair.every(hero => present.has(hero)))
    .flatMap(({ pair, lines }) => lines.map(([speaker, text]) => ({ speaker, text, pair })));
  return lines.length ? lines : heroes.map(speaker => ({ speaker, text: HEROES[speaker].line, pair: heroes.slice(0, 2) }));
}

export function exchange(roster, turn = 0) {
  const lines = dialogueLines(roster);
  return lines.length ? lines[((turn % lines.length) + lines.length) % lines.length] : null;
}

export function frontStyle(pair) {
  if (pair.length < 2) return "STANDBY";
  const weapons = pair.map(hero => HEROES[hero].weapon);
  if (weapons.includes(null)) return "OWL POST / SUPPORT";
  if (weapons.every(weapon => DUEL_SPELLS.has(weapon))) return "WAND DUEL";
  if (weapons.some(weapon => DARK_SPELLS.has(weapon))) return "DARK ARTS / CHARMS";
  if (weapons.some(weapon => DUEL_SPELLS.has(weapon))) return "COUNTER-CURSE";
  return "SPELL BARRAGE";
}
