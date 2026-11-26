// Realm IDs are shared with the Wizarding location emblems and generated background filenames.
export const REALMS = [
  "great-hall", "hogwarts-express", "gryffindor-tower", "slytherin-dungeon",
  "quidditch-pitch", "diagon-alley", "astronomy-tower",
];
export const REALM_NAMES = {
  "great-hall": "Great Hall",
  "hogwarts-express": "Hogwarts Express",
  "gryffindor-tower": "Gryffindor Tower",
  "slytherin-dungeon": "Slytherin Dungeon",
  "quidditch-pitch": "Quidditch Pitch",
  "diagon-alley": "Diagon Alley",
  "astronomy-tower": "Astronomy Tower",
};

export function realmBackground(realm, dark = true) {
  return REALMS.includes(realm)
    ? { image: `backgrounds/realms/${dark ? "slytherin" : "gryffindor"}/${realm}.png`, fit: "cover" }
    : null;
}
