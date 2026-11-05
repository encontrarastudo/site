# -*- coding: utf-8 -*-
"""
Painel administrativo do Encontrarás Tudo.
Edita orações/novenas (data/*.json), faz upload de imagens e publica o site
(regenera o estático em ET_OUT_DIR). App de arquivo único, templates inline.
"""
import os, re, json, secrets, subprocess, sys, unicodedata, shutil
from functools import wraps
from flask import (Flask, request, session, redirect, url_for, flash,
                   render_template_string, abort)
from werkzeug.security import check_password_hash, generate_password_hash

SRC      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SRC, "data")
IMG_DIR  = os.path.join(SRC, "assets", "img")
OUT_DIR  = os.environ.get("ET_OUT_DIR", "/var/www/encontrarastudo")
# Senha: hash em ADMIN_PASSWORD_HASH, ou texto em ADMIN_PASSWORD (gera hash no boot).
_PW_HASH = os.environ.get("ADMIN_PASSWORD_HASH") or (
    generate_password_hash(os.environ["ADMIN_PASSWORD"]) if os.environ.get("ADMIN_PASSWORD") else None)

app = Flask(__name__)
app.secret_key = os.environ.get("ADMIN_SECRET", secrets.token_hex(32))
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  MAX_CONTENT_LENGTH=12 * 1024 * 1024)

CATS_ORACAO = ["Dia a dia", "A Jesus e ao Espírito Santo", "Marianas", "Santos e Anjos"]
GRPS_NOVENA = ["A Jesus e ao Espírito Santo", "A Nossa Senhora", "Aos Santos e Anjos"]

# ---------------- dados ----------------
FILES = {"oracao": "oracoes.json", "novena": "novenas.json", "artigo": "artigos.json", "produto": "produtos.json"}
CORES = [("c1", "Vermelho"), ("c2", "Escuro"), ("c3", "Dourado"), ("c4", "Oxblood")]
CATS_ARTIGO = ["Doutrina", "Santos", "Apologética", "Eucaristia", "Maria", "Vida cristã", "Liturgia", "Moral"]

def _path(kind):
    return os.path.join(DATA_DIR, FILES[kind])

def load(kind):
    with open(_path(kind), encoding="utf-8") as f:
        return json.load(f)

def load_cfg():
    with open(os.path.join(DATA_DIR, "config.json"), encoding="utf-8") as f:
        return json.load(f)

def save_cfg(cfg):
    tmp = os.path.join(DATA_DIR, "config.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, os.path.join(DATA_DIR, "config.json"))

def save(kind, items):
    tmp = _path(kind) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _path(kind))

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "item"

def images():
    try:
        return sorted(f[:-5] for f in os.listdir(IMG_DIR) if f.endswith(".webp"))
    except FileNotFoundError:
        return []

# ---------------- auth ----------------
def login_required(f):
    @wraps(f)
    def g(*a, **k):
        if not session.get("auth"):
            return redirect(url_for("login", next=request.path))
        return f(*a, **k)
    return g

def check_csrf():
    if request.form.get("_csrf") != session.get("csrf"):
        abort(400, "CSRF inválido")

@app.before_request
def _csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)

# ---------------- rotas ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if _PW_HASH and check_password_hash(_PW_HASH, request.form.get("password", "")):
            session["auth"] = True
            return redirect(request.args.get("next") or url_for("index"))
        flash("Senha incorreta.")
    return render_template_string(T_LOGIN)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template_string(T_LIST, oracoes=load("oracao"), novenas=load("novena"),
                                  artigos=load("artigo"), produtos=load("produto"), csrf=session["csrf"])

