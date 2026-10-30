#!/usr/bin/env bash
# No output on success; preserve the complete log and exit code on failure.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$project_dir"
test_log="$(mktemp)"
trap 'rm -f -- "$test_log"' EXIT
if "$project_dir/.venv/bin/python" -m unittest discover -s tests -q "$@" >"$test_log" 2>&1; then
  exit 0
else
  test_status=$?
  cat -- "$test_log" >&2
  exit "$test_status"
fi
