#!/usr/bin/env python3
"""
Motor de arte do Encontrarás Tudo — gera PNGs no padrão da marca
(oxblood + dourado, estátua/arte sacra, Archivo Black) para:
  - post   (feed 1080x1350)
  - carrossel (1080x1350: capa + slides de conteúdo + slide de CTA)
  - story  (9:16 1080x1920)

Renderiza HTML -> PNG com Playwright (Chromium pré-instalado no ambiente).

Uso:
  python3 build_art.py --spec spec.json --out ./saida [--img estatua.webp]

spec.json (exemplos no README do motor):
{
  "formato": "carrossel",
  "slug": "cristo-rei",
  "capa": {"kicker":"...", "titulo":["CRISTO","REI"], "gold":1,
           "sub":"...(post/story)", "cta":"Leia a legenda →"},
  "slides": [{"n":"01","titulo":"...","corpo":"...","fonte":"..."}, ...],
  "cta": {"titulo":"...", "sub":"...", "chip":"Link na bio"}
}
A imagem sacra (fundo preto) é passada em --img e entra na capa/story.
"""
import argparse, base64, json, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

def _b64(path, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(path,"rb").read()).decode())

def fonts_css():
    f = os.path.join(HERE, "fonts")
    def ff(name, w, file):
        return ("@font-face{font-family:'%s';font-weight:%s;src:url(%s) format('truetype')}"
                % (name, w, _b64(os.path.join(f,file),"font/ttf")))
    return "\n".join([
        ff("ArchivoBlack",400,"Archivo-Black.ttf"),
        ff("Archivo",500,"Archivo-Medium.ttf"),
        ff("Archivo",600,"Archivo-SemiBold.ttf"),
        ff("Archivo",700,"Archivo-Bold.ttf"),
    ])

BASE = """
:root{--ox:#681F35;--wine:#9D4058;--gold:#C7A56B;--gold2:#E7C98A;--muted:#b79a86;--cream:#F1E3CF}
*{margin:0;padding:0;box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
html,body{background:#000}
.card{position:relative;overflow:hidden;font-family:'Archivo',sans-serif;color:#fff;
  background:
    radial-gradient(52% 34% at 50% 30%, rgba(199,165,107,.20), transparent 62%),
    radial-gradient(70% 50% at 18% 88%, rgba(157,64,88,.26), transparent 65%),
    linear-gradient(160deg,#1b0c13 0%,#130910 45%,#0c0609 100%);}
.grid{position:absolute;inset:0;opacity:.13;
  background-image:linear-gradient(rgba(199,165,107,.35) 1px,transparent 1px),linear-gradient(90deg,rgba(199,165,107,.35) 1px,transparent 1px);
  background-size:54px 54px;mask-image:radial-gradient(80% 70% at 50% 40%,#000 30%,transparent 85%)}
.vignette{position:absolute;inset:0;z-index:5;background:radial-gradient(92% 82% at 50% 44%,transparent 52%,rgba(0,0,0,.62))}
.halo{position:absolute;left:50%;transform:translateX(-50%);border-radius:50%;z-index:1;filter:blur(8px);
  background:radial-gradient(circle,rgba(231,201,138,.50) 0%,rgba(199,165,107,.16) 40%,transparent 68%)}
.statue{position:absolute;left:50%;transform:translateX(-50%);z-index:3;background-repeat:no-repeat;
  background-size:contain;background-position:center top;mix-blend-mode:screen}
.kicker{font-weight:600;letter-spacing:.01em;color:#efe2cf}
.kicker b{color:var(--gold2);font-weight:700}
.h1{font-family:'ArchivoBlack';line-height:.84;letter-spacing:.01em;text-transform:uppercase;color:#fff;
  text-shadow:0 6px 44px rgba(0,0,0,.75)}
.h1 .g{color:var(--gold);text-shadow:0 4px 30px rgba(0,0,0,.55)}
.scrim{position:absolute;left:0;right:0;bottom:0;z-index:6;
  background:linear-gradient(180deg,transparent 0%,rgba(12,6,9,.62) 44%,rgba(12,6,9,.97) 82%)}
.sub{font-weight:500;color:#f3ead9;margin:0 auto}
.sub b{color:var(--gold2);font-weight:700}
.pill{display:inline-flex;align-items:center;gap:12px;background:linear-gradient(180deg,var(--gold2),var(--gold));
  color:#2a0f1a;font-weight:700;letter-spacing:.06em;text-transform:uppercase;border-radius:999px;
  box-shadow:0 12px 34px rgba(199,165,107,.32)}
.brandrow{display:flex;align-items:center;justify-content:center;gap:15px;border-top:1px solid rgba(199,165,107,.26)}
.brandrow img{height:auto}
.brandrow .bn{font-weight:700;color:#fff;letter-spacing:.02em}
.brandrow .bs{color:var(--muted);letter-spacing:.03em}
/* slides de conteúdo */
.cnum{font-family:'ArchivoBlack';color:transparent;-webkit-text-stroke:2px rgba(199,165,107,.55);line-height:.8}
.ctitle{font-family:'ArchivoBlack';text-transform:uppercase;color:#fff;line-height:.95}
.ctitle .g{color:var(--gold)}
.goldrule{height:3px;width:90px;background:var(--gold);border:0}
.cbody{color:#eaddc9;font-weight:500}
.cbody b{color:var(--gold2);font-weight:700}
.cfonte{color:var(--muted)}
.arrow{color:var(--gold);font-weight:700;letter-spacing:.14em;text-transform:uppercase}
"""

