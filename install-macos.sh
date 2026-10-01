#!/bin/sh
set -eu
MAGIK_SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$MAGIK_SOURCE/macos/install.py" "$@"
