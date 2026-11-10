#!/usr/bin/env python3
"""
Enfileira uma newsletter para disparo automático pelo servidor.

Recebe um JSON com a copy (assunto, preheader, parágrafos, CTA) e grava
newsletter/queue/<slug>.json com o conteúdo HTML pronto para o Listmonk.
O servidor (newsletter/dispatch.py, chamado pelo deploy.sh) envia e marca
como enviado — este script NÃO envia nada, só enfileira.

Uso:
  python3 motor/enqueue_newsletter.py --copy copy.json --slug <slug> [--repo .]

copy.json:
  {
    "assunto": "...",
    "preheader": "...",
    "paragrafos": ["<p1>", "<p2>", ...],
    "cta_texto": "Ler no blog →",
    "cta_url": "https://encontrarastudo.com.br/<slug>.html"
  }
Para a carta de sexta, use tipo:"carta" (sem CTA de artigo) — os parágrafos
já trazem a carta inteira.
"""
import argparse, json, os, html, datetime

OX = "#681F35"; GOLD = "#C7A56B"

def render_content(copy):
    pre = html.escape(copy.get("preheader",""))
    out = []
    # preheader escondido (preview do e-mail)
    out.append('<span style="display:none!important;opacity:0;color:transparent;'
               'height:0;width:0;overflow:hidden">%s</span>' % pre)
    for p in copy.get("paragrafos", []):
        # parágrafos já vêm como HTML interno (podem ter <strong>, <em>…)
        out.append('<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#211C26">%s</p>' % p)
    cta_txt = copy.get("cta_texto"); cta_url = copy.get("cta_url")
    if cta_txt and cta_url:
        out.append(
          '<table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0">'
          '<tr><td style="border-radius:6px;background:%s">'
          '<a href="%s" style="display:inline-block;padding:13px 26px;font-size:16px;'
          'font-weight:700;color:#ffffff;text-decoration:none;border-radius:6px">%s</a>'
          '</td></tr></table>' % (OX, html.escape(cta_url), html.escape(cta_txt)))
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    with open(a.copy, encoding="utf-8") as f:
        copy = json.load(f)
    assunto = copy.get("assunto","").strip()
    if not assunto:
        raise SystemExit("ERRO: copy sem 'assunto'")
    content = render_content(copy)
    qdir = os.path.join(a.repo, "newsletter", "queue")
    os.makedirs(qdir, exist_ok=True)
    entry = {
        "slug": a.slug,
        "assunto": assunto,
        "content_html": content,
        "criado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    path = os.path.join(qdir, a.slug + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2); f.write("\n")
    print("Enfileirada:", path, "|", assunto)

if __name__ == "__main__":
    main()
