#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 -m venv "$project_dir/.venv"
"$project_dir/.venv/bin/python" -m pip install -r "$project_dir/requirements.txt"
if ! command -v aplay >/dev/null; then
  echo 'aplay fehlt: bitte alsa-utils installieren.' >&2
  exit 1
fi
if ! command -v ffmpeg >/dev/null; then
  echo 'ffmpeg fehlt: bitte ffmpeg für die MP3-Dekodierung installieren.' >&2
  exit 1
fi
echo 'Bereit. Simulation: ./start-show.sh --simulate'
echo 'Echte Show: sudo ./start-show.sh --play'
echo 'Schnelldemo ohne Hardware: ./start-show.sh --demo'