@app.route("/edit/<kind>/<slug>", methods=["GET", "POST"])
@app.route("/new/<kind>", methods=["GET", "POST"], defaults={"slug": None})
@login_required
def edit(kind, slug):
    if kind not in ("oracao", "novena"):
        abort(404)
    items = load(kind)
    item = next((x for x in items if x["slug"] == slug), None) if slug else None
    if slug and item is None:
        abort(404)
    if request.method == "POST":
        check_csrf()
        f = request.form
        new_slug = slugify(f.get("slug") or f.get("nome", ""))
        rel = [slugify(r) for r in re.split(r"[,\n]", f.get("related", "")) if r.strip()]
        data = {"slug": new_slug, "nome": f.get("nome", "").strip(),
                "cat": f.get("cat", "").strip(), "img": f.get("img", "").strip(),
                "sub": f.get("sub", "").strip(), "intro": f.get("intro", "").strip(),
                "sobre" if kind == "oracao" else "como": f.get("corpo2", "").strip(),
                "related": rel}
        if kind == "oracao":
            data["texto"] = f.get("corpo1", "").strip()
        else:
            data["oracao"] = f.get("corpo1", "").strip()
            data["grp"] = f.get("grp", "").strip()
            data["fecho"] = f.get("fecho", "").strip()
            data["festa"] = f.get("festa", "").strip()
        if item:
            items[items.index(item)] = data
        else:
            if any(x["slug"] == new_slug for x in items):
                flash("Já existe um item com esse endereço (slug).")
                return render_template_string(T_EDIT, kind=kind, item=request.form, imgs=images(),
                                              cats=CATS_ORACAO, grps=GRPS_NOVENA, csrf=session["csrf"], new=True)
            items.append(data)
        save(kind, items)
        flash("Salvo. Clique em Publicar para pôr no ar.")
        return redirect(url_for("index"))
    return render_template_string(T_EDIT, kind=kind, item=item or {}, imgs=images(),
                                  cats=CATS_ORACAO, grps=GRPS_NOVENA, csrf=session["csrf"], new=item is None)

@app.route("/edit-artigo/<slug>", methods=["GET", "POST"])
@app.route("/new-artigo", methods=["GET", "POST"], defaults={"slug": None})
@login_required
def edit_artigo(slug):
    items = load("artigo")
    item = next((x for x in items if x["slug"] == slug), None) if slug else None
    if slug and item is None:
        abort(404)
    if request.method == "POST":
        check_csrf()
        f = request.form
        new_slug = slugify(f.get("slug") or f.get("titulo", ""))
        tags = [t.strip() for t in re.split(r"[,\n]", f.get("tags", "")) if t.strip()]
        data = {"slug": new_slug, "titulo": f.get("titulo", "").strip(), "dek": f.get("dek", "").strip(),
                "resumo": (f.get("resumo", "").strip() or f.get("dek", "").strip()),
                "categoria": f.get("categoria", "").strip(), "tags": tags,
                "img": f.get("img", "").strip(), "data": f.get("data", "").strip(),
                "data_br": f.get("data_br", "").strip(), "leitura": f.get("leitura", "").strip(),
                "autor": (f.get("autor", "").strip() or "Gustavo Souza"),
                "status": f.get("status", "em-breve").strip(), "body": f.get("body", "").strip()}
        if item:
            items[items.index(item)] = data
        else:
            if any(x["slug"] == new_slug for x in items):
                flash("Já existe um artigo com esse endereço (slug).")
                return render_template_string(T_ARTIGO, item=request.form, imgs=images(),
                                              cats=CATS_ARTIGO, csrf=session["csrf"], new=True)
            items.append(data)
        save("artigo", items)
        flash("Artigo salvo. Clique em Publicar para pôr no ar.")
        return redirect(url_for("index"))
    return render_template_string(T_ARTIGO, item=item or {}, imgs=images(), cats=CATS_ARTIGO,
                                  csrf=session["csrf"], new=item is None)

