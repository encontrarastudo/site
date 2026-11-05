#!/usr/bin/env bash
# Puxa o repo e republica o site quando há commit novo (ou com 'force').
set -e
cd "$(dirname "$0")"
WWW=/var/www/encontrarastudo
build(){
  cp -r assets/* "$WWW/assets/"
  ET_OUT_DIR="$WWW" ET_DATA_DIR="$(pwd)/data" python3 build_oracoes.py >/dev/null
  cp index.html "$WWW/"
  chmod -R a+rX "$WWW"
  echo "[deploy] publicado $(date -u +%FT%TZ)"
}
before=$(git rev-parse HEAD 2>/dev/null || echo none)
git pull --ff-only -q || true
after=$(git rev-parse HEAD 2>/dev/null || echo none)
if [ "$1" = "force" ] || [ "$before" != "$after" ] || [ ! -f "$WWW/index.html" ]; then build; else echo "[deploy] sem mudanca"; fi
