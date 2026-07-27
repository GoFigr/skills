#!/usr/bin/env bash
#
# Package each skill as a zip for upload to surfaces that take skill archives
# rather than plugin marketplaces (claude.ai Settings > Capabilities, the
# Skills API, Claude Science).
#
# The archive root must be the skill folder itself, e.g. gofigr/SKILL.md — not
# the files at the top level of the zip.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_dir="$repo_root/plugins/gofigr/skills"
dist_dir="$repo_root/dist"

rm -rf "$dist_dir"
mkdir -p "$dist_dir"

for skill_path in "$skills_dir"/*/; do
  skill="$(basename "$skill_path")"

  if [[ ! -f "$skill_path/SKILL.md" ]]; then
    echo "skipping $skill: no SKILL.md" >&2
    continue
  fi

  ( cd "$skills_dir" && zip -qr "$dist_dir/$skill.zip" "$skill" -x '.*' -x '**/.*' )
  echo "built dist/$skill.zip"
  unzip -l "$dist_dir/$skill.zip" | sed 's/^/  /'
done