@app.route("/edit-produto/<int:idx>", methods=["GET", "POST"])
@app.route("/new-produto", methods=["GET", "POST"], defaults={"idx": None})
@login_required
def edit_produto(idx):
    items = load("produto")
    item = items[idx] if (idx is not None and 0 <= idx < len(items)) else None
    if idx is not None and item is None:
        abort(404)
    if request.method == "POST":
        check_csrf()
        f = request.form
        data = {"nome": f.get("nome", "").strip(), "desc": f.get("desc", "").strip(),
                "link": f.get("link", "").strip(), "img": f.get("img", "").strip(),
                "cor": f.get("cor", "c1").strip(), "badge": f.get("badge", "").strip()}
        if item is not None:
            items[idx] = data
        else:
            items.append(data)
        save("produto", items)
        flash("Material salvo. Clique em Publicar para pôr no ar.")
        return redirect(url_for("index"))
    return render_template_string(T_PRODUTO, item=item or {}, cores=CORES, imgs=images(),
                                  csrf=session["csrf"], new=item is None)

@app.route("/delete-produto/<int:idx>", methods=["POST"])
@login_required
def delete_produto(idx):
    check_csrf()
    items = load("produto")
    if 0 <= idx < len(items):
        items.pop(idx)
        save("produto", items)
        flash("Material removido. Publique para refletir no site.")
    return redirect(url_for("index"))

@app.route("/config", methods=["GET", "POST"])
@login_required
def config():
    cfg = load_cfg()
    if request.method == "POST":
        check_csrf()
        f = request.form
        cfg["announce"] = {"texto": f.get("an_texto", ""), "link": f.get("an_link", ""), "label": f.get("an_label", "")}
        cfg["cta_gratis"] = {"kicker": f.get("g_kicker", ""), "titulo": f.get("g_titulo", ""),
                             "texto": f.get("g_texto", ""), "botao": f.get("g_botao", ""), "link": f.get("g_link", "")}
        cfg["cta_produto"] = {"kicker": f.get("p_kicker", ""), "titulo": f.get("p_titulo", ""),
                              "texto": f.get("p_texto", ""), "preco": f.get("p_preco", ""),
                              "botao": f.get("p_botao", ""), "link": f.get("p_link", "")}
        for k in ("newsletter_uuid", "listmonk_url", "instagram", "youtube", "email"):
            cfg[k] = f.get(k, "").strip()
        save_cfg(cfg)
        flash("Configurações salvas. Clique em Publicar para aplicar no site.")
        return redirect(url_for("config"))
    return render_template_string(T_CONFIG, c=cfg, csrf=session["csrf"])

@app.route("/delete/<kind>/<slug>", methods=["POST"])
@login_required
def delete(kind, slug):
    check_csrf()
    if kind not in FILES:
        abort(404)
    items = [x for x in load(kind) if x["slug"] != slug]
    save(kind, items)
    flash("Item removido. Publique para refletir no site.")
    return redirect(url_for("index"))

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    check_csrf()
    file = request.files.get("file")
    name = slugify(request.form.get("name", "") or (file.filename if file else ""))
    if not file or not name:
        flash("Selecione um arquivo e um nome.")
        return redirect(url_for("index"))
    dest = os.path.join(IMG_DIR, name + ".webp")
    try:
        from PIL import Image
        im = Image.open(file.stream).convert("RGB")
        w, h = im.size
        if w > 900:
            im = im.resize((900, int(h * 900 / w)))
        os.makedirs(IMG_DIR, exist_ok=True)
        im.save(dest, "WEBP", quality=82, method=6)
        flash("Imagem enviada: %s" % (name + ".webp"))
    except Exception as e:
        flash("Falha ao processar a imagem: %s" % e)
    return redirect(request.form.get("back") or url_for("index"))

