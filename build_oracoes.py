# -*- coding: utf-8 -*-
# Gera páginas de orações e novenas (textos tradicionais) + hubs + sitemap,
# reutilizando os helpers de build_pages (que regenera as páginas-base com nav + SEO).
import os, json, re
import html as _html
from datetime import date
import build_pages as bp

PUB_DATE = "2026-10-28"
MOD_DATE = date.today().isoformat()
MOD_DATE_BR = date.today().strftime("%d/%m/%Y")

def _plain(s):
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = _html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

PERSON = {"@type":"Person","@id":bp.BASE+"/#gustavo","name":"Gustavo Souza","jobTitle":"Catequista",
  "description":"Catequista há quase 20 anos, formado em Filosofia, Teologia e História, com especialização em Catequese.",
  "knowsAbout":["Catequese","Bíblia","Doutrina católica","Orações","Novenas"],
  "worksFor":{"@id":bp.BASE+"/#org"},"url":bp.BASE+"/sobre.html"}

OUT = bp.OUT
BASE = bp.BASE
page = bp.page
phero = bp.phero
IMG = "assets/img"

# Itens cujo texto tem variantes populares e que o Gustavo deve conferir com a
# fonte de confiança dele antes de publicar (impresso no console ao gerar).
REVIEW = []

def jsonld(name, desc, canonical, crumbs, img=None, about=None, kind="CreativeWork", faqs=None):
    org = {"@type":["Organization","EducationalOrganization"],"@id":BASE+"/#org","name":"Encontrarás Tudo",
       "url":BASE+"/","logo":BASE+"/assets/logo-gold.png","sameAs":[bp.IG, bp.YT],
       "foundingDate":"2019","founder":{"@id":BASE+"/#gustavo"},
       "description":"Formação católica com fé e razão: orações, novenas e doutrina católica com textos e fontes."}
    main = {"@type":kind,"name":name,"headline":name,"description":desc,"inLanguage":"pt-BR",
       "url":canonical,"isPartOf":{"@id":BASE+"/#site"},"publisher":{"@id":BASE+"/#org"},
       "author":{"@id":BASE+"/#gustavo"},"datePublished":PUB_DATE,"dateModified":MOD_DATE}
    if img:
        main["image"] = BASE + "/" + img
    if about:
        main["about"] = about
    g = [org, PERSON,
      {"@type":"WebSite","@id":BASE+"/#site","url":BASE+"/","name":"Encontrarás Tudo",
       "inLanguage":"pt-BR","publisher":{"@id":BASE+"/#org"}},
      main,
      {"@type":"BreadcrumbList","itemListElement":[
         {"@type":"ListItem","position":i+1,"name":c[0],"item":BASE+"/"+c[1]} for i,c in enumerate(crumbs)]}]
    if faqs:
        g.append({"@type":"FAQPage","@id":canonical+"#faq","inLanguage":"pt-BR","mainEntity":[
           {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faqs]})
    return json.dumps({"@context":"https://schema.org","@graph":g}, ensure_ascii=False)

def faq_html(qas):
    items = "".join('<div class="faq-item"><h3>%s</h3><p>%s</p></div>'
                    % (_html.escape(q), _html.escape(a)) for q, a in qas)
    return '<section class="faq reveal" id="faq"><h2>Perguntas frequentes</h2>%s</section>' % items

def byline():
    return ('<p class="art-byline">Por <a href="sobre.html">Gustavo Souza</a> &middot; catequista '
            '&middot; <time datetime="%s">Atualizado em %s</time></p>' % (MOD_DATE, MOD_DATE_BR))

# CTA duplo (isca grátis + infoproduto) — vem do config.json via build_pages
CTA = bp.cta_block()

# ===================== ORAÇÕES (dados em data/oracoes.json) =====================
DATA_DIR = os.environ.get("ET_DATA_DIR") or os.path.join(bp.SRC, "data")
P = json.load(open(os.path.join(DATA_DIR, "oracoes.json"), encoding="utf-8"))
PNAME = {p["slug"]: p["nome"] for p in P}

def render_oracao(p):
    slug = p["slug"] + ".html"
    canon = BASE + "/" + slug
    rel = ""
    for r in p["related"]:
        nome = PNAME.get(r)
        if not nome and r.startswith("novena"):
            nome = "Novena: " + r.replace("novena-","").replace("-"," ")
        if not nome:
            nome = r.replace("-"," ")
        rel += '<a href="%s.html">%s</a>' % (r, nome)
    cover = '<div class="devo-cover reveal"><img src="%s/%s.webp" alt="%s" loading="lazy"></div>' % (IMG, p["img"], p["nome"])
    np = _plain(p["nome"])
    qas = [
      ("Qual é o texto da %s?" % np, _plain(p["texto"])),
      ("Como e quando rezar a %s?" % np, _plain(p["sobre"])),
      ("O que é a %s?" % np, _plain(p["intro"])),
    ]
    faqs_html = faq_html(qas)
    body = phero("Oração &middot; " + p["cat"], p["nome"], p["sub"]) + '''
<section class="section light"><div class="wrap narrow">
  <nav class="breadcrumb"><a href="index.html">Início</a><span class="sep">&rsaquo;</span><a href="oracoes.html">Orações</a><span class="sep">&rsaquo;</span>%s</nav>
  %s
  <article class="devo reveal">
    %s
    <p class="lead-in">%s</p>
    <h2>A oração</h2>
    <div class="oracao-texto">%s</div>
    <h2>Como e quando rezar</h2>
    %s
    %s
  </article>
  <div class="related"><h2>Veja também</h2><div class="related-list">%s</div></div>
  %s
</div></section>
''' % (p["nome"], cover, byline(), p["intro"], p["texto"], p["sobre"], faqs_html, rel, CTA)
    jd = jsonld(p["nome"], p["sub"], canon,
                [("Início","index.html"),("Orações","oracoes.html"),(p["nome"], slug)],
                img=IMG+"/"+p["img"]+".webp", about={"@type":"Thing","name":p["nome"]}, faqs=qas)
    title = "%s &mdash; texto e como rezar | Encontrarás Tudo" % p["nome"]
    meta = ("%s Reze o texto completo, com o momento certo para rezar." % p["sub"])
    page(slug, title, meta, "oracoes", body, jd, og_image=IMG+"/"+p["img"]+".webp")

for p in P:
    render_oracao(p)

# ===================== NOVENAS (dados em data/novenas.json) =====================
N = json.load(open(os.path.join(DATA_DIR, "novenas.json"), encoding="utf-8"))
NNAME = {n["slug"]: n["nome"] for n in N}

def render_novena(n):
    slug = n["slug"] + ".html"
    canon = BASE + "/" + slug
    rel = ""
    for r in n["related"]:
        nome = PNAME.get(r) or NNAME.get(r) or r.replace("-"," ")
        rel += '<a href="%s.html">%s</a>' % (r, nome)
    festa = ('<div class="devo-note"><b>Festa:</b> %s. Muitos rezam a novena nos dias que antecedem essa data.</div>' % n["festa"]) if n["festa"] else ''
    cover = '<div class="devo-cover reveal"><img src="%s/%s.webp" alt="%s" loading="lazy"></div>' % (IMG, n["img"], n["nome"])
    nn = _plain(n["nome"])
    qas = [
      ("Como rezar a %s?" % nn, _plain(n["como"])),
      ("Qual é a oração da %s?" % nn, _plain(n["oracao"])),
      ("O que é a %s?" % nn, _plain(n["intro"])),
    ]
    if n["festa"]:
        qas.append(("Quando se reza a %s?" % nn,
                    "A festa é em %s. Muitos rezam a novena nos nove dias que antecedem essa data." % n["festa"]))
    faqs_html = faq_html(qas)
    body = phero("Novena &middot; " + n["cat"], n["nome"], n["sub"]) + '''
<section class="section light"><div class="wrap narrow">
  <nav class="breadcrumb"><a href="index.html">Início</a><span class="sep">&rsaquo;</span><a href="novenas.html">Novenas</a><span class="sep">&rsaquo;</span>%s</nav>
  %s
  <article class="devo reveal">
    %s
    %s
    %s
    <h2>Como rezar a novena</h2>
    %s
    <h2>Oração da novena <span style="font-weight:400;font-size:1rem;color:var(--ink-soft)">(rezada em cada um dos dias)</span></h2>
    <div class="oracao-texto">%s</div>
    <p><strong>Para concluir cada dia:</strong> %s</p>
    <div class="devo-note">Esta é a oração central da devoção. Se a sua paróquia tiver meditações próprias para cada dia, você pode acrescentá-las antes da oração.</div>
    %s
  </article>
  <div class="related"><h2>Veja também</h2><div class="related-list">%s</div></div>
  %s
</div></section>
''' % (n["nome"], cover, byline(), n["intro"], festa, n["como"], n["oracao"], n["fecho"], faqs_html, rel, CTA)
    jd = jsonld(n["nome"], n["sub"], canon,
                [("Início","index.html"),("Novenas","novenas.html"),(n["nome"], slug)],
                img=IMG+"/"+n["img"]+".webp", about={"@type":"Thing","name":n["nome"]}, faqs=qas)
    title = "%s &mdash; oração e como rezar | Encontrarás Tudo" % n["nome"]
    meta = ("%s Oração da novena e o passo a passo dos nove dias." % n["sub"])
    page(slug, title, meta, "novenas", body, jd, og_image=IMG+"/"+n["img"]+".webp")

for n in N:
    render_novena(n)

# ===================== HUB ORAÇÕES =====================
cats = ["Dia a dia","A Jesus e ao Espírito Santo","Marianas","Santos e Anjos"]
catlabel = {"Dia a dia":"Para o dia a dia",
            "A Jesus e ao Espírito Santo":"A Jesus e ao Espírito Santo",
            "Marianas":"Orações marianas",
            "Santos e Anjos":"Santos e anjos"}
def hubcard(slug, img, kicker, nome, sub):
    return ('<a class="hub-card" href="%s.html"><div class="hc-img"><img src="%s/%s.webp" alt="%s" loading="lazy"></div>'
            '<div class="hc-body"><p class="hk">%s</p><h3>%s</h3><p>%s</p></div></a>'
            % (slug, IMG, img, nome, kicker, nome, sub))
groups = ""
for c in cats:
    cards = "".join(hubcard(p["slug"], p["img"], c, p["nome"], p["sub"]) for p in P if p["cat"] == c)
    groups += '<div class="hub-group"><h2>%s</h2><div class="hub-grid">%s</div></div>' % (catlabel[c], cards)

oracoes_body = phero("Orações", "Orações católicas", "Os textos das orações mais rezadas pelos católicos no Brasil &mdash; para rezar hoje e todos os dias.") + '''
<section class="section light"><div class="wrap">
  <nav class="breadcrumb"><a href="index.html">Início</a><span class="sep">&rsaquo;</span>Orações</nav>
  <div class="reveal">%s</div>
  <div class="material reveal" style="margin-top:1rem">
    <div class="ico"><img src="assets/logo-white.png" alt=""></div>
    <div><p class="k">Novenas</p><h3>Procura uma novena?</h3><p>Reunimos as novenas mais rezadas do Brasil, com a oração e o passo a passo dos nove dias.</p></div>
    <a class="btn" href="novenas.html">Ver novenas <span class="chev">&rarr;</span></a>
  </div>
  %s
</div></section>
''' % (groups, faq_html([
  ("O que são orações católicas?", "São fórmulas e jaculatórias com que os católicos se dirigem a Deus, a Nossa Senhora e aos santos. Algumas são rezadas todos os dias, como o Pai-Nosso e a Ave-Maria; outras são ligadas a um santo ou a uma necessidade específica."),
  ("Qual oração rezar todos os dias?", "Um bom começo é rezar de manhã (o Oferecimento do Dia) e à noite, além do Terço. Nesta página você encontra o texto de cada oração para rezar no seu tempo."),
  ("Preciso decorar as orações para rezar?", "Não. O importante é rezar com o coração e com atenção ao sentido. Você pode ler o texto completo aqui enquanto reza, e aos poucos vai memorizando as que mais usa."),
]))
oj = jsonld("Orações católicas", "Os textos das orações mais rezadas pelos católicos no Brasil.",
            BASE+"/oracoes.html", [("Início","index.html"),("Orações","oracoes.html")], kind="CollectionPage",
            faqs=[
  ("O que são orações católicas?", "São fórmulas e jaculatórias com que os católicos se dirigem a Deus, a Nossa Senhora e aos santos. Algumas são rezadas todos os dias, como o Pai-Nosso e a Ave-Maria; outras são ligadas a um santo ou a uma necessidade específica."),
  ("Qual oração rezar todos os dias?", "Um bom começo é rezar de manhã (o Oferecimento do Dia) e à noite, além do Terço. Nesta página você encontra o texto de cada oração para rezar no seu tempo."),
  ("Preciso decorar as orações para rezar?", "Não. O importante é rezar com o coração e com atenção ao sentido. Você pode ler o texto completo aqui enquanto reza, e aos poucos vai memorizando as que mais usa."),
])
page("oracoes.html", "Orações católicas: textos e como rezar | Encontrarás Tudo",
     "Os textos das orações católicas mais rezadas no Brasil: São Miguel, Santo Expedito, São Judas, Santa Rita, Salve-Rainha, Ângelus, Magnificat e muito mais.",
     "oracoes", oracoes_body, oj)

# ===================== HUB NOVENAS =====================
ngrps = ["A Jesus e ao Espírito Santo","A Nossa Senhora","Aos Santos e Anjos"]
ngroups = ""
for g in ngrps:
    cards = ""
    for n in N:
        if n["grp"] == g:
            kick = n["cat"] + ((" &middot; " + n["festa"]) if n["festa"] else "")
            cards += hubcard(n["slug"], n["img"], kick, n["nome"], n["sub"])
    ngroups += '<div class="hub-group"><h2>%s</h2><div class="hub-grid">%s</div></div>' % (g, cards)
novenas_body = phero("Novenas", "Novenas católicas", "As novenas mais rezadas pelos católicos no Brasil, com a oração e o passo a passo dos nove dias.") + '''
<section class="section light"><div class="wrap">
  <nav class="breadcrumb"><a href="index.html">Início</a><span class="sep">&rsaquo;</span>Novenas</nav>
  <div class="devo" style="margin:0 0 2rem"><p class="lead-in">Rezar uma novena é perseverar na oração por <strong>nove dias seguidos</strong>, confiando uma intenção à intercessão de Nossa Senhora ou de um santo. Escolha abaixo a sua.</p></div>
  <div class="reveal">%s</div>
  %s
</div></section>
''' % (ngroups, faq_html([
  ("O que é uma novena?", "Novena é uma oração feita durante nove dias seguidos, confiando uma intenção à intercessão de Nossa Senhora ou de um santo. O número nove recorda os nove dias em que os Apóstolos e Maria rezaram no Cenáculo à espera do Espírito Santo."),
  ("Como se reza uma novena?", "Reze todos os dias, de preferência no mesmo horário: faça o Sinal da Cruz, apresente a sua intenção, reze a oração própria da novena e conclua com um Pai-Nosso, uma Ave-Maria e um Glória ao Pai."),
  ("Qualquer pessoa pode fazer uma novena?", "Sim. Qualquer católico pode rezar uma novena, em casa ou na igreja, sozinho ou em família. O essencial é a fé, a perseverança e a confiança na vontade de Deus."),
]))
nj = jsonld("Novenas católicas", "As novenas mais rezadas pelos católicos no Brasil, com oração e passo a passo.",
            BASE+"/novenas.html", [("Início","index.html"),("Novenas","novenas.html")], kind="CollectionPage",
            faqs=[
  ("O que é uma novena?", "Novena é uma oração feita durante nove dias seguidos, confiando uma intenção à intercessão de Nossa Senhora ou de um santo. O número nove recorda os nove dias em que os Apóstolos e Maria rezaram no Cenáculo à espera do Espírito Santo."),
  ("Como se reza uma novena?", "Reze todos os dias, de preferência no mesmo horário: faça o Sinal da Cruz, apresente a sua intenção, reze a oração própria da novena e conclua com um Pai-Nosso, uma Ave-Maria e um Glória ao Pai."),
  ("Qualquer pessoa pode fazer uma novena?", "Sim. Qualquer católico pode rezar uma novena, em casa ou na igreja, sozinho ou em família. O essencial é a fé, a perseverança e a confiança na vontade de Deus."),
])
page("novenas.html", "Novenas católicas: oração e como rezar | Encontrarás Tudo",
     "As novenas mais rezadas no Brasil: Aparecida, Perpétuo Socorro, Fátima, Santa Rita, Santo Expedito, São Judas, Sagrado Coração, Divina Misericórdia, Desatadora dos Nós e mais.",
     "novenas", novenas_body, nj)

# ===================== SITEMAP + ROBOTS =====================
urls = ["index.html","sobre.html","oracoes.html","novenas.html","blog.html","ferramentas.html","contato.html","guia.html"]
urls += [p["slug"]+".html" for p in P] + [n["slug"]+".html" for n in N]
urls += [a["slug"]+".html" for a in bp.ARTIGOS if a.get("status") == "publicado"]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    loc = BASE + "/" + ("" if u == "index.html" else u)
    pr_ = "1.0" if u == "index.html" else ("0.8" if (u in ("oracoes.html","novenas.html")) else "0.7")
    sm.append("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>%s</priority></url>"
              % (loc, MOD_DATE, pr_))
sm.append("</urlset>")
with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write("\n".join(sm))

# robots.txt — libera explicitamente os crawlers de IA (ChatGPT, Claude, Perplexity, Google AI, etc.)
AI_BOTS = ["GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-SearchBot","Claude-User",
           "anthropic-ai","PerplexityBot","Perplexity-User","Google-Extended","Googlebot",
           "Bingbot","Applebot","Applebot-Extended","CCBot","Amazonbot","Bytespider",
           "Meta-ExternalAgent","cohere-ai","YouBot","DuckAssistBot","Timpibot","AI2Bot"]
robots = ["# Encontrarás Tudo — crawlers de busca e de IA são bem-vindos",
          "User-agent: *", "Allow: /", ""]
for b in AI_BOTS:
    robots += ["User-agent: %s" % b, "Allow: /", ""]
robots += ["Sitemap: %s/sitemap.xml" % BASE, ""]
with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(robots))

print("Orações:", len(P), "| Novenas:", len(N), "| URLs no sitemap:", len(urls))
if REVIEW:
    print("\n>>> CONFERIR TEXTO antes de publicar (variantes populares):")
    for r in REVIEW:
        print("   -", r)
