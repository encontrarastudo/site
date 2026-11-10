#!/usr/bin/env python3
"""
Publicador de artigo do Encontrarás Tudo.

Converte uma "peça" aprovada no painel (Central de Conteúdo) numa entrada do
data/artigos.json, marcando status=publicado. Determinístico e idempotente:
se o slug já existe, atualiza no lugar; senão, insere no topo (mais recente).

Uso:
  python3 motor/publish_article.py --piece peca.json [--date YYYY-MM-DD]
                                   [--repo .] [--dry-run]

A peça (JSON) espera os campos que o painel grava em cada artigo:
  slug, titulo, resumo, tags[], img, conteudo   (dek/categoria/autor opcionais)
O corpo mantém o token [[CTA]] — o build_pages.py injeta o CTA no lugar certo.
"""
import argparse, json, os, re, sys, unicodedata
from datetime import datetime, timezone, timedelta

MESES = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto",
         "setembro","outubro","novembro","dezembro"]

def hoje_brt():
    return datetime.now(timezone(timedelta(hours=-3)))

def data_br(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day} de {MESES[d.month-1]} de {d.year}"

def tempo_leitura(html):
    txt = re.sub(r"<[^>]+>", " ", html or "")
    txt = re.sub(r"&[a-zA-Z]+;", " ", txt)
    n = len([w for w in txt.split() if w.strip()])
    minutos = max(1, round(n/200))
    return f"{minutos} min de leitura"

def slugify(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "artigo"

def to_entry(p, iso):
    slug = p.get("slug") or slugify(p.get("titulo",""))
    resumo = p.get("resumo","")
    tags = p.get("tags") or []
    categoria = p.get("categoria") or (tags[0] if tags else "Doutrina")
    return {
        "slug": slug,
        "titulo": p.get("titulo",""),
        "dek": p.get("dek") or resumo,
        "resumo": resumo,
        "categoria": categoria,
        "tags": tags,
        "img": p.get("img","eucaristia"),
        "data": iso,
        "data_br": data_br(iso),
        "leitura": tempo_leitura(p.get("conteudo","")),
        "autor": p.get("autor","Gustavo Souza"),
        "status": "publicado",
        "body": p.get("conteudo",""),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piece", required=True, help="arquivo JSON da peça aprovada")
    ap.add_argument("--date", help="data de publicação YYYY-MM-DD (padrão: hoje BRT)")
    ap.add_argument("--repo", default=".", help="raiz do repositório do site")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    iso = a.date or hoje_brt().strftime("%Y-%m-%d")
    with open(a.piece, encoding="utf-8") as f:
        piece = json.load(f)
    entry = to_entry(piece, iso)
    if not entry["slug"] or not entry["titulo"]:
        print("ERRO: peça sem slug/titulo", file=sys.stderr); sys.exit(2)

    path = os.path.join(a.repo, "data", "artigos.json")
    with open(path, encoding="utf-8") as f:
        artigos = json.load(f)

    idx = next((i for i,x in enumerate(artigos) if x.get("slug")==entry["slug"]), None)
    if idx is None:
        artigos.insert(0, entry); acao = "inserido (novo)"
    else:
        # preserva a data original se o artigo já estava publicado antes
        if artigos[idx].get("status")=="publicado" and artigos[idx].get("data"):
            entry["data"] = artigos[idx]["data"]; entry["data_br"] = data_br(entry["data"])
        artigos[idx] = entry; acao = "atualizado (existente)"

    if a.dry_run:
        print(f"[dry-run] {acao}: {entry['slug']} ({entry['data']}, {entry['leitura']})")
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artigos, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"OK {acao}: {entry['slug']} — {entry['titulo']} ({entry['data']}, {entry['leitura']})")

if __name__ == "__main__":
    main()
