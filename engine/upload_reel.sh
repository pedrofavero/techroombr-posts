#!/usr/bin/env bash
# Publica posts/<slug>/reel.mp4 como asset da release "reels" sem inflar o repositório:
# empurra o arquivo para o branch órfão "reels-inbox" (sempre um único commit) e a Action
# "reels" sobe o arquivo para a release. Uso: engine/upload_reel.sh <slug> [<slug2> ...]
set -euo pipefail
repo="pedrofavero/techroombr-posts"; here=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d); cd "$tmp"; git init -q -b reels-inbox
git config user.name "Claude"; git config user.email "noreply@anthropic.com"
for slug in "$@"; do cp "$here/posts/$slug/reel.mp4" "$slug.mp4"; cp "$here/posts/$slug/reel_cover.jpg" "$slug.jpg"; done
git add . && git commit -qm "reels: $*" && git push -q -f "https://github.com/$repo" reels-inbox
cd "$here"; rm -rf "$tmp"
for slug in "$@"; do
  url="https://github.com/$repo/releases/download/reels/$slug.mp4"
  for i in $(seq 1 24); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -L -r 0-100 "$url" || true)
    [ "$code" = "206" ] || [ "$code" = "200" ] && break; sleep 15
  done
  echo "$url ($code)"
done
