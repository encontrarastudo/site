#!/usr/bin/env bash
# Puxa o repositório e republica o site só quando há commit novo.
set -e
cd "$(dirname "$0")"
VENV=/opt/encontrarastudo-admin/venv/bin/python
WWW=/var/www/encontrarastudo
before=$(git rev-parse HEAD 2>/dev/null || echo none)
git pull --ff-only -q || exit 0
after=$(git rev-parse HEAD)
[ "$before" = "$after" ] && exit 0
echo "[deploy] mudanca detectada: $before -> $after"
cp -r assets/* "$WWW/assets/"
ET_OUT_DIR="$WWW" ET_DATA_DIR="$(pwd)/data" "$VENV" build_oracoes.py
cp index.html "$WWW/"
chmod -R a+rX "$WWW"
echo "[deploy] publicado em $(date)"
