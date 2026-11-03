#!/bin/sh
# graphify-local: refresh graphify-out/ of this checkout. AST only, no LLM, background. Always exits 0.
# tools/graphify_hooks.py installs this file as post-commit, post-checkout, post-merge and
# post-rewrite (decision 87B2). The copy runs from the hooks folder and must not read tools/:
# some branches do not have it.
PIN=graphifyy==0.9.100
[ "$GRAPHIFY_SKIP_HOOK" = 1 ] && exit 0
command -v uvx >/dev/null 2>&1 || exit 0
top=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$top" || exit 0
# Opt-in for each checkout: a temporary worktree never builds, so its removal is never blocked.
[ -d graphify-out ] || exit 0
hook=${0##*/}; hook=${hook##*\\}; hook=${hook%.legacy}  # pre-commit migration mode renames a hook to *.legacy
case $hook in
  post-checkout) [ "$3" = 1 ] && [ "$1" != "$2" ] || exit 0 ;;  # only when HEAD moves
  post-rewrite)  [ "$1" = rebase ] || exit 0 ;;                # an amend already ran post-commit
esac
if [ "$hook" = post-commit ]; then
  # A rebase fires post-commit for each picked commit; post-rewrite or post-checkout covers it.
  # shortcut: a multi-commit cherry-pick or revert gets no rebuild; the next trigger catches up.
  for d in rebase-merge rebase-apply sequencer; do
    [ -d "$(git rev-parse --git-path "$d")" ] && exit 0
  done
fi
log="$HOME/.cache/graphify-rebuild.log"; mkdir -p "${log%/*}"
echo "$(date '+%F %T') start $hook $(git rev-parse --short HEAD) $top" >> "$log"
# macOS has no timeout; Homebrew coreutils has gtimeout. With neither, the build has no limit.
limit=$(command -v timeout || command -v gtimeout)
# shortcut: a later run waits on the graphify lock, so quick commits rebuild one after another.
# A git command that runs under `uv run` passes its Python variables; uvx must not read them.
unset PYTHONHOME PYTHONPATH VIRTUAL_ENV UV_INTERNAL__PYTHONHOME UV_RUN_RECURSION_DEPTH
( { GRAPHIFY_BACKEND=none GRAPHIFY_MAX_WORKERS=1 GRAPHIFY_NO_TIPS=1 PYTHONHASHSEED=0 UV_NO_PROGRESS=1 \
      ${limit:+"$limit" 900} uvx --from "$PIN" graphify update . --force
    echo "$(date '+%F %T') done rc=$? $hook $top"; } </dev/null >>"$log" 2>&1 & )
exit 0