@app.route("/publish", methods=["POST"])
@login_required
def publish():
    check_csrf()
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        # 1) copia assets (inclui imagens novas) para a saída
        src_assets = os.path.join(SRC, "assets")
        if os.path.isdir(src_assets):
            subprocess.run(["cp", "-r", src_assets, OUT_DIR + "/"], check=True)
        # 2) regenera o HTML
        env = dict(os.environ, ET_OUT_DIR=OUT_DIR, ET_DATA_DIR=DATA_DIR)
        r = subprocess.run([sys.executable, "build_oracoes.py"], cwd=SRC, env=env,
                           capture_output=True, text=True, timeout=120)
        # 3) index.html não é gerado: copia da fonte se existir
        idx = os.path.join(SRC, "index.html")
        if os.path.isfile(idx):
            shutil.copy(idx, os.path.join(OUT_DIR, "index.html"))
        # 4) permissões de leitura pública
        subprocess.run(["chmod", "-R", "a+rX", OUT_DIR], check=False)
        if r.returncode == 0:
            flash("Publicado! O site foi atualizado em encontrarastudo.com.br.")
        else:
            flash("Erro ao gerar: " + (r.stderr or r.stdout)[-400:])
    except Exception as e:
        flash("Falha ao publicar: %s" % e)
    return redirect(url_for("index"))

# ---------------- templates ----------------
BASE_CSS = """
:root{--red:#681f35;--gold:#c7a56b;--dark:#211c26;--palha:#f1e3cf;--surface:#f8efdd;--ink:#211c26;--soft:#6a5b60;--rule:#e1d2b6}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,Segoe UI,sans-serif;background:var(--palha);color:var(--ink)}
a{color:var(--red)}header{background:var(--dark);color:#f1e3cf;padding:.9rem 1.2rem;display:flex;justify-content:space-between;align-items:center}
header a{color:var(--gold);text-decoration:none;font-weight:600}.wrap{max-width:900px;margin:0 auto;padding:1.4rem 1.2rem}
.btn{display:inline-block;background:var(--red);color:#f1e3cf;border:none;padding:.55rem 1.1rem;border-radius:7px;font-weight:600;cursor:pointer;text-decoration:none;font-size:.95rem}
.btn.gold{background:var(--gold);color:#2a1c06}.btn.ghost{background:transparent;border:1px solid var(--red);color:var(--red)}
.btn.sm{padding:.3rem .7rem;font-size:.85rem}.btn.danger{background:#9a2520}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:1rem 1.2rem;margin-bottom:.7rem;display:flex;justify-content:space-between;align-items:center;gap:1rem}
.card h3{margin:.1rem 0;font-size:1.05rem}.card p{margin:0;color:var(--soft);font-size:.85rem}
label{display:block;font-weight:600;font-size:.85rem;margin:.9rem 0 .25rem}
input,select,textarea{width:100%;padding:.55rem .7rem;border:1px solid var(--rule);border-radius:6px;font-family:inherit;font-size:.95rem;background:#fff}
textarea{min-height:7rem;line-height:1.5}.hint{font-size:.78rem;color:var(--soft);margin:.2rem 0 0}
.flash{background:#fff6e0;border:1px solid var(--gold);border-radius:8px;padding:.7rem 1rem;margin-bottom:1rem}
.group{margin:1.6rem 0 .6rem;font-weight:700;color:var(--red);border-bottom:1px solid var(--rule);padding-bottom:.3rem}
.row{display:flex;gap:1rem;flex-wrap:wrap}.row>div{flex:1 1 15rem}.toolbar{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:1.2rem}
"""
def _flash():
    return ("{% with m=get_flashed_messages() %}{% if m %}<div class='flash'>"
            "{% for x in m %}{{x}}<br>{% endfor %}</div>{% endif %}{% endwith %}")

T_LOGIN = """<!doctype html><meta charset=utf-8><title>Admin · Encontrarás Tudo</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<div class=wrap style="max-width:360px;margin-top:12vh">
<h1 style="color:var(--red)">Painel · Encontrarás Tudo</h1>""" + _flash() + """
<form method=post><label>Senha</label><input type=password name=password autofocus>
<p><button class=btn type=submit>Entrar</button></p></form></div>"""

