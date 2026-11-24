#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BUILD="$ROOT/build"
CLASSES="$BUILD/classes"
if [ -L "$BUILD" ] || [ -L "$CLASSES" ] || [ -L "$BUILD/beelzebub-av.jar" ] || [ -L "$BUILD/sources.list" ]; then
  echo "Refusing to build through a symbolic link." >&2
  exit 1
fi
rm -rf "$CLASSES"
mkdir -p "$CLASSES"
find "$ROOT/src/main/java" -name '*.java' -print > "$BUILD/sources.list"
javac --release 17 -encoding UTF-8 -d "$CLASSES" @"$BUILD/sources.list"
if [ -d "$ROOT/src/main/resources" ]; then cp -R "$ROOT/src/main/resources/." "$CLASSES/"; fi
jar --create --file "$BUILD/beelzebub-av.jar" --main-class ai.duckos.beelzebub.Main -C "$CLASSES" .
printf 'Built %s\n' "$BUILD/beelzebub-av.jar"
