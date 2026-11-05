# -*- coding: utf-8 -*-
import os, json
SRC = os.path.dirname(os.path.abspath(__file__))
# Pasta de saída dos HTML: configurável (o painel publica direto em /var/www/encontrarastudo)
OUT = os.environ.get("ET_OUT_DIR") or SRC
os.makedirs(OUT, exist_ok=True)
BASE = "https://encontrarastudo.com.br"
from datetime import date
DATA_DIR = os.environ.get("ET_DATA_DIR") or os.path.join(SRC, "data")
def _load(name, default):
    try:
        with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default
CFG = _load("config.json", {})
ARTIGOS = _load("artigos.json", [])
PRODUTOS = _load("produtos.json", [])
MATERIAIS = _load("materiais.json", [])
IG = CFG.get("instagram", "https://instagram.com/encontrarastudo")
YT = CFG.get("youtube", "https://youtube.com/@encontrarastudo")
EMAIL = CFG.get("email", "contato@encontrarastudo.com.br")
PUB_DATE = "2026-10-28"
MOD_DATE = date.today().isoformat()
MOD_DATE_BR = date.today().strftime("%d/%m/%Y")
PERSON = {"@type":"Person","@id":BASE+"/#gustavo","name":"Gustavo Souza","jobTitle":"Catequista",
  "description":"Catequista há quase 20 anos, formado em Filosofia, Teologia e História, com especialização em Catequese.",
  "knowsAbout":["Catequese","Bíblia","Doutrina católica","Orações","Novenas"],
  "worksFor":{"@id":BASE+"/#org"},"url":BASE+"/sobre.html"}

def cta_block(prod=None):
    g = CFG.get("cta_gratis", {})
    # aceita um produto de produtos.json (nome/desc/link/preco) ou o cta_produto do config
    if prod:
        p = {"kicker": "Material recomendado", "titulo": prod.get("nome",""), "texto": prod.get("desc",""),
             "preco": prod.get("preco",""), "link": prod.get("link","#"), "botao": "Quero conhecer",
             "ext": prod.get("link","").startswith("http")}
    else:
        p = dict(CFG.get("cta_produto", {})); p["ext"] = str(p.get("link","")).startswith("http")
    preco = ('<span class="price">%s</span>' % p.get("preco","")) if p.get("preco") else ""
    tgt = ' target="_blank" rel="noopener"' if p.get("ext") else ""
    return ('''<div class="cta-stack">
    <div class="material reveal"><div class="ico"><img src="assets/logo-white.png" alt=""></div>
      <div><p class="k">%s</p><h3>%s</h3><p>%s</p></div>
      <a class="btn" href="%s">%s <span class="chev">&rarr;</span></a></div>
    <div class="material produto reveal"><div class="ico"><img src="assets/logo-white.png" alt=""></div>
      <div><p class="k">%s</p><h3>%s</h3><p>%s</p>%s</div>
      <a class="btn btn-gold" href="%s"%s>%s <span class="chev">&rarr;</span></a></div>
  </div>''' % (g.get("kicker",""), g.get("titulo",""), g.get("texto",""), g.get("link","guia.html"), g.get("botao","Baixar grátis"),
               p.get("kicker",""), p.get("titulo",""), p.get("texto",""), preco, p.get("link","#"), tgt, p.get("botao","Quero conhecer")))

def cta_inline(mat=None):
    g = CFG.get("cta_gratis", {})
    if mat:
        k, t, s, link, bot = "Material gratuito", mat.get("nome",""), mat.get("desc",""), mat.get("pagina","guia.html"), "Baixar grátis"
    else:
        k, t, s, link, bot = g.get("kicker",""), g.get("titulo",""), g.get("texto",""), g.get("link","guia.html"), g.get("botao","Baixar grátis")
    return ('<aside class="isca-banner"><div class="txt"><p class="k">%s</p><p class="t">%s</p>'
            '<p class="s">%s</p></div><a class="btn" href="%s">%s</a></aside>'
            % (k, t, s, link, bot))

FONTS = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Mulish:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">')

def head(title, desc, slug='', jsonld='', og_image=''):
    canonical = BASE + '/' + slug if slug else BASE + '/'
    img = (BASE + '/' + og_image) if og_image else (BASE + '/assets/logo-gold.png')
    card = 'summary_large_image' if og_image else 'summary'
    og = (('<link rel="canonical" href="%s">\n'
           '<link rel="alternate" hreflang="pt-br" href="%s">\n'
           '<meta name="robots" content="index,follow,max-image-preview:large">\n'
           '<meta name="theme-color" content="#211c26">\n'
           '<meta property="og:type" content="website">\n'
           '<meta property="og:site_name" content="Encontrarás Tudo">\n'
           '<meta property="og:locale" content="pt_BR">\n'
           '<meta property="og:title" content="%s">\n'
           '<meta property="og:description" content="%s">\n'
           '<meta property="og:url" content="%s">\n'
           '<meta property="og:image" content="%s">\n'
           '<meta name="twitter:card" content="%s">\n')
          % (canonical, canonical, title, desc, canonical, img, card))
    ld = ('<script type="application/ld+json">%s</script>\n' % jsonld) if jsonld else ''
    return ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s%s\n'
            '<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">\n'
            '<link rel="icon" type="image/png" sizes="256x256" href="assets/favicon.png">\n'
            '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">\n'
            '<link rel="stylesheet" href="assets/styles.css">\n%s</head>\n<body>\n'
            % (title, desc, og, FONTS, ld))

