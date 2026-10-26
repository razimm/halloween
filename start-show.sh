#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_path="$project_dir/.venv/bin/python"
audio_path="$project_dir/audio/electric-zap.wav"
if [[ ! -x "$python_path" ]]; then
  echo 'Zuerst ./setup.sh als normaler Benutzer ausführen.' >&2
  exit 1
fi
if [[ ! -f "$audio_path" ]]; then
  echo 'audio/electric-zap.wav fehlt. Einrichtung siehe docs/sound-sync.md.' >&2
  exit 1
fi
mode=(--play --audio-device 'plughw:CARD=Headset,DEV=0')
if [[ "${1:-}" == '--simulate' ]]; then
  shift
  mode=()
fi
exec "$python_path" "$project_dir/tools/sound_light.py" "$audio_path" "${mode[@]}" "$@"
