#!/usr/bin/env bash
# Puxa o repo e republica o site quando há commit novo (ou com 'force').
set -e
cd "$(dirname "$0")"
WWW=/var/www/encontrarastudo
build(){
  # index.html é GERADO por build_pages.py (home dinâmica: recomendados +
  # carrossel de destaques a partir de data/artigos.json). Não copiar o
  # index.html do repositório — ele é apenas o template de entrada do build.
  cp -r assets/* "$WWW/assets/"
  ET_OUT_DIR="$WWW" ET_DATA_DIR="$(pwd)/data" python3 build_pages.py >/dev/null
  ET_OUT_DIR="$WWW" ET_DATA_DIR="$(pwd)/data" python3 build_oracoes.py >/dev/null
  chmod -R a+rX "$WWW"
  echo "[deploy] publicado $(date -u +%FT%TZ)"
}
before=$(git rev-parse HEAD 2>/dev/null || echo none)
git pull --ff-only -q || true
after=$(git rev-parse HEAD 2>/dev/null || echo none)
if [ "$1" = "force" ] || [ "$before" != "$after" ] || [ ! -f "$WWW/index.html" ]; then build; else echo "[deploy] sem mudanca"; fi

# Disparo automático de newsletters enfileiradas (newsletter/queue/*.json).
# Usa as credenciais do Listmonk em /opt/newsletter.env (fora do repositório).
# Idempotente: dispatch.py só envia o que ainda não foi enviado (.sent.log).
if [ -f /opt/newsletter.env ]; then
  ( set -a; . /opt/newsletter.env; set +a
    python3 newsletter/dispatch.py ) >> /var/log/et-newsletter.log 2>&1 || true

  # Relatório de métricas (entrega/abertura/clique) dos últimos 7 dias.
  # Grava um JSON num caminho não-adivinhável servido pelo site; a tarefa
  # semanal lê esse JSON e manda o resumo pro Gustavo. report.py só regenera
  # se o arquivo tiver mais de 6h (não martela a API do Listmonk a cada tick).
  ( set -a; . /opt/newsletter.env; set +a
    python3 newsletter/report.py \
      --out "$WWW/_stats/rel-5a5dd2846e1658b1a020e839.json" --days 7
  ) >> /var/log/et-newsletter.log 2>&1 || true
  [ -d "$WWW/_stats" ] && chmod -R a+rX "$WWW/_stats" 2>/dev/null || true
fi