def nav(active):
    def a(key, href, label):
        cls = ' class="active"' if key == active else ''
        return '<a href="%s"%s>%s</a>' % (href, cls, label)
    _an = CFG.get("announce", {})
    announce = ('<div class="announce"><div class="wrap">%s &mdash; <a href="%s">%s &rarr;</a></div></div>'
                % (_an.get("texto","Formação católica com fé e razão"), _an.get("link","guia.html"), _an.get("label","saiba mais")))
    return (announce + '''
<header class="nav" id="nav">
  <div class="wrap">
    <a class="brand" href="index.html"><img src="assets/emblem-gold.png" alt="Encontrarás Tudo"><span class="bn">Encontrarás Tudo</span></a>
    <button class="menu-toggle" id="menuToggle" aria-label="Abrir menu" aria-expanded="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18" stroke-linecap="round"/></svg></button>
    <nav class="menu" id="menu">
      ''' + a('home','index.html','Home') + '\n      ' + a('sobre','sobre.html','Sobre')
      + '\n      ' + a('oracoes','oracoes.html','Orações') + '\n      ' + a('novenas','novenas.html','Novenas') + '\n      ' + a('blog','blog.html','Blog')
      + '\n      ' + a('ferramentas','ferramentas.html','Material e Ferramentas') + '\n      ' + a('contato','contato.html','Contato') + '''
      <a class="navcta" href="guia.html">Guia grátis</a>
    </nav>
  </div>
</header>
''')

FOOTER = '''<footer class="foot">
  <div class="wrap">
    <div class="lema">
      <div class="q">&ldquo;Buscai, e encontrareis.&rdquo;</div>
      <div class="r">Mateus 7,7</div>
    </div>
    <div class="foot-grid">
      <div class="foot-brand">
        <img src="assets/logo-gold.png" alt="Encontrar&aacute;s Tudo">
        <p>Forma&ccedil;&atilde;o cat&oacute;lica com f&eacute; e raz&atilde;o. Para crer com entendimento e defender a vida com caridade.</p>
        <div class="socials">
          <a href="https://instagram.com/encontrarastudo" aria-label="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></a>
          <a href="https://youtube.com/@encontrarastudo" aria-label="YouTube"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23 12s0-3.9-.5-5.6a2.8 2.8 0 0 0-2-2C18.8 4 12 4 12 4s-6.8 0-8.5.4a2.8 2.8 0 0 0-2 2C1 8.1 1 12 1 12s0 3.9.5 5.6a2.8 2.8 0 0 0 2 2C5.2 20 12 20 12 20s6.8 0 8.5-.4a2.8 2.8 0 0 0 2-2C23 15.9 23 12 23 12zM10 15.5v-7l6 3.5-6 3.5z"/></svg></a>
        </div>
      </div>
      <div class="foot-col"><h4>Geral</h4><ul>
        <li><a href="index.html">Home</a></li><li><a href="sobre.html">Sobre</a></li><li><a href="blog.html">Blog</a></li></ul></div>
      <div class="foot-col"><h4>Conte&uacute;dos</h4><ul>
        <li><a href="oracoes.html">Ora&ccedil;&otilde;es</a></li><li><a href="index.html#materiais">Materiais</a></li><li><a href="index.html#newsletter">Newsletter</a></li></ul></div>
      <div class="foot-col"><h4>Contato</h4><ul>
        <li><a href="contato.html">Fale comigo</a></li><li><a href="https://instagram.com/encontrarastudo">@encontrarastudo</a></li><li><a href="mailto:contato@encontrarastudo.com.br">E-mail</a></li></ul></div>
    </div>
    <div class="foot-legal"><span>&copy; 2026 Encontrar&aacute;s Tudo. Todos os direitos reservados.</span><span>F&eacute; e Raz&atilde;o</span></div>
  </div>
</footer>
<script src="assets/site.js"></script>
</body>
</html>'''
# Rodapé e config do site vêm do config.json (editável pelo painel)
CFG_JS = '<script>window.ET_CFG=%s;</script>' % json.dumps(
    {"listUuid": CFG.get("newsletter_uuid",""), "listmonk": CFG.get("listmonk_url","")}, ensure_ascii=False)
FOOTER = (FOOTER
    .replace("https://instagram.com/encontrarastudo", IG)
    .replace("https://youtube.com/@encontrarastudo", YT)
    .replace("contato@encontrarastudo.com.br", EMAIL)
    .replace('<script src="assets/site.js">', CFG_JS + '\n<script src="assets/site.js">'))

def page(fname, title, desc, active, body, jsonld='', og_image=''):
    html = head(title, desc, fname, jsonld, og_image) + nav(active) + body + FOOTER
    with open(os.path.join(OUT, fname), 'w', encoding='utf-8') as f:
        f.write(html)
    print("wrote", fname, len(html), "bytes")

def phero(eyebrow, h1, sub=""):
    s = '<p>%s</p>' % sub if sub else ''
    return ('<section class="page-hero"><img class="emblem-bg" src="assets/emblem-gold.png" alt="">'
            '<div class="wrap"><p class="eyebrow">%s</p><h1>%s</h1>%s</div></section>\n' % (eyebrow, h1, s))

# ============ BLOG + ARTIGOS (dados em data/artigos.json) ============
import re as _re, html as _htmlmod
def _txt(s):
    s = _re.sub(r"<[^>]+>", " ", s or ""); s = _htmlmod.unescape(s)
    return _re.sub(r"\s+", " ", s).strip()

def bcover(img, cat):
    return ('<div class="cover has-img"><img class="thumb" src="assets/img/%s.webp" alt="" loading="lazy">'
            '<span class="cat">%s</span></div>' % (img, cat))

