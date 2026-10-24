# /// script
# requires-python = ">=3.9"
# dependencies = ["markdown>=3.5"]
# ///
"""Gera o blog Perspectives (https://fabianofilho.com/perspectives/) a partir de posts/*.md.

Uso, na raiz do repo:
    uv run scripts/build_blog.py            # gera perspectives/, feed, sitemap e o link no menu
    uv run scripts/build_blog.py --check    # só confere se o que está commitado bate com os posts

Cada post é um arquivo posts/AAAA-MM-DD-slug.md com cabeçalho simples:

    ---
    title: Why calibration matters more than accuracy
    summary: One or two sentences for the index, the feed and the search snippet.
    date: 2026-10-24
    draft: false
    ---
    Texto em Markdown (inglês).

Post com draft: true não é publicado. O slug vem do nome do arquivo, depois da data.
O link "Perspectives" no menu da home só aparece quando há pelo menos um post publicado.
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent.parent
POSTS = RAIZ / "posts"
SAIDA = RAIZ / "perspectives"
SITE = "https://fabianofilho.com"
BASE = SITE + "/perspectives/"
NOME_BLOG = "Perspectives"
DESCRICAO_BLOG = ("Essays by Fabiano Filho, MD, on artificial intelligence in medicine: "
                  "clinical prediction, fairness, evaluation and what it takes to use AI well in health care.")
PESSOA = SITE + "/#person"
MARCA_INI, MARCA_FIM = "<!-- blog-nav:inicio -->", "<!-- blog-nav:fim -->"
ARQ_NOME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")


def le_post(arq):
    m = ARQ_NOME.match(arq.name)
    if not m:
        raise SystemExit(f"nome fora do padrão AAAA-MM-DD-slug.md: {arq.name}")
    texto = arq.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        raise SystemExit(f"{arq.name}: falta o cabeçalho entre ---")
    cab, corpo = texto[4:].split("\n---\n", 1)
    meta = {}
    for linha in cab.splitlines():
        if linha.strip():
            k, _, v = linha.partition(":")
            meta[k.strip()] = v.strip()
    for campo in ("title", "summary", "date"):
        if not meta.get(campo):
            raise SystemExit(f"{arq.name}: falta '{campo}' no cabeçalho")
    data = dt.date.fromisoformat(meta["date"])
    return {
        "titulo": meta["title"],
        "resumo": meta["summary"],
        "data": data,
        "atualizado": dt.date.fromisoformat(meta["updated"]) if meta.get("updated") else data,
        "rascunho": meta.get("draft", "false").lower() == "true",
        "slug": m.group(2),
        "html": markdown.markdown(corpo, extensions=["extra", "smarty", "sane_lists"], output_format="html"),
        "palavras": len(re.findall(r"\w+", corpo)),
    }


def posts_publicados():
    todos = [le_post(a) for a in sorted(POSTS.glob("*.md"))] if POSTS.exists() else []
    slugs = [p["slug"] for p in todos]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dois posts com o mesmo slug")
    return sorted((p for p in todos if not p["rascunho"]), key=lambda p: p["data"], reverse=True)


def data_longa(d):
    return d.strftime("%B %-d, %Y")


CSS = """
:root{--paper:#f6f4ee;--paper-blur:rgba(246,244,238,.92);--ink:#1c1b18;--ink-3:#3b3934;--muted:#6e6a60;--rule:#dcd7cb;--rule-soft:#ebe7dd;--accent:#0f6b4f;--selection:#cfe3d9;--serif:'Source Serif 4',Georgia,serif;--mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;--gutter:32px;color-scheme:light}
html.dark{--paper:#161512;--paper-blur:rgba(22,21,18,.92);--ink:#ebe7dc;--ink-3:#bdb8ab;--muted:#969185;--rule:#35322c;--rule-soft:#282621;--accent:#5fc39c;--selection:#24493b;color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-optical-sizing:auto;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--accent);text-decoration:none}a:hover{color:var(--ink);text-decoration:underline;text-underline-offset:3px}
::selection{background:var(--selection)}:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.site-header{position:sticky;top:0;z-index:10;background:var(--paper-blur);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}
.hdr{max-width:1120px;margin:0 auto;padding:14px var(--gutter);display:flex;flex-wrap:wrap;align-items:center;gap:8px 24px;font-family:var(--mono);font-size:12px;letter-spacing:.02em;color:var(--muted)}
.hdr-name{color:var(--ink);font-weight:500;white-space:nowrap}
.hdr-nav{margin-left:auto;display:flex;gap:4px 18px}.hdr-nav a{color:var(--muted);white-space:nowrap}.hdr-nav a:hover,.hdr-nav a.active{color:var(--ink)}
.hdr-nav a.active{text-decoration:underline;text-underline-offset:3px;text-decoration-color:var(--accent)}
.hdr-tools{display:flex;align-items:center;border-left:1px solid var(--rule);padding-left:14px}
.tool-btn{all:unset;cursor:pointer;color:var(--muted);padding:4px 6px;line-height:1;display:inline-flex}.tool-btn:hover{color:var(--accent)}
.tool-btn svg{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
main{max-width:720px;margin:0 auto;padding:72px var(--gutter) 96px}
.eyebrow{margin:0 0 20px;font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-weight:400;font-size:44px;line-height:1.1;letter-spacing:-.01em;margin:0 0 18px}
.lede{font-size:20px;line-height:1.55;color:var(--ink-3);margin:0 0 40px}
.list{list-style:none;margin:0;padding:0;border-top:1px solid var(--rule)}
.list li{padding:24px 0;border-bottom:1px solid var(--rule-soft)}
.list time{font-family:var(--mono);font-size:12px;color:var(--muted)}
.list h2{font-weight:500;font-size:24px;line-height:1.25;margin:6px 0 8px}.list h2 a{color:var(--ink)}.list h2 a:hover{color:var(--accent)}
.list p{margin:0;font-size:17px;line-height:1.55;color:var(--ink-3)}
.empty{font-family:var(--mono);font-size:13px;color:var(--muted);padding:24px 0;border-top:1px solid var(--rule)}
.meta{font-family:var(--mono);font-size:12px;color:var(--muted);margin:0 0 40px;padding-bottom:20px;border-bottom:1px solid var(--rule)}
.prose{font-size:19px;line-height:1.7}
.prose p{margin:0 0 1.15em}.prose h2{font-weight:500;font-size:26px;line-height:1.25;margin:1.8em 0 .6em}.prose h3{font-weight:600;font-size:20px;margin:1.6em 0 .5em}
.prose blockquote{margin:1.4em 0;padding:4px 0 4px 20px;border-left:2px solid var(--accent);color:var(--ink-3);font-style:italic}
.prose ul,.prose ol{padding-left:1.3em;margin:0 0 1.15em}.prose li{margin:.3em 0}
.prose code{font-family:var(--mono);font-size:.82em;background:var(--rule-soft);padding:1px 5px}
.prose pre{font-family:var(--mono);font-size:14px;line-height:1.6;background:var(--rule-soft);padding:16px;overflow-x:auto}.prose pre code{background:none;padding:0}
.prose img{max-width:100%;height:auto}.prose hr{border:none;border-top:1px solid var(--rule);margin:2em 0}
.prose table{border-collapse:collapse;width:100%;font-size:16px}.prose th,.prose td{border-bottom:1px solid var(--rule);padding:8px 6px;text-align:left}
.byline{margin-top:56px;padding-top:20px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:12.5px;line-height:1.8;color:var(--muted)}
.ftr{max-width:1120px;margin:0 auto;padding:24px var(--gutter) 40px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px 24px;font-family:var(--mono);font-size:12px;color:var(--muted);border-top:1px solid var(--rule)}
@media (max-width:720px){:root{--gutter:20px}.hdr{flex-wrap:nowrap;gap:12px}.hdr-nav{gap:12px}.hdr-tools{padding-left:8px}main{padding-top:48px}h1{font-size:34px}.lede{font-size:18px}.prose{font-size:18px}}
@media (max-width:420px){.hdr-nav a:first-child{display:none}}
"""

TEMA_CEDO = ("<script>(function(){var t=null;try{t=localStorage.getItem('theme')}catch(e){}"
             "if(!t)t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
             "if(t==='dark')document.documentElement.classList.add('dark')})();</script>")

TEMA_BOTAO = """<script>(function(){var r=document.documentElement,i=document.getElementById('theme-icon');
var SUN='<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>';
var MOON='<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
function p(){i.innerHTML=r.classList.contains('dark')?SUN:MOON}
document.getElementById('theme-btn').addEventListener('click',function(){var d=!r.classList.contains('dark');r.classList.toggle('dark',d);try{localStorage.setItem('theme',d?'dark':'light')}catch(e){}p()});p()})();</script>"""


def pagina(titulo, descricao, url, jsonld, corpo, og_tipo="website", extra_head=""):
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(titulo)}</title>
  <meta name="description" content="{e(descricao)}" />
  <meta name="author" content="Fabiano Filho" />
  <link rel="canonical" href="{url}" />
  <link rel="alternate" type="application/rss+xml" title="{NOME_BLOG} by Fabiano Filho" href="{BASE}feed.xml" />
  <meta property="og:type" content="{og_tipo}" />
  <meta property="og:site_name" content="Fabiano Filho" />
  <meta property="og:title" content="{e(titulo)}" />
  <meta property="og:description" content="{e(descricao)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/img/og-fabiano-filho.jpg" />
  <meta property="og:locale" content="en_US" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{e(titulo)}" />
  <meta name="twitter:description" content="{e(descricao)}" />
  <meta name="twitter:image" content="{SITE}/img/og-fabiano-filho.jpg" />
{extra_head}  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
  {TEMA_CEDO}
  <style>{CSS}</style>
</head>
<body>
<header class="site-header">
  <div class="hdr">
    <a href="/" class="hdr-name">Barcellos Filho, F.</a>
    <nav class="hdr-nav" aria-label="Site">
      <a href="/">Home</a>
      <a href="/perspectives/" class="active">{NOME_BLOG}</a>
    </nav>
    <div class="hdr-tools">
      <button type="button" class="tool-btn" id="theme-btn" aria-label="Toggle light and dark theme"><svg id="theme-icon" viewBox="0 0 24 24" aria-hidden="true"></svg></button>
    </div>
  </div>
</header>
<main>
{corpo}
</main>
<footer class="site-footer">
  <div class="ftr">
    <span>© {dt.date.today().year} Fabiano Barcellos Filho · São Paulo</span>
    <span><a href="{BASE}feed.xml">RSS</a> · <a href="/">fabianofilho.com</a></span>
  </div>
</footer>
{TEMA_BOTAO}
</body>
</html>
"""


def gera_indice(posts):
    e = html.escape
    if posts:
        itens = "\n".join(
            f'    <li><time datetime="{p["data"]}">{data_longa(p["data"])}</time>'
            f'<h2><a href="{p["slug"]}/">{e(p["titulo"])}</a></h2><p>{e(p["resumo"])}</p></li>'
            for p in posts)
        lista = f'  <ol class="list">\n{itens}\n  </ol>'
    else:
        lista = '  <p class="empty">The first essay is on its way.</p>'
    corpo = f"""  <p class="eyebrow">Essays · in English</p>
  <h1>{NOME_BLOG}</h1>
  <p class="lede">{e(DESCRICAO_BLOG)}</p>
{lista}"""
    ld = {"@context": "https://schema.org", "@type": "Blog", "@id": BASE + "#blog", "url": BASE,
          "name": f"{NOME_BLOG} by Fabiano Filho", "description": DESCRICAO_BLOG, "inLanguage": "en",
          "author": {"@id": PESSOA}, "publisher": {"@id": PESSOA},
          "isPartOf": {"@id": SITE + "/#website"},
          "blogPost": [{"@type": "BlogPosting", "headline": p["titulo"], "url": BASE + p["slug"] + "/",
                        "datePublished": p["data"].isoformat()} for p in posts]}
    extra = "" if posts else '  <meta name="robots" content="noindex" />\n'  # sem post, fora do Google
    return pagina(f"{NOME_BLOG} · Fabiano Filho, MD", DESCRICAO_BLOG, BASE, ld, corpo, extra_head=extra)


def gera_post(p):
    e = html.escape
    url = BASE + p["slug"] + "/"
    minutos = max(1, round(p["palavras"] / 230))
    atual = f' · updated <time datetime="{p["atualizado"]}">{data_longa(p["atualizado"])}</time>' if p["atualizado"] != p["data"] else ""
    corpo = f"""  <p class="eyebrow"><a href="/perspectives/">{NOME_BLOG}</a></p>
  <article>
  <h1>{e(p["titulo"])}</h1>
  <p class="meta">By <a href="/">Fabiano Filho, MD</a> · <time datetime="{p["data"]}">{data_longa(p["data"])}</time>{atual} · {minutos} min read</p>
  <div class="prose">
{p["html"]}
  </div>
  <p class="byline">Fabiano Filho (Fabiano Barcellos Filho) is a physician and data scientist who teaches AI in medicine.
  PhD candidate at LABDAPS, School of Public Health, University of São Paulo. More at <a href="/">fabianofilho.com</a>.</p>
  </article>"""
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url + "#post",
          "headline": p["titulo"], "description": p["resumo"], "url": url, "mainEntityOfPage": url,
          "datePublished": p["data"].isoformat(), "dateModified": p["atualizado"].isoformat(),
          "inLanguage": "en", "wordCount": p["palavras"], "image": SITE + "/img/og-fabiano-filho.jpg",
          "author": {"@id": PESSOA, "@type": "Person", "name": "Fabiano Filho", "url": SITE + "/"},
          "publisher": {"@id": PESSOA}, "isPartOf": {"@id": BASE + "#blog"}}
    extra = (f'  <meta property="article:published_time" content="{p["data"].isoformat()}" />\n'
             f'  <meta property="article:author" content="{SITE}/" />\n')
    return pagina(f'{p["titulo"]} · Fabiano Filho', p["resumo"], url, ld, corpo, og_tipo="article", extra_head=extra)


def gera_feed(posts):
    e = html.escape
    def rfc822(d):
        return dt.datetime(d.year, d.month, d.day, 9, 0, tzinfo=dt.timezone(dt.timedelta(hours=-3))).strftime("%a, %d %b %Y %H:%M:%S %z")
    itens = "".join(
        f"""  <item>
    <title>{e(p["titulo"])}</title>
    <link>{BASE}{p["slug"]}/</link>
    <guid isPermaLink="true">{BASE}{p["slug"]}/</guid>
    <pubDate>{rfc822(p["data"])}</pubDate>
    <description>{e(p["resumo"])}</description>
  </item>
""" for p in posts)
    ultimo = rfc822(posts[0]["data"]) if posts else rfc822(dt.date(2026, 10, 24))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{NOME_BLOG} by Fabiano Filho</title>
  <link>{BASE}</link>
  <atom:link href="{BASE}feed.xml" rel="self" type="application/rss+xml" />
  <description>{e(DESCRICAO_BLOG)}</description>
  <language>en</language>
  <lastBuildDate>{ultimo}</lastBuildDate>
{itens}</channel>
</rss>
"""


def gera_sitemap(posts):
    marca = re.search(r"<loc>https://fabianofilho.com/</loc>\s*<lastmod>([\d-]+)</lastmod>",
                      (RAIZ / "sitemap.xml").read_text(encoding="utf-8"))
    home_mod = marca.group(1) if marca else dt.date.today().isoformat()
    blog_mod = posts[0]["atualizado"].isoformat() if posts else home_mod
    urls = [(SITE + "/", home_mod)]
    if posts:  # índice vazio não entra no sitemap
        urls += [(BASE, blog_mod)] + [(BASE + p["slug"] + "/", p["atualizado"].isoformat()) for p in posts]
    linhas = "".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{m}</lastmod>\n  </url>\n" for u, m in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{linhas}</urlset>\n'


def com_link_no_menu(index_html, tem_posts):
    ini, fim = index_html.find(MARCA_INI), index_html.find(MARCA_FIM)
    if ini < 0 or fim < 0:
        raise SystemExit("index.html sem as marcas blog-nav no menu")
    miolo = f'\n      <a href="/perspectives/">{NOME_BLOG}</a>\n      ' if tem_posts else ""
    return index_html[:ini + len(MARCA_INI)] + miolo + index_html[fim:]


def arquivos(posts):
    saida = {SAIDA / "index.html": gera_indice(posts), SAIDA / "feed.xml": gera_feed(posts),
             RAIZ / "sitemap.xml": gera_sitemap(posts),
             RAIZ / "index.html": com_link_no_menu((RAIZ / "index.html").read_text(encoding="utf-8"), bool(posts))}
    for p in posts:
        saida[SAIDA / p["slug"] / "index.html"] = gera_post(p)
    return saida


def main():
    posts = posts_publicados()
    saida = arquivos(posts)
    if "--check" in sys.argv:
        velhos = [str(a.relative_to(RAIZ)) for a, t in saida.items() if not a.exists() or a.read_text(encoding="utf-8") != t]
        orfaos = [str(d.relative_to(RAIZ)) for d in SAIDA.glob("*/") if d.is_dir() and d.name not in {p["slug"] for p in posts}]
        if velhos or orfaos:
            print("desatualizado:", ", ".join(velhos + orfaos))
            sys.exit(1)
        print(f"ok: {len(posts)} post(s) publicados, tudo em dia")
        return
    for d in SAIDA.glob("*/"):
        if d.is_dir() and d.name not in {p["slug"] for p in posts}:
            for f in d.glob("*"):
                f.unlink()
            d.rmdir()
    for arq, texto in saida.items():
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto, encoding="utf-8")
    print(f"{len(posts)} post(s) publicados; gerado em perspectives/")


if __name__ == "__main__":
    main()
