#!/usr/bin/env bash
# Installs the Harry Potter (Hogwarts) layout and its seven custom mods into a Herdr app home.
set -eu

REPO="$(cd "$(dirname "$0")" && pwd)"
HERDR_HOME="${HERDR_APP_HOME:-$HOME/.config/herdr-app}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HERDR_HOME/backups/hogwarts-$STAMP"
MODS="hogwarts-agents hogwarts-alerts hogwarts-status hogwarts-systems hogwarts-arena hogwarts-spell-run hogwarts-tabs"

fail() { echo "install.sh: $*" >&2; exit 1; }
command -v herdr-app >/dev/null 2>&1 || fail "herdr-app is not on PATH. Install Herdr and try again."

backup_path() {
  relative="$1"
  target="$HERDR_HOME/$1"
  if [ -e "$target" ] || [ -L "$target" ]; then
    mkdir -p "$BACKUP/$(dirname "$relative")"
    mv "$target" "$BACKUP/$relative"
    echo "  backed up $relative to backups/hogwarts-$STAMP/"
  fi
}

install_file() {
  relative="$1"
  source="$REPO/$1"
  target="$HERDR_HOME/$1"
  [ -f "$source" ] || fail "missing project file: $relative"
  backup_path "$relative"
  mkdir -p "$(dirname "$target")"
  cp "$source" "$target"
}

replace_mod() {
  mod="$1"
  relative="mods/$1"
  target="$HERDR_HOME/mods/$1"
  [ -d "$REPO/$relative" ] || fail "missing project mod: $relative"
  backup_path "$relative"
  mkdir -p "$HERDR_HOME/mods"
  cp -R "$REPO/$relative" "$target"
}

mkdir -p "$HERDR_HOME"
echo "Installing Harry Potter for Herdr into $HERDR_HOME"

for file in layouts/hogwarts.json layouts/hogwarts.png themes/gryffindor.json themes/slytherin.json; do
  install_file "$file"
done

find "$REPO/backgrounds/realms" -type f ! -name .DS_Store -print | while IFS= read -r source; do
  relative="${source#"$REPO"/}"
  install_file "$relative"
done

for mod in $MODS; do
  replace_mod "$mod"
done

for mod in $MODS; do
  HERDR_APP_HOME="$HERDR_HOME" herdr-app check "$HERDR_HOME/mods/$mod" \
    || fail "mods/$mod failed Herdr validation; previous files are in the backup directory."
done

if HERDR_APP_HOME="$HERDR_HOME" herdr-app do layout.switch --name hogwarts; then
  echo "Harry Potter layout installed and selected."
else
  echo "Installed, but Herdr could not switch layouts. Select Hogwarts from the layout menu." >&2
fi
