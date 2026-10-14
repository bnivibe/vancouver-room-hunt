#!/bin/sh
# Installs the pre-commit, commit-msg and pre-push hooks that run the privacy guard.
# Hooks go where git looks for them: a linked worktree shares the main repo's hooks, and
# core.hooksPath is honored. An existing hook that is not this guard is never replaced.
set -e
hooks="$(git rev-parse --path-format=absolute --git-path hooks)"
mkdir -p "$hooks"

install_hook() {
  target="$hooks/$1"
  if [ -e "$target" ] && ! grep -q "guard/check_public.py" "$target"; then
    echo "refusing to replace an existing $1 hook: $target" >&2
    exit 1
  fi
  printf '#!/bin/sh\n%s\n' "$2" > "$target"
  chmod +x "$target"
  echo "$1 hook installed: $target"
}

# pre-commit scans the staged changes, commit-msg the message, and pre-push every outgoing
# commit: the last local point before anything is public.
install_hook pre-commit 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --staged'
install_hook commit-msg 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --message "$1"'
install_hook pre-push 'exec python3 "$(git rev-parse --show-toplevel)/guard/check_public.py" --pre-push'
