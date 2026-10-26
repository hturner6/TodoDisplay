#!/bin/bash

# Forces an immediate screen refresh on the Pi. The TodoDisplay service holds the display's GPIO,
# so it is stopped while drawing and always started again afterwards.
# Usage: ./refresh.sh [--clear]   (--clear wipes the screen first, to remove ghosting)
cd "$(dirname "$0")" || exit 1

sudo systemctl stop TodoDisplay
trap 'sudo systemctl start TodoDisplay' EXIT

if [ "$1" = "--clear" ]; then
    .venv/bin/python ./src/__main__.py --clear
fi
.venv/bin/python ./src/__main__.py --task
