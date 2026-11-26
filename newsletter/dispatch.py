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
WARMUP_CFG   = os.path.join(HERE, "warmup.json")     # versionado: plano do aquecimento
WARMUP_STATE = os.path.join(HERE, ".warmup_state")   # gitignored: nº de envios já feitos

def load_sent():
    if not os.path.exists(SENT): return set()
    with open(SENT, encoding="utf-8") as f:
        return {ln.split("\t")[0].strip() for ln in f if ln.strip()}

def warmup_passos():
    """Lê o plano de aquecimento. Retorna lista de cortes % (ex.: [5,12,...,100]) ou []."""
    try:
        cfg = json.load(open(WARMUP_CFG, encoding="utf-8"))
    except Exception:
        return []
    if not cfg.get("ativo"):
        return []
    passos = [int(x) for x in cfg.get("passos", []) if 0 < int(x) <= 100]
    return passos

def warmup_feitos():
    try:
        return int(open(WARMUP_STATE, encoding="utf-8").read().strip() or "0")
    except Exception:
        return 0

def warmup_marca(n):
    try:
        with open(WARMUP_STATE, "w", encoding="utf-8") as f:
            f.write(str(n))
    except Exception:
        pass

def proxima_fatia():
    """Query do Listmonk para o envio de agora, ou None (lista inteira).
    Segurança: durante o aquecimento NUNCA retorna a lista inteira antes da hora;
    se algo estiver estranho no estado, usa o menor passo."""
    passos = warmup_passos()
    if not passos:
        return None, None
    feitos = warmup_feitos()
    if feitos >= len(passos):
        return None, None  # aquecimento concluído -> lista inteira
    k = passos[feitos]
    if k >= 100:
        return None, k     # último passo é a lista inteira
    return "(subscribers.id %% 100) < %d" % k, k

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
        query, k = proxima_fatia()   # aquecimento: fatia crescente da lista
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(content); cpath = tf.name
        try:
            lm.send_article(assunto, cpath, query=query)   # cria campanha e inicia o envio
            mark_sent(slug, assunto)
            if k is not None:  # era um passo de aquecimento -> avança o contador
                warmup_marca(warmup_feitos() + 1)
                print("[dispatch] ENVIADA (aquecimento ~%d%%): %s | %s" % (k, slug, assunto))
            else:
                print("[dispatch] ENVIADA (lista inteira): %s | %s" % (slug, assunto))
        except Exception as ex:
            print("[dispatch] ERRO em %s: %s" % (slug, ex), file=sys.stderr)
        finally:
            try: os.unlink(cpath)
            except OSError: pass

if __name__ == "__main__":
    main()
