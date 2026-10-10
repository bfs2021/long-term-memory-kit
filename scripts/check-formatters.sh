#!/usr/bin/env bash
# Proves Prettier and oxfmt leave Record frontmatter alone under the shipped overrides.
# Exit 0 = all checks pass, 1 = a check failed, 2 = broken setup (usage or missing binary).
# 2 stays apart from 1 so CI's --no-overrides step can't pass on a setup error.
set -u

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
overrides=1
for arg in "$@"; do
  case "$arg" in
    --no-overrides) overrides=0 ;;
    *) echo "usage: check-formatters.sh [--no-overrides]" >&2; exit 2 ;;
  esac
done

for tool in prettier oxfmt; do
  if [[ ! -x "$root/node_modules/.bin/$tool" ]]; then
    echo "missing $root/node_modules/.bin/$tool; run the package install first" >&2
    exit 2
  fi
done

# Temp copy per tool: oxfmt walks the whole working tree, untracked files included, so formatting in the repo would rewrite it.
tmps=()
trap 'rm -rf "${tmps[@]}"' EXIT

# Frontmatter only: first --- through the next ---. A whole-file diff would flag body reflow.
frontmatter() {
  awk '/^---$/ { n++; print; if (n == 2) exit; next } n == 1 { print }' "$1"
}

status=0

run_tool() {
  local tool="$1" tmp
  # pwd -P: macOS $TMPDIR is behind a /var -> /private/var symlink, and override globs miss when the tool sees the other spelling.
  tmp="$(cd "$(mktemp -d)" && pwd -P)"
  tmps+=("$tmp")
  cp -R "$root/fixtures/formatter/repo/." "$tmp/"
  mkdir -p "$tmp/_memory/decisions"
  cp "$root"/fixtures/formatter/before/*.md "$tmp/_memory/decisions/"

  # Pinned configs so a user's own config can't leak in; oxfmt has no --no-config, so it gets an empty one.
  local -a tool_args
  case "$tool" in
    prettier) tool_args=(--no-config --no-editorconfig) ;;
    oxfmt) echo '{}' > "$tmp/empty.json"; tool_args=(-c "$tmp/empty.json") ;;
  esac
  if (( overrides )); then
    case "$tool" in
      prettier)
        cp "$root/templates/formatters/prettierrc.json" "$tmp/.prettierrc.json"
        tool_args=(--config "$tmp/.prettierrc.json" --no-editorconfig) ;;
      oxfmt)
        cp "$root/templates/formatters/oxfmtrc.json" "$tmp/.oxfmtrc.json"
        tool_args=(-c "$tmp/.oxfmtrc.json") ;;
    esac
  fi

  # Run with cwd at the temp root so the _memory/** globs resolve against it.
  case "$tool" in
    prettier) (cd "$tmp" && "$root/node_modules/.bin/prettier" ${tool_args[@]+"${tool_args[@]}"} --write . >/dev/null) ;;
    oxfmt) (cd "$tmp" && "$root/node_modules/.bin/oxfmt" ${tool_args[@]+"${tool_args[@]}"} . >/dev/null) ;;
  esac
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "$tool exited $rc" >&2
    exit 2
  fi

  local f name
  for f in "$root"/fixtures/formatter/before/*.md; do
    name="$(basename "$f")"
    if ! cmp -s <(frontmatter "$f") <(frontmatter "$tmp/_memory/decisions/$name"); then
      echo "$tool: $name: frontmatter changed"
      status=1
    fi
  done

  # Override is scoped to _memory/**; if notes.md isn't reformatted, a tool that ignored everything would pass vacuously.
  if (( overrides )) && cmp -s <(frontmatter "$root/fixtures/formatter/repo/notes.md") <(frontmatter "$tmp/notes.md"); then
    echo "$tool: notes.md: frontmatter unchanged, so the run proves nothing about the override"
    status=1
  fi
}

for tool in prettier oxfmt; do
  run_tool "$tool"
done

# The guide quotes the shipped templates verbatim; this fails when either side is edited without the other.
guide=""
[[ -f "$root/guide/formatters.md" ]] && guide="$(<"$root/guide/formatters.md")"
for template in prettierrc.json oxfmtrc.json; do
  snippet="$(<"$root/templates/formatters/$template")"
  if [[ -z "$guide" || "$guide" != *"$snippet"* ]]; then
    echo "guide/formatters.md: missing templates/formatters/$template"
    status=1
  fi
done

exit "$status"
