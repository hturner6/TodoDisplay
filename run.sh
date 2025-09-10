#!usr/bin/env bash

# Runs the script in the background, refreshing every 30 mins
source .venv/bin/activate
pip install -r ./src/requirements.txt
python ./src/__main__.py --run 30
