#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$ROOT/build.sh"
java -jar "$ROOT/build/beelzebub-av.jar" --self-test
