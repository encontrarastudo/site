#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatório de métricas das newsletters (Listmonk).

Roda NO SERVIDOR (onde estão as credenciais em /opt/newsletter.env), puxa as
campanhas dos últimos N dias via API do Listmonk e grava um JSON de resumo
(entrega, abertura, clique) num caminho servido pelo site. Uma tarefa semanal
lê esse JSON e manda o resumo pro Gustavo — assim o token nunca sai do servidor.

Uso:
  python3 newsletter/report.py --out /var/www/encontrarastudo/_stats/rel-<token>.json
Opções:
  --days N        janela em dias (padrão 7)
  --max-age-min M só regenera se o arquivo tiver mais de M minutos (padrão 360)
"""
import os, sys, json, argparse, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lm  # reaproveita req() e as credenciais do ambiente


def parse_dt(s):
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=datetime.timezone.utc)
        except Exception:
            return None


def pct(num, den):
    return round(100.0 * num / den, 1) if den else 0.0


def coletar(days):
    res = lm.req("GET", "/api/campaigns?page=1&per_page=100&order_by=created_at&order=DESC")
    data = res.get("data", res)
    camps = data.get("results") if isinstance(data, dict) else data
    camps = camps or []
    agora = datetime.datetime.now(datetime.timezone.utc)
    corte = agora - datetime.timedelta(days=days)
    linhas = []
    for c in camps:
        quando = parse_dt(c.get("started_at")) or parse_dt(c.get("created_at"))
        if quando and quando < corte:
            continue
        # só campanhas que de fato saíram
        if c.get("status") not in ("finished", "running", "cancelled"):
            continue
        sent = int(c.get("sent") or 0)
        if sent <= 0:
            continue
        views = int(c.get("views") or 0)      # aberturas (total, não únicas)
        clicks = int(c.get("clicks") or 0)
        bounces = int(c.get("bounces") or 0)  # presente só se o SES reporta bounces ao Listmonk
        entregues = max(sent - bounces, 0)
        linhas.append({
            "nome": c.get("name", ""),
            "assunto": c.get("subject", ""),
            "data": (quando.date().isoformat() if quando else ""),
            "enviados": sent,
            "entregues": entregues,
            "bounces": bounces,
            "aberturas": views,
            "cliques": clicks,
            "taxa_entrega": pct(entregues, sent),
            "taxa_abertura": pct(views, sent),
            "taxa_clique": pct(clicks, sent),
        })
    tot_env = sum(l["enviados"] for l in linhas)
    tot_vie = sum(l["aberturas"] for l in linhas)
    tot_cli = sum(l["cliques"] for l in linhas)
    tot_ent = sum(l["entregues"] for l in linhas)
    tem_bounce = any(l["bounces"] for l in linhas)
    return {
        "gerado_em": agora.isoformat(),
        "periodo_dias": days,
        "campanhas": linhas,
        "resumo": {
            "n_campanhas": len(linhas),
            "enviados": tot_env,
            "taxa_entrega_media": pct(tot_ent, tot_env),
            "taxa_abertura_media": pct(tot_vie, tot_env),
            "taxa_clique_media": pct(tot_cli, tot_env),
            "entrega_confiavel": tem_bounce,  # False = Listmonk não recebeu bounces do SES
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-age-min", type=int, default=360)
    a = ap.parse_args()
    # frescor: evita martelar a API a cada tick do cron
    if a.max_age_min > 0 and os.path.exists(a.out):
        idade = (datetime.datetime.now().timestamp() - os.path.getmtime(a.out)) / 60.0
        if idade < a.max_age_min:
            print("[report] recente (%.0f min) — pulando" % idade)
            return
    rel = coletar(a.days)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=1)
    try:
        os.chmod(a.out, 0o644)
    except Exception:
        pass
    r = rel["resumo"]
    print("[report] %d campanhas | enviados %d | abertura %.1f%% | clique %.1f%%"
          % (r["n_campanhas"], r["enviados"], r["taxa_abertura_media"], r["taxa_clique_media"]))


if __name__ == "__main__":
    main()