def _wrap(inner, w, h, extra=""):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s\n%s\n.card{width:%dpx;height:%dpx}%s</style></head>"
            "<body>%s</body></html>") % (fonts_css(), BASE, w, h, extra, inner)

def _brand(emblem, size=44):
    return ("<div class='brandrow' style='margin-top:34px;padding-top:26px'>"
            "<img src='%s' style='width:%dpx'>"
            "<div style='text-align:left;line-height:1.08'>"
            "<div class='bn' style='font-size:28px'>@encontrarastudo</div>"
            "<div class='bs' style='font-size:19px'>Formação católica</div></div></div>") % (emblem, size)

def cover_html(spec, img, emblem, mode):
    c = spec["capa"]; t = c["titulo"]; gi = c.get("gold", len(t)-1)
    title = "".join("<br>" if i else "" for i in range(0)) + "<br>".join(
        ("<span class='g'>%s</span>" % w) if i==gi else w for i,w in enumerate(t))
    if mode == "story":
        W,H = 1080,1920
        head = ("<div style='position:absolute;top:150px;left:0;right:0;text-align:center;z-index:2'>"
                "<div class='kicker' style='font-size:31px;margin-bottom:14px'>%s</div>"
                "<div class='h1' style='font-size:196px'>%s</div></div>") % (c.get("kicker",""), title)
        halo = "<div class='halo' style='top:560px;width:620px;height:620px'></div>"
        statue = "<div class='statue' style='top:560px;width:1000px;height:1200px;background-image:url(%s)'></div>" % img
        bottom = ("<div style='position:absolute;left:70px;right:70px;bottom:90px;z-index:7;text-align:center'>"
                  "<p class='sub' style='font-size:38px;line-height:1.34;max-width:940px;margin-bottom:30px'>%s</p>"
                  "<div class='arrow' style='font-size:30px'>%s</div></div>") % (c.get("sub",""), c.get("cta","Veja no feed"))
        scrim = "<div class='scrim' style='height:720px'></div>"
        inner = ("<div class='card'><div class='grid'></div>%s%s%s<div class='vignette'></div>%s%s</div>"
                 % (halo, head, statue, scrim, bottom))
        return _wrap(inner, W, H)
    # post / carrossel_cover (1080x1350)
    W,H = 1080,1350
    head = ("<div style='position:absolute;top:74px;left:0;right:0;text-align:center;z-index:2'>"
            "<div class='kicker' style='font-size:29px;margin-bottom:12px'>%s</div>"
            "<div class='h1' style='font-size:188px'>%s</div></div>") % (c.get("kicker",""), title)
    halo = "<div class='halo' style='top:330px;width:560px;height:560px'></div>"
    statue = "<div class='statue' style='top:322px;width:980px;height:1010px;background-image:url(%s)'></div>" % img
    scrim = "<div class='scrim' style='height:560px'></div>"
    if mode == "carrossel_cover":
        bottom = ("<div style='position:absolute;left:70px;right:70px;bottom:60px;z-index:7;text-align:center'>"
                  "<p class='sub' style='font-size:33px;line-height:1.34;max-width:900px;margin-bottom:26px'>%s</p>"
                  "<div class='arrow' style='font-size:28px'>Arraste &rarr;</div>%s</div>") % (c.get("sub",""), _brand(emblem))
    else:
        bottom = ("<div style='position:absolute;left:70px;right:70px;bottom:52px;z-index:7;text-align:center'>"
                  "<p class='sub' style='font-size:34px;line-height:1.35;max-width:900px;margin-bottom:30px'>%s</p>"
                  "<span class='pill' style='font-size:27px;padding:16px 38px'>%s</span>%s</div>"
                  ) % (c.get("sub",""), c.get("cta","Leia a legenda &rarr;"), _brand(emblem))
    inner = ("<div class='card'><div class='grid'></div>%s%s%s<div class='vignette'></div>%s%s</div>"
             % (halo, head, statue, scrim, bottom))
    return _wrap(inner, W, H)

