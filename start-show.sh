#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_path="$project_dir/.venv/bin/python"
if [[ ! -x "$python_path" ]]; then
  echo 'Zuerst ./setup.sh als normaler Benutzer ausführen.' >&2
  exit 1
fi
cd -- "$project_dir"
exec "$python_path" -u -m tools.show "$@"
