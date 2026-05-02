#!/usr/bin/env bash
set -e
# Activate virtualenv if present, then run the app
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi
python src/main.py
