#!/usr/bin/env python3
# Ferramenta de newsletter via API do Listmonk. Roda no servidor (alcança o Listmonk).
# Credenciais vêm do ambiente (ver /opt/newsletter.env), nunca do repositório.
import os, sys, json, urllib.request, urllib.error

URL  = os.environ.get("LISTMONK_URL", "https://lista.encontrarastudo.com.br").rstrip("/")
USER = os.environ.get("LISTMONK_USER", "")
TOKEN= os.environ.get("LISTMONK_TOKEN", "")
LIST_BLOG = int(os.environ.get("LISTMONK_LIST_BLOG", "3"))
HERE = os.path.dirname(os.path.abspath(__file__))
TPL_NAME = "Encontrarás Tudo"

def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(URL + path, data=body, method=method)
    r.add_header("Authorization", "token %s:%s" % (USER, TOKEN))
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            txt = resp.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        sys.stderr.write("HTTP %s em %s: %s\n" % (e.code, path, e.read().decode()[:500]))
        raise

def register_template():
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    existing = req("GET", "/api/templates").get("data", [])
    found = next((t for t in existing if t.get("name") == TPL_NAME), None)
    payload = {"name": TPL_NAME, "type": "campaign", "body": tpl}
    if found:
        req("PUT", "/api/templates/%d" % found["id"], payload)
        print("Template atualizado (id %d)" % found["id"]); return found["id"]
    res = req("POST", "/api/templates", payload)
    tid = res.get("data", {}).get("id")
    print("Template criado (id %s)" % tid); return tid

def send_article(subject, content_path, test_to=None):
    content = open(content_path, encoding="utf-8").read()
    tid = register_template()
    camp = {"name": "[Blog] " + subject, "subject": subject, "lists": [LIST_BLOG],
            "type": "regular", "content_type": "html", "template_id": tid,
            "body": content, "messenger": "email", "tags": ["blog"]}
    res = req("POST", "/api/campaigns", camp)
    cid = res.get("data", {}).get("id")
    print("Campanha criada (id %s)" % cid)
    if test_to:
        req("POST", "/api/campaigns/%d/test" % cid,
            {"subscribers": [test_to], "name": camp["name"], "subject": subject,
             "lists": [LIST_BLOG], "template_id": tid, "content_type": "html", "body": content, "messenger": "email"})
        print("E-mail de teste enviado para %s (campanha fica em rascunho)." % test_to)
    else:
        req("PUT", "/api/campaigns/%d/status" % cid, {"status": "running"})
        print("Campanha iniciada — enviando para a lista.")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "register-template":
        register_template()
    elif cmd == "send-article":
        # send-article "<assunto>" <arquivo_conteudo> [email_de_teste]
        send_article(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        print("uso: lm.py register-template | send-article \"<assunto>\" <arquivo_conteudo> [email_teste]")