T_LIST = """<!doctype html><meta charset=utf-8><title>Admin · Encontrarás Tudo</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<header><span><b>Encontrarás Tudo</b> · painel</span>
<span><a href="https://encontrarastudo.com.br" target=_blank>ver site ↗</a> &nbsp; <a href="{{url_for('logout')}}">sair</a></span></header>
<div class=wrap>""" + _flash() + """
<div class=toolbar>
  <form method=post action="{{url_for('publish')}}" onsubmit="return confirm('Publicar as alterações no site ao vivo?')">
    <input type=hidden name=_csrf value="{{csrf}}"><button class="btn gold">▲ Publicar site</button></form>
  <a class="btn" href="{{url_for('edit', kind='oracao', slug=None)}}">+ Oração</a>
  <a class="btn" href="{{url_for('edit', kind='novena', slug=None)}}">+ Novena</a>
  <a class="btn" href="{{url_for('edit_artigo', slug=None)}}">+ Artigo</a>
  <a class="btn" href="{{url_for('edit_produto', idx=None)}}">+ Material</a>
  <a class="btn ghost" href="{{url_for('config')}}">⚙ Banners &amp; Config</a>
</div>
<form method=post action="{{url_for('upload')}}" enctype=multipart/form-data class=card>
  <input type=hidden name=_csrf value="{{csrf}}">
  <div style="flex:1"><b>Enviar imagem</b><div class=row>
    <div><input type=file name=file accept="image/*" required></div>
    <div><input name=name placeholder="nome-da-imagem (ex.: sao-jorge)" required></div></div></div>
  <button class="btn sm">Enviar</button>
</form>
<div class=group>Orações ({{oracoes|length}})</div>
{% for o in oracoes %}<div class=card><div><h3>{{o.nome}}</h3><p>{{o.cat}} · imagem: {{o.img}}</p></div>
<div><a class="btn sm" href="{{url_for('edit',kind='oracao',slug=o.slug)}}">editar</a>
<form method=post action="{{url_for('delete',kind='oracao',slug=o.slug)}}" style=display:inline onsubmit="return confirm('Remover {{o.nome}}?')">
<input type=hidden name=_csrf value="{{csrf}}"><button class="btn sm danger">excluir</button></form></div></div>{% endfor %}
<div class=group>Novenas ({{novenas|length}})</div>
{% for o in novenas %}<div class=card><div><h3>{{o.nome}}</h3><p>{{o.grp}} · imagem: {{o.img}}</p></div>
<div><a class="btn sm" href="{{url_for('edit',kind='novena',slug=o.slug)}}">editar</a>
<form method=post action="{{url_for('delete',kind='novena',slug=o.slug)}}" style=display:inline onsubmit="return confirm('Remover {{o.nome}}?')">
<input type=hidden name=_csrf value="{{csrf}}"><button class="btn sm danger">excluir</button></form></div></div>{% endfor %}
<div class=group>Blog ({{artigos|length}})</div>
{% for o in artigos %}<div class=card><div><h3>{{o.titulo|safe}}</h3>
<p>{{o.categoria}} · {{ 'publicado' if o.status=='publicado' else 'em breve' }}{% if o.data_br %} · {{o.data_br}}{% endif %}</p></div>
<div><a class="btn sm" href="{{url_for('edit_artigo',slug=o.slug)}}">editar</a>
<form method=post action="{{url_for('delete',kind='artigo',slug=o.slug)}}" style=display:inline onsubmit="return confirm('Remover este artigo?')">
<input type=hidden name=_csrf value="{{csrf}}"><button class="btn sm danger">excluir</button></form></div></div>{% endfor %}
<div class=group>Ferramentas / materiais ({{produtos|length}})</div>
{% for o in produtos %}<div class=card><div><h3>{{o.nome|safe}}</h3><p>{{o.link}}</p></div>
<div><a class="btn sm" href="{{url_for('edit_produto',idx=loop.index0)}}">editar</a>
<form method=post action="{{url_for('delete_produto',idx=loop.index0)}}" style=display:inline onsubmit="return confirm('Remover este material?')">
<input type=hidden name=_csrf value="{{csrf}}"><button class="btn sm danger">excluir</button></form></div></div>{% endfor %}
</div>"""

