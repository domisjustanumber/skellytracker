#!/bin/sh
# Measure the graphify build of this repository (decision 87B2).
#
# Usage:
#
#     sh decisions/scripts/graphify_build_timing.sh DIR
#
# The script clones the repository of the current folder into the new folder DIR. In that clone it
# times a full build, a build with no change and a cached uvx start. It counts the files that the
# graph reads, by extension. It runs tools/check_private_data.py while graphify-out/ exists. Then it
# stops a forced build after 3 s, lists the graphify Python processes that stay (Windows only), and
# times the next build, which must not wait on the lock of the stopped build.
# It changes nothing in the repository of the current folder. Delete DIR afterwards.
set -eu
dir=$1
src=$(git rev-parse --show-toplevel)
G="uvx --from graphifyy==0.9.100 graphify"
export UV_NO_PROGRESS=1 GRAPHIFY_BACKEND=none GRAPHIFY_NO_TIPS=1

git clone -q "$src" "$dir"
cd "$dir"
echo graphify-out/ >> "$(git rev-parse --git-path info/exclude)"
echo "== versions"; uv --version; git --version; $G --version 2>/dev/null || true
echo "== cached uvx start"; time $G --help >/dev/null
echo "== full build"; time $G update . >/dev/null
echo "== build with no change"; time $G update . >/dev/null
echo "== size"; du -sh graphify-out
echo "== files by extension"
uv run --no-project python -c "import collections, json, os; m = json.load(open('graphify-out/manifest.json', encoding='utf-8')); print(collections.Counter(os.path.splitext(f)[1] for f in m).most_common())"
echo "== private data"; uv run --project "$src" --no-sync python tools/check_private_data.py
echo "== stopped build"
rm -rf graphify-out/cache
timeout 3 $G update . --force >/dev/null 2>&1 || echo "rc=$?"
if command -v powershell >/dev/null 2>&1; then
  powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -match 'graphify' } | Measure-Object | ForEach-Object { 'graphify python processes left: ' + \$_.Count }"
fi
echo "== next build after the stop"; time timeout 120 $G update . --force >/dev/null