def article_jsonld(a, canonical, img):
    org = {"@type":["Organization","EducationalOrganization"],"@id":BASE+"/#org","name":"Encontrarás Tudo",
      "url":BASE+"/","logo":BASE+"/assets/logo-gold.png","sameAs":[IG,YT],"foundingDate":"2019","founder":{"@id":BASE+"/#gustavo"}}
    main = {"@type":"Article","headline":_txt(a["titulo"]),"description":_txt(a.get("dek","")),
      "image":BASE+"/"+img,"inLanguage":"pt-BR","url":canonical,"mainEntityOfPage":canonical,
      "author":{"@id":BASE+"/#gustavo"},"publisher":{"@id":BASE+"/#org"},
      "datePublished":a.get("data") or PUB_DATE,"dateModified":MOD_DATE,"articleSection":a.get("categoria","")}
    g = [org, PERSON,
      {"@type":"WebSite","@id":BASE+"/#site","url":BASE+"/","name":"Encontrarás Tudo","inLanguage":"pt-BR","publisher":{"@id":BASE+"/#org"}},
      main,
      {"@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Início","item":BASE+"/"},
        {"@type":"ListItem","position":2,"name":"Blog","item":BASE+"/blog.html"},
        {"@type":"ListItem","position":3,"name":_txt(a["titulo"]),"item":canonical}]}]
    return json.dumps({"@context":"https://schema.org","@graph":g}, ensure_ascii=False)

# ---- Recomendação automática de produto por artigo ----
import unicodedata as _ud
def _norm(s):
    s = _txt(s or "").lower()
    return "".join(c for c in _ud.normalize("NFD", s) if _ud.category(c) != "Mn")

PROD_BY_IMG = {p.get("img"): p for p in PRODUTOS}

def best_product(a):
    """Escolhe o produto mais relacionado ao artigo. Override: a['produto'] = chave da img."""
    key = a.get("produto")
    if key and key in PROD_BY_IMG:
        return PROD_BY_IMG[key]
    if not PRODUTOS:
        return None
    text = _norm(" ".join([a.get("titulo",""), a.get("dek",""), a.get("categoria",""),
                           " ".join(a.get("tags", [])), a.get("body","")]))
    best, score = None, 0
    for p in PRODUTOS:
        s = sum(text.count(k) for k in p.get("tags", []))
        if s > score:
            best, score = p, s
    # fallback: produto carro-chefe (Mapas Mentais) ou o primeiro
    return best or PROD_BY_IMG.get("mapas-mentais") or PRODUTOS[0]

def prod_cta(p):
    """Banner de produto para o meio do artigo."""
    if not p:
        return ""
    preco = ('<span class="price">%s</span>' % p["preco"]) if p.get("preco") else ""
    thumb = ('<img class="prod-thumb" src="assets/img/%s.webp" alt="" loading="lazy">' % p["img"]) if p.get("img") else ""
    ext = ' target="_blank" rel="noopener"' if str(p.get("link","")).startswith("http") else ""
    return ('<aside class="isca-banner produto">%s<div class="txt">'
            '<p class="k">Material recomendado</p><p class="t">%s</p>'
            '<p class="s">%s %s</p></div>'
            '<a class="btn btn-gold" href="%s"%s>Quero conhecer <span class="chev">&rarr;</span></a></aside>'
            % (thumb, p["nome"], p.get("desc",""), preco, p.get("link","#"), ext))