T_EDIT = """<!doctype html><meta charset=utf-8><title>Editar · Admin</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<header><span><b>Encontrarás Tudo</b> · {{ 'nova' if new else 'editar' }} {{ 'oração' if kind=='oracao' else 'novena' }}</span>
<a href="{{url_for('index')}}">← voltar</a></header>
<div class=wrap>""" + _flash() + """
<form method=post><input type=hidden name=_csrf value="{{csrf}}">
<label>Nome (título)</label><input name=nome value="{{item.nome|default('')}}" required>
<div class=row>
  <div><label>Endereço (slug)</label><input name=slug value="{{item.slug|default('')}}" placeholder="gera do nome se vazio">
    <p class=hint>vira o endereço: /slug.html — só letras, números e hífen</p></div>
  <div><label>Imagem</label><input name=img list=imglist value="{{item.img|default('')}}">
    <datalist id=imglist>{% for i in imgs %}<option value="{{i}}">{% endfor %}</datalist>
    <p class=hint>nome do arquivo em assets/img, sem .webp — envie novas no painel inicial</p></div>
</div>
<div class=row>
{% if kind=='oracao' %}
  <div><label>Categoria</label><select name=cat>{% for c in cats %}<option {{'selected' if item.cat==c else ''}}>{{c}}</option>{% endfor %}</select></div>
{% else %}
  <div><label>Grupo</label><select name=grp>{% for g in grps %}<option {{'selected' if item.grp==g else ''}}>{{g}}</option>{% endfor %}</select></div>
  <div><label>Rótulo (cat)</label><input name=cat value="{{item.cat|default('')}}" placeholder="ex.: Causas urgentes"></div>
{% endif %}
</div>
<label>Subtítulo</label><input name=sub value="{{item.sub|default('')}}">
<label>Introdução (pode usar &lt;strong&gt;)</label><textarea name=intro>{{item.intro|default('')}}</textarea>
{% if kind=='oracao' %}
  <label>Texto da oração (use &lt;br&gt; para quebra de linha)</label><textarea name=corpo1 style=min-height:12rem>{{item.texto|default('')}}</textarea>
  <label>Como e quando rezar (pode usar &lt;p&gt;)</label><textarea name=corpo2>{{item.sobre|default('')}}</textarea>
{% else %}
  <label>Oração da novena (use &lt;br&gt;)</label><textarea name=corpo1 style=min-height:12rem>{{item.oracao|default('')}}</textarea>
  <label>Como rezar (pode usar &lt;p&gt;)</label><textarea name=corpo2>{{item.como|default('')}}</textarea>
  <div class=row>
    <div><label>Para concluir cada dia</label><input name=fecho value="{{item.fecho|default('Pai-Nosso, Ave-Maria e Glória ao Pai.')}}"></div>
    <div><label>Festa (ex.: 22 de maio)</label><input name=festa value="{{item.festa|default('')}}"></div>
  </div>
{% endif %}
<label>Relacionadas (slugs, separados por vírgula)</label><textarea name=related style=min-height:3rem>{{ item.related|join(', ') if item.related else '' }}</textarea>
<p style=margin-top:1.4rem><button class="btn" type=submit>Salvar</button>
<a class="btn ghost" href="{{url_for('index')}}">cancelar</a></p>
</form></div>"""