def content_html(sl, idx, total, emblem):
    W,H = 1080,1350
    body = ("<div class='card'>"
            "<div class='grid'></div>"
            "<div style='position:absolute;top:92px;left:84px;z-index:3'>"
            "<div class='cnum' style='font-size:150px'>%s</div></div>"
            "<div style='position:absolute;top:300px;left:84px;right:84px;z-index:3'>"
            "<div class='ctitle' style='font-size:74px'>%s</div>"
            "<hr class='goldrule' style='margin:30px 0 34px'>"
            "<div class='cbody' style='font-size:38px;line-height:1.5'>%s</div>"
            "%s</div>"
            "<div style='position:absolute;left:84px;right:84px;bottom:56px;z-index:3;display:flex;justify-content:space-between;align-items:center'>"
            "<span class='cfonte' style='font-size:22px'>@encontrarastudo</span>"
            "<span class='cfonte' style='font-size:22px'>%s / %s</span></div>"
            "</div>") % (
            sl.get("n","01"),
            sl.get("titulo",""),
            sl.get("corpo",""),
            ("<div class='cfonte' style='font-size:24px;margin-top:34px'>%s</div>" % sl["fonte"]) if sl.get("fonte") else "",
            str(idx), str(total))
    return _wrap(body, W, H)

def cta_html(spec, emblem):
    W,H = 1080,1350
    c = spec.get("cta", {})
    body = ("<div class='card'>"
            "<div class='grid'></div>"
            "<div class='halo' style='top:300px;width:520px;height:520px'></div>"
            "<div style='position:absolute;inset:0;z-index:3;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 110px'>"
            "<img src='%s' style='width:120px;margin-bottom:40px'>"
            "<div class='h1' style='font-size:96px;margin-bottom:28px'>%s</div>"
            "<p class='sub' style='font-size:38px;line-height:1.4;max-width:860px;margin-bottom:46px'>%s</p>"
            "<span class='pill' style='font-size:30px;padding:18px 44px'>%s</span>"
            "<div class='bs' style='color:var(--muted);font-size:26px;margin-top:40px'>@encontrarastudo &middot; Formação católica</div>"
            "</div></div>") % (emblem, c.get("titulo","Gostou?"), c.get("sub",""), c.get("chip","Link na bio"))
    return _wrap(body, W, H)

def render(html, w, h, out):
    from playwright.sync_api import sync_playwright
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html); path=f.name
    with sync_playwright() as p:
        b=p.chromium.launch()
        pg=b.new_page(viewport={"width":w,"height":h}, device_scale_factor=2)
        pg.goto("file://"+path, wait_until="networkidle")
        pg.wait_for_timeout(400)
        pg.screenshot(path=out, clip={"x":0,"y":0,"width":w,"height":h})
        b.close()
    os.unlink(path)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--img", help="imagem sacra (fundo preto) para capa/story")
    a=ap.parse_args()
    spec=json.load(open(a.spec, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)
    emblem=_b64(os.path.join(HERE,"emblem-gold.png"),"image/png")
    img=_b64(a.img, "image/webp") if a.img else ""
    fmt=spec["formato"]; slug=spec.get("slug","peca"); outs=[]
    if fmt=="post":
        o=os.path.join(a.out,"%s-post.png"%slug); render(cover_html(spec,img,emblem,"post"),1080,1350,o); outs.append(o)
    elif fmt=="story":
        o=os.path.join(a.out,"%s-story.png"%slug); render(cover_html(spec,img,emblem,"story"),1080,1920,o); outs.append(o)
    elif fmt=="carrossel":
        slides=spec.get("slides",[]); total=1+len(slides)+1
        o=os.path.join(a.out,"%s-01-capa.png"%slug); render(cover_html(spec,img,emblem,"carrossel_cover"),1080,1350,o); outs.append(o)
        for i,sl in enumerate(slides):
            o=os.path.join(a.out,"%s-%02d.png"%(slug,i+2)); render(content_html(sl,i+2,total,emblem),1080,1350,o); outs.append(o)
        o=os.path.join(a.out,"%s-%02d-cta.png"%(slug,total)); render(cta_html(spec,emblem),1080,1350,o); outs.append(o)
    for o in outs: print("gerado:", o)

if __name__=="__main__":
    main()