def insert_mid(body_html, bloco):
    """Insere um bloco após o parágrafo central do artigo (ou usa [[PRODUTO]])."""
    if not bloco:
        return body_html
    if "[[PRODUTO]]" in body_html:
        return body_html.replace("[[PRODUTO]]", bloco)
    ends = [m.end() for m in _re.finditer(r"</p>", body_html)]
    if len(ends) < 3:
        return body_html + "\n" + bloco
    pos = ends[len(ends) // 2]
    return body_html[:pos] + "\n" + bloco + "\n" + body_html[pos:]

def best_material(a):
    """Material (isca) mais relacionado ao artigo. None se nenhum tema casar."""
    if not MATERIAIS:
        return None
    by_slug = {m.get("slug"): m for m in MATERIAIS}
    key = a.get("material")
    if key and key in by_slug:
        return by_slug[key]
    text = _norm(" ".join([a.get("titulo",""), a.get("dek",""), a.get("categoria",""),
                           " ".join(a.get("tags", [])), a.get("body","")]))
    best, score = None, 0
    for m in MATERIAIS:
        s = sum(text.count(_norm(k)) for k in m.get("tags", []))
        if s > score:
            best, score = m, s
    return best   # None quando o assunto não casa com nenhum material

def insert_early(body_html, bloco):
    """Insere um bloco logo após o 2º parágrafo (bom para captura de isca)."""
    if not bloco:
        return body_html
    ends = [m.end() for m in _re.finditer(r"</p>", body_html)]
    if len(ends) < 3:
        return bloco + "\n" + body_html
    pos = ends[min(2, len(ends) - 1)]
    return body_html[:pos] + "\n" + bloco + "\n" + body_html[pos:]

def render_artigo(a, fname=None):
    fname = fname or (a["slug"] + ".html")
    canon = BASE + "/" + fname
    img = "assets/img/%s.webp" % a.get("img", "eucaristia")
    tags = "".join('<span class="tag">%s</span>' % t for t in a.get("tags", []))
    meta_line = " &middot; ".join(x for x in [a.get("data_br",""), a.get("leitura","")] if x)
    prod = best_product(a)
    mat = best_material(a)
    body_html = (a.get("body","") or "")
    if "[[CTA]]" in body_html:
        body_html = body_html.replace("[[CTA]]", cta_inline(mat))   # isca onde o autor marcou
    elif mat:
        body_html = insert_early(body_html, cta_inline(mat))        # tema casou: isca no início
    body_html = insert_mid(body_html, prod_cta(prod))   # 1 produto no meio, o mais relevante
    byline = ('<p class="art-byline">Por <a href="sobre.html">%s</a> &middot; <time datetime="%s">%s</time></p>'
              % (a.get("autor","Gustavo Souza"), a.get("data",""), a.get("data_br","")))
    body = ('<article class="article wrap"><div class="tags">%s</div><h1>%s</h1>'
            '<p class="dek">%s</p>%s<p class="art-meta">%s</p>'
            '<div class="body">%s\n%s</div></article>'
            % (tags, a["titulo"], a.get("dek",""), byline, meta_line, body_html, cta_block(prod)))
    jd = article_jsonld(a, canon, img)
    page(fname, _txt(a["titulo"]) + " — Encontrarás Tudo", _txt(a.get("dek","")), "blog", body, jd, og_image=img)

def blog_card(a):
    cov = bcover(a.get("img","eucaristia"), a.get("categoria",""))
    if a.get("status") == "publicado":
        return ('<a class="post live reveal" href="%s.html">%s<div class="pbody"><h3>%s</h3>'
                '<p class="ex">%s</p><div class="meta"><span class="d">%s</span><span>Ler &rarr;</span></div></div></a>'
                % (a["slug"], cov, a["titulo"], a.get("resumo",""), a.get("data_br","")))
    return ('<div class="post reveal">%s<div class="pbody"><h3>%s</h3><p class="ex">%s</p>'
            '<div class="meta"><span>Em prepara&ccedil;&atilde;o</span><span class="soon">Em breve</span></div></div></div>'
            % (cov, a["titulo"], a.get("resumo","")))

_pub = [a for a in ARTIGOS if a.get("status") == "publicado"]
for _a in _pub:
    render_artigo(_a)
if _pub:
    render_artigo(_pub[0], fname="artigo.html")   # alias p/ a URL antiga

blog_body = phero("Blog", "&Uacute;ltimos artigos", "Doutrina, santos, apolog&eacute;tica e vida &mdash; com f&eacute; e raz&atilde;o.") + (
  '<section class="section light"><div class="wrap"><div class="grid">%s</div></div></section>'
  % "".join(blog_card(a) for a in ARTIGOS))
page("blog.html", "Blog &mdash; Encontrar&aacute;s Tudo",
     "Artigos de forma&ccedil;&atilde;o cat&oacute;lica: doutrina, santos, apolog&eacute;tica e vida.", "blog", blog_body)

_ARTIGO_ANTIGO = '''
<div class="body">
    <p>Existe uma frase que resume os dois lados do debate sobre o aborto. E o impressionante &eacute; que &eacute; a mesma frase, dita de dois jeitos que n&atilde;o poderiam ser mais opostos.</p>
    <p class="pull">A frase &eacute;: &ldquo;este &eacute; o meu corpo&rdquo;.</p>
    <p>Quando o movimento a favor do aborto diz &ldquo;este &eacute; o meu corpo&rdquo;, o que est&aacute; dizendo &eacute;: <em>eu decido. &Eacute; meu, eu mando. Mesmo que outra vida tenha de morrer para isso.</em></p>
    <p>Quando Cristo diz &ldquo;este &eacute; o meu corpo&rdquo;, na noite da &Uacute;ltima Ceia, Ele diz exatamente o contr&aacute;rio: &ldquo;Isto &eacute; o meu corpo, que &eacute; dado por v&oacute;s&rdquo; (Lc 22,19). Ou seja: <em>eu me entrego. Eu morro para que voc&ecirc; viva.</em></p>
    <p>A mesma frase. Dois mundos. E &eacute; a&iacute; que mora o cora&ccedil;&atilde;o da posi&ccedil;&atilde;o cat&oacute;lica sobre o aborto, muito antes de qualquer discuss&atilde;o pol&iacute;tica.</p>
    <h2>Duas l&oacute;gicas que n&atilde;o cabem no mesmo cora&ccedil;&atilde;o</h2>
    <p>Repare no que cada vers&atilde;o da frase carrega. A l&oacute;gica do aborto &eacute;: <em>voc&ecirc; morre para que eu viva como quero.</em> A vida que est&aacute; come&ccedil;ando &eacute; tratada como obst&aacute;culo ao projeto de quem j&aacute; est&aacute; aqui. A l&oacute;gica de Cristo &eacute; o espelho invertido disso: <em>eu me entrego para que voc&ecirc; tenha vida.</em> N&atilde;o &eacute; o mais forte eliminando o mais fr&aacute;gil; &eacute; o mais forte se doando pelo mais fr&aacute;gil. A cruz &eacute; isso. A Eucaristia &eacute; isso, repetido em cada missa.</p>
    <p>Por isso o aborto n&atilde;o &eacute; apenas um erro moral entre outros: &eacute; uma invers&atilde;o direta da l&oacute;gica da Eucaristia. &Eacute; pegar o gesto mais sagrado do cristianismo, o corpo entregue por amor, e vir&aacute;-lo de cabe&ccedil;a para baixo.</p>
    <p>Quando voc&ecirc; enxerga isso, o debate muda de altura. N&atilde;o se trata mais s&oacute; de &ldquo;sou contra&rdquo; ou &ldquo;sou a favor&rdquo;. Trata-se de qual l&oacute;gica governa a sua vida: a da entrega ou a da imposi&ccedil;&atilde;o.</p>
    <h2>N&atilde;o &eacute; s&oacute; f&eacute;: a raz&atilde;o tamb&eacute;m diz o mesmo</h2>
    <p>Algu&eacute;m dir&aacute;: &ldquo;isso &eacute; lindo para quem cr&ecirc;, mas e quem n&atilde;o cr&ecirc;?&rdquo;. Justo. E aqui a posi&ccedil;&atilde;o cat&oacute;lica mostra a sua for&ccedil;a: ela tamb&eacute;m se sustenta na raz&atilde;o e nos dados.</p>
    <p>Comece pela biologia. A pergunta &ldquo;quando come&ccedil;a uma vida humana?&rdquo; n&atilde;o &eacute;, antes de tudo, religiosa: &eacute; cient&iacute;fica. E entre os cientistas h&aacute; consenso. Numa pesquisa conduzida na Universidade de Chicago com 5.502 bi&oacute;logos de 1.058 institui&ccedil;&otilde;es, <strong>95% afirmaram que a vida de um ser humano come&ccedil;a na fertiliza&ccedil;&atilde;o</strong> (Jacobs, 2018). N&atilde;o foram te&oacute;logos: foram bi&oacute;logos, de todo o espectro pol&iacute;tico e religioso.</p>
    <p>O fil&oacute;sofo Peter Kreeft resume o racioc&iacute;nio em tr&ecirc;s passos: (1) &eacute; errado matar deliberadamente um ser humano inocente; (2) o aborto mata deliberadamente um ser humano inocente; (3) logo, o aborto &eacute; errado. Nenhuma premissa precisa da B&iacute;blia para ser verdadeira.</p>
    <p>E se algu&eacute;m disser &ldquo;mas ainda n&atilde;o &eacute; uma <em>pessoa</em>&rdquo;, a resposta &eacute; uma pergunta: voc&ecirc; tem certeza? Se voc&ecirc; n&atilde;o tem certeza se h&aacute; uma pessoa ali, e age assim mesmo, isso &eacute; como atirar no mato que se mexe sem checar se &eacute; um animal ou um companheiro de ca&ccedil;a. A d&uacute;vida n&atilde;o libera. A d&uacute;vida obriga a n&atilde;o matar.</p>
    <aside class="isca-banner"><div class="txt"><p class="k">Guia gratuito</p><p class="t">O Cat&oacute;lico que Defende a Vida</p><p class="s">As 7 obje&ccedil;&otilde;es mais comuns e como responder a cada uma, com f&eacute; e raz&atilde;o, cada resposta com sua fonte.</p></div><a class="btn" href="guia.html">Baixar gr&aacute;tis</a></aside>
    <h2>Ser pr&oacute;-vida &eacute; mais do que dizer &ldquo;n&atilde;o&rdquo;</h2>
    <p>E aqui est&aacute; a parte que mais distingue o cat&oacute;lico maduro: ser contra o aborto tamb&eacute;m significa acolher, ajudar e proteger concretamente a m&atilde;e e a crian&ccedil;a. A vis&atilde;o cat&oacute;lica n&atilde;o vira as costas para a mulher. Ela abra&ccedil;a as duas vidas.</p>
    <p>Isso n&atilde;o &eacute; discurso bonito: &eacute; resposta ao problema real. Quando se pergunta &agrave;s mulheres por que buscaram um aborto, as raz&otilde;es que mais aparecem n&atilde;o s&atilde;o &ldquo;ego&iacute;smo&rdquo;. S&atilde;o desamparo e medo. Na maior pesquisa sobre o tema, 74% disseram que ter um filho naquele momento interferiria no trabalho ou nos estudos, e 73% afirmaram n&atilde;o ter condi&ccedil;&otilde;es de sustentar um filho (Finer et al., 2005). Boa parte dos abortos nasce de uma mulher que se sente sozinha e sem sa&iacute;da.</p>
    <p>Se a Eucaristia &eacute; &ldquo;eu me entrego por voc&ecirc;&rdquo;, ent&atilde;o a defesa da vida n&atilde;o pode ser s&oacute; um &ldquo;n&atilde;o&rdquo; na boca; tem que ser um &ldquo;sim&rdquo; nas m&atilde;os. Sim &agrave; mulher gr&aacute;vida e assustada. Sim &agrave; m&atilde;e sozinha. E sim, tamb&eacute;m, &agrave; mulher que j&aacute; abortou e carrega essa ferida: para ela, a resposta da Igreja n&atilde;o &eacute; condena&ccedil;&atilde;o, &eacute; miseric&oacute;rdia e cura.</p>
    <p>Quem aponta o dedo mas n&atilde;o estende a m&atilde;o ainda n&atilde;o entendeu a l&oacute;gica que diz defender. Porque a cruz nunca foi um dedo apontado. Foi um corpo aberto.</p>
    <aside class="isca-banner"><div class="txt"><p class="k">Antes de ir &middot; gr&aacute;tis</p><p class="t">Leve as respostas com voc&ecirc;</p><p class="s">Baixe o guia com as 7 obje&ccedil;&otilde;es respondidas, para ter &agrave; m&atilde;o quando o assunto aparecer.</p></div><a class="btn" href="guia.html">Baixar o guia</a></aside>
    <aside class="isca-banner produto"><div class="txt"><p class="k">Para aprofundar</p><p class="t">Mapas Mentais da B&iacute;blia</p><p class="s">73 mapas que resumem a B&iacute;blia inteira, livro por livro &mdash; para catequistas e para quem quer estudar a Palavra com clareza. <span class="price">R$ 47</span></p></div><a class="btn btn-gold" href="__LINK_MAPAS_MENTAIS__">Quero conhecer</a></aside>
    <p class="sources"><b>Fontes</b>Lc 22,19; Jr 1,5; Catecismo da Igreja Cat&oacute;lica &sect;2270&ndash;2275; <em>Evangelium Vitae</em> (Jo&atilde;o Paulo II, 1995); Jacobs, S. A., &ldquo;Biologists&rsquo; Consensus on &lsquo;When Life Begins&rsquo;&rdquo; (SSRN, 2018); Finer, L. et al. (2005); Peter Kreeft, <em>Three Approaches to Abortion</em>.</p>
  </div>
</article>
'''

# ============ GUIA (landing) ============
guia_body = '''
<main class="wrap">
  <div class="land">
    <section class="pitch">
      <p class="eyebrow">Guia gratuito</p>
      <h1>Da pr&oacute;xima vez que te disserem &ldquo;&eacute; o seu corpo&rdquo;, voc&ecirc; vai saber responder.</h1>
      <p class="sub">As 7 obje&ccedil;&otilde;es mais comuns sobre o aborto e como responder a cada uma com raz&atilde;o e caridade &mdash; cada resposta com a sua fonte.</p>
      <ul class="receive">
        <li>As 7 obje&ccedil;&otilde;es que todo cat&oacute;lico ouve, com a resposta pronta para cada uma.</li>
        <li>Argumentos de raz&atilde;o (que funcionam at&eacute; com quem n&atilde;o tem f&eacute;) e de f&eacute;.</li>
        <li>As fontes de cada resposta: Catecismo, Escritura e documentos da Igreja.</li>
        <li>A chave que muda tudo: por que o aborto inverte a l&oacute;gica da Eucaristia.</li>
      </ul>
    </section>
    <section class="card" id="card">
      <form id="form" novalidate>
        <p class="k">Receba no seu e-mail</p>
        <h2>O Cat&oacute;lico que Defende a Vida</h2>
        <p class="coverln">Guia completo em PDF, gratuito. Enviamos o link assim que voc&ecirc; confirmar.</p>
        <label for="nome">Seu nome</label>
        <input id="nome" name="name" type="text" autocomplete="name" placeholder="Como quer ser chamado(a)">
        <label for="email">Seu melhor e-mail</label>
        <input id="email" name="email" type="email" autocomplete="email" placeholder="voce@exemplo.com">
        <p class="err" id="err" role="alert"></p>
        <button class="btn" type="submit">Quero receber o guia gr&aacute;tis</button>
        <p class="consent">Enviamos s&oacute; conte&uacute;do bom, no seu tempo. Cancele quando quiser, sem spam. Seus dados ficam seguros (LGPD).</p>
      </form>
      <div class="done" id="done">
        <div class="mark">&#10022;</div>
        <h2>Pronto!</h2>
        <p>Seu guia est&aacute; pronto. Clique abaixo para baixar agora:</p>
        <a class="btn btn-gold" href="assets/materiais/guia-defende-a-vida.pdf" target="_blank" rel="noopener" download>Baixar o guia (PDF) &darr;</a>
        <p class="consent" style="margin-top:14px">Enviamos o link tamb&eacute;m para o seu e-mail. <strong>Confirme a inscri&ccedil;&atilde;o</strong> para receber os pr&oacute;ximos materiais.</p>
      </div>
    </section>
  </div>
</main>
'''
page("guia.html", "O Cat&oacute;lico que Defende a Vida &mdash; Guia gr&aacute;tis",
     "Guia gratuito: as 7 obje&ccedil;&otilde;es mais comuns sobre o aborto e como responder a cada uma.", "", guia_body)

# ============ FERRAMENTAS (produtos, dados em data/produtos.json) ============
def prod_card(p):
    badge = ('<span class="cat">%s</span>' % p["badge"]) if p.get("badge") else ""
    if p.get("img"):
        cover = ('<div class="cover has-img prod"><img class="thumb" src="assets/img/%s.webp" alt="%s" loading="lazy">%s</div>'
                 % (p["img"], p["nome"], badge))
    else:
        cover = '<div class="cover %s"><img class="wm" src="assets/emblem-gold.png" alt="">%s</div>' % (p.get("cor", "c1"), badge)
    return ('<a class="post live reveal" href="%s" target="_blank" rel="noopener">%s'
            '<div class="pbody"><h3>%s</h3><p class="ex">%s</p>'
            '<div class="meta"><span class="d">Acessar</span><span>&rarr;</span></div></div></a>'
            % (p["link"], cover, p["nome"], p.get("desc", "")))
ferr_body = phero("Materiais", "Material e Ferramentas",
    "Tudo o que produzimos para ajudar voc&ecirc; a crescer na f&eacute; e a ensinar com seguran&ccedil;a.") + (
  '<section class="section light"><div class="wrap"><div class="grid">%s</div>'
  '<p style="text-align:center;color:var(--ink-soft);margin-top:2rem">Tem alguma d&uacute;vida sobre os materiais? '
  '<a href="contato.html">Fale comigo</a>.</p></div></section>' % "".join(prod_card(p) for p in PRODUTOS))
page("ferramentas.html", "Material e Ferramentas &mdash; Encontrar&aacute;s Tudo",
     "Os materiais do Encontrar&aacute;s Tudo: Mapas Mentais da B&iacute;blia, Encontro Pronto, atividades b&iacute;blicas para crian&ccedil;as e o aplicativo Didake.",
     "ferramentas", ferr_body)

# ============ SOBRE ============
sobre_body = phero("Sobre", "Buscar com seriedade, encontrar com f&eacute;", "O que &eacute; o Encontrar&aacute;s Tudo e por que ele existe.") + '''
<section class="section light">
  <div class="wrap">
    <div class="prose reveal">
      <p class="lead-in">O <strong>Encontrar&aacute;s Tudo</strong> nasceu de uma convic&ccedil;&atilde;o simples: a f&eacute; cat&oacute;lica n&atilde;o tem medo de perguntas. Quem busca com honestidade encontra &mdash; e encontra tudo em Cristo.</p>
      <p>Desde 2019, o projeto leva forma&ccedil;&atilde;o cat&oacute;lica a mais de 50 mil pessoas no Instagram <a href="https://instagram.com/encontrarastudo">@encontrarastudo</a> e no YouTube. A proposta &eacute; explicar a doutrina com clareza, unindo duas coisas que muita gente acha que brigam entre si: <strong>f&eacute; e raz&atilde;o</strong>.</p>
      <h2>No que acreditamos</h2>
      <div class="values">
        <div class="value"><div class="vi">&#10022;</div><h3>F&eacute;</h3><p>Fi&eacute;is ao ensino da Igreja: Escritura, Tradi&ccedil;&atilde;o e Magist&eacute;rio. Sem atalhos, sem inven&ccedil;&otilde;es.</p></div>
        <div class="value"><div class="vi">&#10022;</div><h3>Raz&atilde;o</h3><p>A f&eacute; cat&oacute;lica &eacute; razo&aacute;vel. Argumentos claros, que convencem tamb&eacute;m quem ainda n&atilde;o cr&ecirc;.</p></div>
        <div class="value"><div class="vi">&#10022;</div><h3>Caridade</h3><p>Firmeza no argumento, caridade com a pessoa. O inimigo &eacute; o erro, nunca quem erra.</p></div>
      </div>
    </div>
  </div>
</section>
<section class="section surface">
  <div class="wrap">
    <div class="pessoa reveal">
      <div class="pessoa-foto foto-real"><img src="assets/img/gustavo.jpg" alt="Gustavo Souza &mdash; Encontrar&aacute;s Tudo"></div>
      <div class="pessoa-txt">
        <p class="eyebrow">A pessoa por tr&aacute;s</p>
        <h2>Prazer, eu sou Gustavo Souza</h2>
        <p>H&aacute; quase <strong>20 anos</strong> estou na catequese. Passei por todas as etapas, de crian&ccedil;as a adultos, e hoje sou <strong>catequista de adultos</strong>, com uma metodologia de inspira&ccedil;&atilde;o catecumenal &mdash; no esp&iacute;rito das primeiras comunidades crist&atilde;s, quando liturgia e catequese caminhavam juntas.</p>
        <p>Tamb&eacute;m j&aacute; formei e acompanhei outros catequistas; por isso conhe&ccedil;o por dentro as dores dessa voca&ccedil;&atilde;o. Os <strong>Mapas Mentais da B&iacute;blia</strong> nasceram dessa estrada: fi&eacute;is ao Catecismo e &agrave; Tradi&ccedil;&atilde;o da Igreja.</p>
        <ul class="creds">
          <li>Forma&ccedil;&atilde;o em Filosofia, Teologia e Hist&oacute;ria</li>
          <li>Especializa&ccedil;&atilde;o em Catequese</li>
          <li>Quase 20 anos como catequista &mdash; de crian&ccedil;as a adultos</li>
          <li>J&aacute; formou e acompanhou outros catequistas</li>
        </ul>
      </div>
    </div>
  </div>
</section>
<section class="section dark">
  <div class="wrap quote-band reveal">
    <img class="emblem-bg" src="assets/emblem-gold.png" alt="">
    <blockquote>&ldquo;Buscai, e encontrareis.&rdquo;</blockquote>
    <p class="ref">Mateus 7,7</p>
    <p>Comece agora, de gra&ccedil;a: baixe o guia do cat&oacute;lico que defende a vida e receba a forma&ccedil;&atilde;o no seu e-mail.</p>
    <div class="actions"><a class="btn btn-gold" href="guia.html">Baixar o guia gratuito <span class="chev">&rarr;</span></a></div>
  </div>
</section>
'''
page("sobre.html", "Sobre &mdash; Encontrar&aacute;s Tudo",
     "O que &eacute; o Encontrar&aacute;s Tudo: forma&ccedil;&atilde;o cat&oacute;lica com f&eacute; e raz&atilde;o.", "sobre", sobre_body)

# ============ ORA&Ccedil;&Otilde;ES ============
oracoes_body = phero("Ora&ccedil;&otilde;es", "Ora&ccedil;&otilde;es para alimentar a sua f&eacute;", "Uma sele&ccedil;&atilde;o para rezar todos os dias e aproximar-se de Deus.") + '''
<section class="section light">
  <div class="wrap">
    <div class="prayer-feat reveal">
      <div class="pf-img"><img src="assets/emblem-gold.png" alt=""></div>
      <div class="pf-body">
        <span class="pill">Prote&ccedil;&atilde;o</span>
        <h2>Ora&ccedil;&atilde;o a S&atilde;o Miguel Arcanjo</h2>
        <p class="pt">&ldquo;S&atilde;o Miguel Arcanjo, defendei-nos no combate, sede o nosso aux&iacute;lio contra as maldades e ciladas do demônio. Ordene-lhe Deus, instantemente o pedimos. E v&oacute;s, pr&iacute;ncipe da mil&iacute;cia celeste, pela virtude divina, precipitai no inferno a Satan&aacute;s e aos outros esp&iacute;ritos malignos que andam pelo mundo para perder as almas. Am&eacute;m.&rdquo;</p>
      </div>
    </div>
  </div>
</section>
<section class="section surface">
  <div class="wrap">
    <div class="section-head reveal"><div><p class="eyebrow">Ora&ccedil;&otilde;es recomendadas</p><h2>Para rezar todos os dias</h2></div></div>
    <div class="prayer-list">
      <div class="prayer reveal"><p class="pk">Fundamental</p><h3>Pai-Nosso</h3><p>A ora&ccedil;&atilde;o que o pr&oacute;prio Jesus ensinou. &ldquo;Pai nosso que estais nos c&eacute;us, santificado seja o vosso nome...&rdquo;</p></div>
      <div class="prayer reveal"><p class="pk">Mariana</p><h3>Ave-Maria</h3><p>A sauda&ccedil;&atilde;o do anjo e de Isabel a Maria. &ldquo;Ave Maria, cheia de gra&ccedil;a, o Senhor &eacute; convosco...&rdquo;</p></div>
      <div class="prayer reveal"><p class="pk">Louvor</p><h3>Gl&oacute;ria ao Pai</h3><p>&ldquo;Gl&oacute;ria ao Pai, ao Filho e ao Esp&iacute;rito Santo, como era no princ&iacute;pio, agora e sempre. Am&eacute;m.&rdquo;</p></div>
      <div class="prayer reveal"><p class="pk">Diária</p><h3>Ângelus</h3><p>Rezado ao meio-dia, recorda a Encarna&ccedil;&atilde;o. &ldquo;O Anjo do Senhor anunciou a Maria...&rdquo;</p></div>
      <div class="prayer reveal"><p class="pk">Esp&iacute;rito Santo</p><h3>Vinde, Esp&iacute;rito Santo</h3><p>&ldquo;Vinde, Esp&iacute;rito Santo, enchei os cora&ccedil;&otilde;es dos vossos fi&eacute;is e acendei neles o fogo do vosso amor.&rdquo;</p></div>
      <div class="prayer reveal"><p class="pk">Devo&ccedil;&atilde;o</p><h3>O Santo Ter&ccedil;o</h3><p>A medita&ccedil;&atilde;o dos mist&eacute;rios da vida de Cristo com Maria. Uma escola de ora&ccedil;&atilde;o para todos os dias.</p></div>
    </div>
  </div>
</section>
<section class="section light">
  <div class="wrap"><div class="news news-inner reveal">
    <div><p class="eyebrow">Receba no seu e-mail</p><h2>Ora&ccedil;&otilde;es e forma&ccedil;&atilde;o, no seu tempo</h2><p class="lead">Materiais selecionados para alimentar a sua f&eacute; e devo&ccedil;&atilde;o. Sem spam, cancele quando quiser.</p></div>
    <div><form class="nl-form" id="nlForm" novalidate>
      <input id="nlNome" type="text" name="name" placeholder="Seu nome" autocomplete="name" aria-label="Seu nome">
      <input id="nlEmail" type="email" name="email" placeholder="Seu melhor e-mail" autocomplete="email" aria-label="Seu e-mail">
      <button class="btn" type="submit">Quero receber</button></form>
      <p class="nl-note">Seus dados ficam seguros (LGPD).</p>
      <p class="nl-done" id="nlDone">&#10022; Pronto! Confira seu e-mail para confirmar a inscri&ccedil;&atilde;o.</p></div>
  </div></div>
</section>
'''
page("oracoes.html", "Ora&ccedil;&otilde;es &mdash; Encontrar&aacute;s Tudo",
     "Ora&ccedil;&otilde;es cat&oacute;licas para rezar todos os dias e alimentar a f&eacute;.", "oracoes", oracoes_body)

# ============ CONTATO ============
contato_body = phero("Contato", "Fale comigo", "D&uacute;vidas, pedidos de ora&ccedil;&atilde;o ou uma palavra: estou por aqui.") + '''
<section class="section light">
  <div class="wrap">
    <div class="contact-grid">
      <a class="contact-card reveal" href="https://instagram.com/encontrarastudo">
        <div class="ci"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></div>
        <h3>Instagram</h3><p>O dia a dia da forma&ccedil;&atilde;o, em primeira m&atilde;o.</p><span class="val">@encontrarastudo</span>
      </a>
      <a class="contact-card reveal" href="mailto:contato@encontrarastudo.com.br">
        <div class="ci"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg></div>
        <h3>E-mail</h3><p>Para contato direto e parcerias.</p><span class="val">contato@encontrarastudo.com.br</span>
      </a>
      <a class="contact-card reveal" href="https://youtube.com/@encontrarastudo">
        <div class="ci"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M23 12s0-3.9-.5-5.6a2.8 2.8 0 0 0-2-2C18.8 4 12 4 12 4s-6.8 0-8.5.4a2.8 2.8 0 0 0-2 2C1 8.1 1 12 1 12s0 3.9.5 5.6a2.8 2.8 0 0 0 2 2C5.2 20 12 20 12 20s6.8 0 8.5-.4a2.8 2.8 0 0 0 2-2C23 15.9 23 12 23 12zM10 15.5v-7l6 3.5-6 3.5z"/></svg></div>
        <h3>YouTube</h3><p>V&iacute;deos e forma&ccedil;&atilde;o em profundidade.</p><span class="val">@encontrarastudo</span>
      </a>
    </div>
  </div>
</section>
<section class="section surface">
  <div class="wrap narrow">
    <div class="section-head reveal"><div><p class="eyebrow">Mensagem</p><h2>Deixe a sua mensagem</h2></div></div>
    <div class="card reveal" id="ctCard" style="position:static">
      <form id="ctForm" novalidate>
        <label for="ctNome">Seu nome</label>
        <input id="ctNome" type="text" placeholder="Como quer ser chamado(a)" autocomplete="name">
        <label for="ctEmail">Seu e-mail</label>
        <input id="ctEmail" type="email" placeholder="voce@exemplo.com" autocomplete="email">
        <label for="ctMsg">Mensagem</label>
        <input id="ctMsg" type="text" placeholder="Escreva aqui...">
        <button class="btn" type="submit">Enviar mensagem</button>
        <p class="consent">Respondo assim que poss&iacute;vel. Seus dados ficam seguros (LGPD).</p>
      </form>
      <div class="done" id="ctDone"><div class="mark">&#10022;</div><h2>Mensagem enviada!</h2><p>Obrigado por escrever. Respondo assim que poss&iacute;vel.</p></div>
    </div>
  </div>
</section>
'''
page("contato.html", "Contato &mdash; Encontrar&aacute;s Tudo",
     "Fale com o Encontrar&aacute;s Tudo: Instagram, e-mail e YouTube.", "contato", contato_body)

print("OK")