T_ARTIGO = """<!doctype html><meta charset=utf-8><title>Artigo · Admin</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<header><span><b>Encontrarás Tudo</b> · {{ 'novo' if new else 'editar' }} artigo</span>
<a href="{{url_for('index')}}">← voltar</a></header>
<div class=wrap>""" + _flash() + """
<form method=post><input type=hidden name=_csrf value="{{csrf}}">
<label>Título</label><input name=titulo value="{{item.titulo|default('')}}" required>
<div class=row>
  <div><label>Endereço (slug)</label><input name=slug value="{{item.slug|default('')}}" placeholder="gera do título se vazio">
    <p class=hint>vira /slug.html</p></div>
  <div><label>Status</label><select name=status>
    <option value=publicado {{'selected' if item.status=='publicado' else ''}}>publicado</option>
    <option value=em-breve {{'selected' if item.status!='publicado' else ''}}>em breve (só card, sem página)</option>
  </select></div>
</div>
<div class=row>
  <div><label>Categoria</label><input name=categoria list=catlist value="{{item.categoria|default('')}}">
    <datalist id=catlist>{% for c in cats %}<option value="{{c}}">{% endfor %}</datalist></div>
  <div><label>Imagem de capa</label><input name=img list=imglist value="{{item.img|default('')}}">
    <datalist id=imglist>{% for i in imgs %}<option value="{{i}}">{% endfor %}</datalist></div>
</div>
<div class=row>
  <div><label>Data (AAAA-MM-DD)</label><input name=data value="{{item.data|default('')}}" placeholder="2026-11-03"></div>
  <div><label>Data por extenso</label><input name=data_br value="{{item.data_br|default('')}}" placeholder="3 de novembro de 2026"></div>
  <div><label>Tempo de leitura</label><input name=leitura value="{{item.leitura|default('')}}" placeholder="6 min de leitura"></div>
</div>
<label>Chamada (dek) — frase curta abaixo do título</label><textarea name=dek style=min-height:3rem>{{item.dek|default('')}}</textarea>
<label>Resumo do card (no blog) — se vazio, usa a chamada</label><textarea name=resumo style=min-height:3rem>{{item.resumo|default('')}}</textarea>
<label>Tags (separadas por vírgula)</label><input name=tags value="{{ item.tags|join(', ') if item.tags else '' }}">
<label>Corpo do artigo (HTML: &lt;p&gt;, &lt;h2&gt;, &lt;em&gt;… use [[CTA]] onde quiser inserir o banner do guia)</label>
<textarea name=body style=min-height:22rem>{{item.body|default('')}}</textarea>
<p class=hint>O banner duplo (guia grátis + Mapas Mentais) é adicionado automaticamente no fim. Autor: Gustavo Souza.</p>
<input type=hidden name=autor value="{{item.autor|default('Gustavo Souza')}}">
<p style=margin-top:1.4rem><button class="btn" type=submit>Salvar</button>
<a class="btn ghost" href="{{url_for('index')}}">cancelar</a></p>
</form></div>"""

