#!/usr/bin/env python3
"""
Despachante de newsletters (roda NO SERVIDOR, chamado pelo deploy.sh).

Lê newsletter/queue/*.json e, para cada item ainda não enviado, dispara via
lm.py -> Listmonk. Marca o slug em newsletter/.sent.log (fora do git) para
nunca reenviar. Idempotente: pode rodar a cada deploy sem risco de duplicar.

Credenciais vêm do ambiente (/opt/newsletter.env), igual ao lm.py.
  LISTMONK_URL, LISTMONK_USER, LISTMONK_TOKEN, LISTMONK_LIST_BLOG

Uso:
  python3 newsletter/dispatch.py            # envia os pendentes
  python3 newsletter/dispatch.py --dry-run  # só lista o que enviaria
"""
import os, sys, json, tempfile, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue")
SENT  = os.path.join(HERE, ".sent.log")   # gitignored; estado local do servidor

def load_sent():
    if not os.path.exists(SENT): return set()
    with open(SENT, encoding="utf-8") as f:
        return {ln.split("\t")[0].strip() for ln in f if ln.strip()}

def mark_sent(slug, assunto):
    with open(SENT, "a", encoding="utf-8") as f:
        f.write("%s\t%s\t%s\n" % (slug, datetime.datetime.now(datetime.timezone.utc)
                                  .isoformat(timespec="seconds"), assunto))

def main():
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(QUEUE):
        print("[dispatch] sem fila."); return
    sent = load_sent()
    items = sorted(f for f in os.listdir(QUEUE) if f.endswith(".json"))
    pend = []
    for fn in items:
        slug = fn[:-5]
        if slug in sent: continue
        with open(os.path.join(QUEUE, fn), encoding="utf-8") as f:
            pend.append(json.load(f))
    if not pend:
        print("[dispatch] nada pendente."); return

    if dry:
        for e in pend:
            print("[dry-run] enviaria:", e["slug"], "|", e["assunto"])
        return

    # importa lm.py do diretório irmão
    sys.path.insert(0, HERE)
    import lm
    for e in pend:
        slug, assunto, content = e["slug"], e["assunto"], e["content_html"]
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(content); cpath = tf.name
        try:
            lm.send_article(assunto, cpath)      # cria campanha e inicia o envio p/ a lista
            mark_sent(slug, assunto)
            print("[dispatch] ENVIADA:", slug, "|", assunto)
        except Exception as ex:
            print("[dispatch] ERRO em %s: %s" % (slug, ex), file=sys.stderr)
        finally:
            try: os.unlink(cpath)
            except OSError: pass

if __name__ == "__main__":
    main()