T_CONFIG = """<!doctype html><meta charset=utf-8><title>Config · Admin</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<header><span><b>Encontrarás Tudo</b> · banners &amp; configurações</span><a href="{{url_for('index')}}">← voltar</a></header>
<div class=wrap>""" + _flash() + """
<form method=post><input type=hidden name=_csrf value="{{csrf}}">
<div class=group>Barra de aviso (topo do site)</div>
<div class=row>
  <div style="flex:2 1 20rem"><label>Texto</label><input name=an_texto value="{{c.announce.texto|default('')}}"></div>
  <div><label>Link</label><input name=an_link value="{{c.announce.link|default('')}}"></div>
  <div><label>Rótulo do link</label><input name=an_label value="{{c.announce.label|default('')}}"></div>
</div>
<div class=group>Banner — material GRÁTIS (isca)</div>
<div class=row>
  <div><label>Rótulo</label><input name=g_kicker value="{{c.cta_gratis.kicker|default('')}}"></div>
  <div><label>Título</label><input name=g_titulo value="{{c.cta_gratis.titulo|default('')}}"></div>
</div>
<label>Texto</label><textarea name=g_texto style=min-height:3rem>{{c.cta_gratis.texto|default('')}}</textarea>
<div class=row>
  <div><label>Texto do botão</label><input name=g_botao value="{{c.cta_gratis.botao|default('')}}"></div>
  <div><label>Link</label><input name=g_link value="{{c.cta_gratis.link|default('')}}"></div>
</div>
<div class=group>Banner — material PAGO (infoproduto)</div>
<div class=row>
  <div><label>Rótulo</label><input name=p_kicker value="{{c.cta_produto.kicker|default('')}}"></div>
  <div><label>Título</label><input name=p_titulo value="{{c.cta_produto.titulo|default('')}}"></div>
</div>
<label>Texto</label><textarea name=p_texto style=min-height:3rem>{{c.cta_produto.texto|default('')}}</textarea>
<div class=row>
  <div><label>Preço</label><input name=p_preco value="{{c.cta_produto.preco|default('')}}" placeholder="R$ 47"></div>
  <div><label>Texto do botão</label><input name=p_botao value="{{c.cta_produto.botao|default('')}}"></div>
  <div><label>Link do Cakto</label><input name=p_link value="{{c.cta_produto.link|default('')}}" placeholder="https://pay.cakto.com.br/..."></div>
</div>
<div class=group>Formulários &amp; redes</div>
<div class=row>
  <div><label>UUID da lista (Listmonk)</label><input name=newsletter_uuid value="{{c.newsletter_uuid|default('')}}"></div>
  <div><label>URL do Listmonk</label><input name=listmonk_url value="{{c.listmonk_url|default('')}}"></div>
</div>
<div class=row>
  <div><label>Instagram</label><input name=instagram value="{{c.instagram|default('')}}"></div>
  <div><label>YouTube</label><input name=youtube value="{{c.youtube|default('')}}"></div>
  <div><label>E-mail de contato</label><input name=email value="{{c.email|default('')}}"></div>
</div>
<p style=margin-top:1.4rem><button class="btn" type=submit>Salvar</button>
<a class="btn ghost" href="{{url_for('index')}}">cancelar</a></p>
</form></div>"""

T_PRODUTO = """<!doctype html><meta charset=utf-8><title>Material · Admin</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>""" + BASE_CSS + """</style>
<header><span><b>Encontrarás Tudo</b> · {{ 'novo' if new else 'editar' }} material</span>
<a href="{{url_for('index')}}">← voltar</a></header>
<div class=wrap>""" + _flash() + """
<form method=post><input type=hidden name=_csrf value="{{csrf}}">
<label>Nome do material</label><input name=nome value="{{item.nome|default('')}}" required>
<label>Descrição</label><textarea name=desc style=min-height:4rem>{{item.desc|default('')}}</textarea>
<label>Link (URL)</label><input name=link value="{{item.link|default('')}}" placeholder="https://..." required>
<div class=row>
  <div><label>Imagem (capa)</label><input name=img list=imglist value="{{item.img|default('')}}">
    <datalist id=imglist>{% for i in imgs %}<option value="{{i}}">{% endfor %}</datalist>
    <p class=hint>nome do arquivo em assets/img, sem .webp. Sem imagem, usa fundo colorido.</p></div>
  <div><label>Cor do card (sem imagem)</label><select name=cor>{% for v,n in cores %}<option value="{{v}}" {{'selected' if item.cor==v else ''}}>{{n}}</option>{% endfor %}</select></div>
  <div><label>Selo (opcional)</label><input name=badge value="{{item.badge|default('')}}" placeholder="ex.: Mais procurado"></div>
</div>
<p style=margin-top:1.4rem><button class="btn" type=submit>Salvar</button>
<a class="btn ghost" href="{{url_for('index')}}">cancelar</a></p>
</form></div>"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8001)))
