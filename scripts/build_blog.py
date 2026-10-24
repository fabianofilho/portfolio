# /// script
# requires-python = ">=3.9"
# dependencies = ["markdown>=3.5"]
# ///
"""Gera o blog Perspectives (https://fabianofilho.com/perspectives/) a partir de posts/*.md, em inglês e português.

Uso, na raiz do repo:
    uv run scripts/build_blog.py            # gera perspectives/, feeds, sitemap e o link no menu
    uv run scripts/build_blog.py --check    # só confere se o que está commitado bate com os posts

Cada post tem uma versão por idioma, com o mesmo slug:

    posts/AAAA-MM-DD-slug.md       inglês   -> /perspectives/slug/
    posts/AAAA-MM-DD-slug.pt.md    português -> /perspectives/pt/slug/

Qualquer uma pode ser o original e a outra a tradução; basta existir uma. Cabeçalho simples:

    ---
    title: Why calibration matters more than accuracy
    summary: One or two sentences for the index, the feed and the search snippet.
    date: 2026-10-24
    draft: false
    translation: false   # true na versão que é tradução da outra
    ---
    Texto em Markdown.

Post com draft: true não é publicado. O botão PT/EN leva à outra versão do mesmo texto; sem tradução,
leva ao índice do outro idioma, que lista o post no idioma em que ele existe. As duas versões se
apontam por hreflang. O link "Perspectives" no menu da home só aparece com pelo menos um post e
segue o idioma escolhido na home.
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
NOME_BLOG = "Perspectives"
PESSOA = SITE + "/#person"
MARCA_INI, MARCA_FIM = "<!-- blog-nav:inicio -->", "<!-- blog-nav:fim -->"
ARQ_NOME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)(?:\.(pt|en))?\.md$")
IDIOMAS = ("en", "pt")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]

T = {
    "en": {
        "html_lang": "en", "og_locale": "en_US", "hreflang": "en",
        "base": SITE + "/perspectives/", "caminho": "/perspectives/",
        "descricao": ("Essays by Fabiano Filho, MD, on artificial intelligence in medicine: "
                      "clinical prediction, fairness, evaluation and what it takes to use AI well in health care."),
        "eyebrow": "Essays", "vazio": "The first essay is on its way.", "por": "By",
        "atualizado": "updated", "min": "min read", "outro_idioma": "in Portuguese",
        "byline": ("Fabiano Filho (Fabiano Barcellos Filho) is a physician and data scientist who teaches AI in "
                   "medicine. PhD candidate at LABDAPS, School of Public Health, University of São Paulo. "
                   "More at <a href=\"/\">fabianofilho.com</a>."),
        "home": "Home", "tema": "Toggle light and dark theme", "botao": "PT", "botao_aria": "Ler em português",
        "titulo_indice": f"{NOME_BLOG} · Fabiano Filho, MD",
    },
    "pt": {
        "html_lang": "pt-BR", "og_locale": "pt_BR", "hreflang": "pt-BR",
        "base": SITE + "/perspectives/pt/", "caminho": "/perspectives/pt/",
        "descricao": ("Ensaios de Fabiano Filho, médico, sobre inteligência artificial na medicina: "
                      "predição clínica, justiça algorítmica, avaliação e o que é preciso para usar IA bem na saúde."),
        "eyebrow": "Ensaios", "vazio": "O primeiro ensaio está a caminho.", "por": "Por",
        "atualizado": "atualizado em", "min": "min de leitura", "outro_idioma": "em inglês",
        "byline": ("Fabiano Filho (Fabiano Barcellos Filho) é médico e cientista de dados e ensina IA na "
                   "medicina. Doutorando no LABDAPS, Faculdade de Saúde Pública da Universidade de São Paulo. "
                   "Mais em <a href=\"/\">fabianofilho.com</a>."),
        "home": "Início", "tema": "Alternar tema claro e escuro", "botao": "EN", "botao_aria": "Read in English",
        "titulo_indice": f"{NOME_BLOG} · Fabiano Filho, médico",
    },
}
OUTRO = {"en": "pt", "pt": "en"}


def le_post(arq):
    m = ARQ_NOME.match(arq.name)
    if not m:
        raise SystemExit(f"nome fora do padrão AAAA-MM-DD-slug[.pt].md: {arq.name}")
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
        "titulo": meta["title"], "resumo": meta["summary"], "data": data,
        "atualizado": dt.date.fromisoformat(meta["updated"]) if meta.get("updated") else data,
        "rascunho": meta.get("draft", "false").lower() == "true",
        "traducao": meta.get("translation", "false").lower() == "true",
        "slug": m.group(2), "lang": m.group(3) or "en",
        "html": markdown.markdown(corpo, extensions=["extra", "sane_lists"], output_format="html"),
        "palavras": len(re.findall(r"\w+", corpo)),
    }


def carrega():
    """Devolve {slug: {lang: post}} só com o publicado, e os slugs do mais novo ao mais antigo."""
    grupos = {}
    for arq in sorted(POSTS.glob("*.md")) if POSTS.exists() else []:
        p = le_post(arq)
        if p["rascunho"]:
            continue
        if p["lang"] in grupos.setdefault(p["slug"], {}):
            raise SystemExit(f"slug repetido no mesmo idioma: {p['slug']} ({p['lang']})")
        grupos[p["slug"]][p["lang"]] = p
    def data_de(slug):
        return min(v["data"] for v in grupos[slug].values())
    return grupos, sorted(grupos, key=data_de, reverse=True)


def url_post(slug, lang):
    return T[lang]["base"] + slug + "/"


def data_longa(d, lang):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}" if lang == "pt" else d.strftime("%B %-d, %Y")


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
.hdr-tools{display:flex;align-items:center;gap:2px;border-left:1px solid var(--rule);padding-left:14px}
.tool-btn{all:unset;cursor:pointer;box-sizing:border-box;font-family:var(--mono);font-size:12px;letter-spacing:.04em;color:var(--muted);padding:4px 6px;line-height:1;display:inline-flex;align-items:center}.tool-btn:hover{color:var(--accent);text-decoration:none}
.tool-btn svg{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
main{max-width:720px;margin:0 auto;padding:72px var(--gutter) 96px}
.eyebrow{margin:0 0 20px;font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-weight:400;font-size:44px;line-height:1.1;letter-spacing:-.01em;margin:0 0 18px}
.lede{font-size:20px;line-height:1.55;color:var(--ink-3);margin:0 0 40px}
.list{list-style:none;margin:0;padding:0;border-top:1px solid var(--rule)}
.list li{padding:24px 0;border-bottom:1px solid var(--rule-soft)}
.list time,.list .tag{font-family:var(--mono);font-size:12px;color:var(--muted)}
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

SCRIPTS = """<script>(function(){var r=document.documentElement,i=document.getElementById('theme-icon');
var SUN='<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>';
var MOON='<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
function p(){i.innerHTML=r.classList.contains('dark')?SUN:MOON}
document.getElementById('theme-btn').addEventListener('click',function(){var d=!r.classList.contains('dark');r.classList.toggle('dark',d);try{localStorage.setItem('theme',d?'dark':'light')}catch(e){}p()});p();
var l=document.getElementById('lang-btn');l.addEventListener('click',function(){try{localStorage.setItem('lang',l.getAttribute('data-lang'))}catch(e){}});})();</script>"""


def pagina(lang, titulo, descricao, url, jsonld, corpo, troca, alternativos, og_tipo="website", extra_head=""):
    """troca: URL do botão PT/EN. alternativos: {lang: url} para o hreflang (vazio se só há um idioma)."""
    e, t = html.escape, T[lang]
    alt = ""
    if len(alternativos) > 1:
        alt = "".join(f'  <link rel="alternate" hreflang="{T[k]["hreflang"]}" href="{v}" />\n' for k, v in alternativos.items())
        alt += f'  <link rel="alternate" hreflang="x-default" href="{alternativos.get("en", url)}" />\n'
    outro = OUTRO[lang]
    return f"""<!DOCTYPE html>
<html lang="{t["html_lang"]}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{e(titulo)}</title>
  <meta name="description" content="{e(descricao)}" />
  <meta name="author" content="Fabiano Filho" />
  <link rel="canonical" href="{url}" />
{alt}  <link rel="alternate" type="application/rss+xml" title="{NOME_BLOG} · Fabiano Filho" href="{t["base"]}feed.xml" />
  <meta property="og:type" content="{og_tipo}" />
  <meta property="og:site_name" content="Fabiano Filho" />
  <meta property="og:title" content="{e(titulo)}" />
  <meta property="og:description" content="{e(descricao)}" />
  <meta property="og:url" content="{url}" />
  <meta property="og:image" content="{SITE}/img/og-fabiano-filho.jpg" />
  <meta property="og:locale" content="{t["og_locale"]}" />
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
      <a href="/">{t["home"]}</a>
      <a href="{t["caminho"]}" class="active">{NOME_BLOG}</a>
    </nav>
    <div class="hdr-tools">
      <a class="tool-btn" id="lang-btn" href="{troca}" hreflang="{T[outro]["hreflang"]}" data-lang="{outro}" aria-label="{t["botao_aria"]}">{t["botao"]}</a>
      <button type="button" class="tool-btn" id="theme-btn" aria-label="{t["tema"]}"><svg id="theme-icon" viewBox="0 0 24 24" aria-hidden="true"></svg></button>
    </div>
  </div>
</header>
<main>
{corpo}
</main>
<footer class="site-footer">
  <div class="ftr">
    <span>© {dt.date.today().year} Fabiano Barcellos Filho · São Paulo</span>
    <span><a href="{t["base"]}feed.xml">RSS</a> · <a href="/">fabianofilho.com</a></span>
  </div>
</footer>
{SCRIPTS}
</body>
</html>
"""


def gera_indice(lang, grupos, ordem):
    e, t = html.escape, T[lang]
    itens = []
    for slug in ordem:
        versoes = grupos[slug]
        p = versoes.get(lang) or versoes[OUTRO[lang]]
        aviso = "" if lang in versoes else f' <span class="tag">· {t["outro_idioma"]}</span>'
        itens.append(f'    <li><time datetime="{p["data"]}">{data_longa(p["data"], lang)}</time>{aviso}'
                     f'<h2><a href="{url_post(slug, p["lang"])}" hreflang="{T[p["lang"]]["hreflang"]}">{e(p["titulo"])}</a></h2>'
                     f'<p>{e(p["resumo"])}</p></li>')
    lista = f'  <ol class="list">\n' + "\n".join(itens) + "\n  </ol>" if itens else f'  <p class="empty">{t["vazio"]}</p>'
    corpo = f"""  <p class="eyebrow">{t["eyebrow"]}</p>
  <h1>{NOME_BLOG}</h1>
  <p class="lede">{e(t["descricao"])}</p>
{lista}"""
    proprios = [s for s in ordem if lang in grupos[s]]
    ld = {"@context": "https://schema.org", "@type": "Blog", "@id": t["base"] + "#blog", "url": t["base"],
          "name": f"{NOME_BLOG} · Fabiano Filho", "description": t["descricao"], "inLanguage": t["hreflang"],
          "author": {"@id": PESSOA}, "publisher": {"@id": PESSOA}, "isPartOf": {"@id": SITE + "/#website"},
          "blogPost": [{"@type": "BlogPosting", "headline": grupos[s][lang]["titulo"], "url": url_post(s, lang),
                        "datePublished": grupos[s][lang]["data"].isoformat()} for s in proprios]}
    extra = "" if proprios else '  <meta name="robots" content="noindex" />\n'  # sem post próprio, fora do Google
    alternativos = {k: T[k]["base"] for k in IDIOMAS}
    return pagina(lang, t["titulo_indice"], t["descricao"], t["base"], ld, corpo,
                  troca=T[OUTRO[lang]]["caminho"], alternativos=alternativos, extra_head=extra)


def gera_post(p, versoes):
    e, lang, t = html.escape, p["lang"], T[p["lang"]]
    url = url_post(p["slug"], lang)
    outro = OUTRO[lang]
    troca = T[outro]["caminho"] + p["slug"] + "/" if outro in versoes else T[outro]["caminho"]
    alternativos = {k: url_post(p["slug"], k) for k in IDIOMAS if k in versoes}
    minutos = max(1, round(p["palavras"] / 230))
    atual = (f' · {t["atualizado"]} <time datetime="{p["atualizado"]}">{data_longa(p["atualizado"], lang)}</time>'
             if p["atualizado"] != p["data"] else "")
    corpo = f"""  <p class="eyebrow"><a href="{t["caminho"]}">{NOME_BLOG}</a></p>
  <article>
  <h1>{e(p["titulo"])}</h1>
  <p class="meta">{t["por"]} <a href="/">Fabiano Filho, MD</a> · <time datetime="{p["data"]}">{data_longa(p["data"], lang)}</time>{atual} · {minutos} {t["min"]}</p>
  <div class="prose">
{p["html"]}
  </div>
  <p class="byline">{t["byline"]}</p>
  </article>"""
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url + "#post",
          "headline": p["titulo"], "description": p["resumo"], "url": url, "mainEntityOfPage": url,
          "datePublished": p["data"].isoformat(), "dateModified": p["atualizado"].isoformat(),
          "inLanguage": t["hreflang"], "wordCount": p["palavras"], "image": SITE + "/img/og-fabiano-filho.jpg",
          "author": {"@id": PESSOA, "@type": "Person", "name": "Fabiano Filho", "url": SITE + "/"},
          "publisher": {"@id": PESSOA}, "isPartOf": {"@id": t["base"] + "#blog"}}
    if outro in versoes:  # liga original e tradução (translation: true marca a tradução)
        chave = "translationOfWork" if p["traducao"] else ("workTranslation" if versoes[outro]["traducao"] else None)
        if chave:
            ld[chave] = {"@id": url_post(p["slug"], outro) + "#post"}
    extra = (f'  <meta property="article:published_time" content="{p["data"].isoformat()}" />\n'
             f'  <meta property="article:author" content="{SITE}/" />\n')
    return pagina(lang, f'{p["titulo"]} · Fabiano Filho', p["resumo"], url, ld, corpo,
                  troca=troca, alternativos=alternativos, og_tipo="article", extra_head=extra)


def gera_feed(lang, grupos, ordem):
    e, t = html.escape, T[lang]
    def rfc822(d):
        return dt.datetime(d.year, d.month, d.day, 9, 0, tzinfo=dt.timezone(dt.timedelta(hours=-3))).strftime("%a, %d %b %Y %H:%M:%S %z")
    posts = [grupos[s][lang] for s in ordem if lang in grupos[s]]
    itens = "".join(
        f"""  <item>
    <title>{e(p["titulo"])}</title>
    <link>{url_post(p["slug"], lang)}</link>
    <guid isPermaLink="true">{url_post(p["slug"], lang)}</guid>
    <pubDate>{rfc822(p["data"])}</pubDate>
    <description>{e(p["resumo"])}</description>
  </item>
""" for p in posts)
    ultimo = rfc822(posts[0]["data"]) if posts else rfc822(dt.date(2026, 10, 24))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{NOME_BLOG} · Fabiano Filho</title>
  <link>{t["base"]}</link>
  <atom:link href="{t["base"]}feed.xml" rel="self" type="application/rss+xml" />
  <description>{e(t["descricao"])}</description>
  <language>{t["hreflang"]}</language>
  <lastBuildDate>{ultimo}</lastBuildDate>
{itens}</channel>
</rss>
"""


def gera_sitemap(grupos, ordem):
    marca = re.search(r"<loc>https://fabianofilho.com/</loc>\s*<lastmod>([\d-]+)</lastmod>",
                      (RAIZ / "sitemap.xml").read_text(encoding="utf-8"))
    home_mod = marca.group(1) if marca else dt.date.today().isoformat()
    urls = [(SITE + "/", home_mod)]
    for lang in IDIOMAS:
        proprios = [grupos[s][lang] for s in ordem if lang in grupos[s]]
        if proprios:  # índice sem post próprio não entra no sitemap
            urls.append((T[lang]["base"], max(p["atualizado"] for p in proprios).isoformat()))
            urls += [(url_post(p["slug"], lang), p["atualizado"].isoformat()) for p in proprios]
    linhas = "".join(f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{m}</lastmod>\n  </url>\n" for u, m in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{linhas}</urlset>\n'


def com_link_no_menu(index_html, tem_posts):
    ini, fim = index_html.find(MARCA_INI), index_html.find(MARCA_FIM)
    if ini < 0 or fim < 0:
        raise SystemExit("index.html sem as marcas blog-nav no menu")
    miolo = ""
    if tem_posts:
        # A home abre em português; o link segue o idioma escolhido no botão EN/PT dela.
        miolo = (f'\n      <a href="{T["pt"]["caminho"]}" id="blog-link" data-pt="{T["pt"]["caminho"]}" '
                 f'data-en="{T["en"]["caminho"]}" class="nav-blog">{NOME_BLOG}<span class="nav-pill">blog</span></a>\n'
                 "      <script>(function(){var a=document.getElementById('blog-link');"
                 "function u(){var l=null;try{l=localStorage.getItem('lang')}catch(e){}a.href=l==='en'?a.dataset.en:a.dataset.pt}"
                 "u();document.addEventListener('DOMContentLoaded',function(){var b=document.getElementById('lang-btn');"
                 "if(b)b.addEventListener('click',function(){setTimeout(u,0)})})})();</script>\n      ")
    return index_html[:ini + len(MARCA_INI)] + miolo + index_html[fim:]


DESTAQUE_INI, DESTAQUE_FIM = "<!-- blog-destaque:inicio -->", "<!-- blog-destaque:fim -->"
DESTAQUE_CSS = """<style>
    .hdr-nav a.nav-blog { color: var(--accent); }
    .hdr-nav a.nav-blog:hover { color: var(--ink); }
    @media (min-width: 721px) and (max-width: 1180px) { .hdr { column-gap: 16px; } .hdr-nav { column-gap: 14px; } }
    .nav-pill { margin-left: 6px; padding: 1px 6px; border: 1px solid currentColor; border-radius: 10px; font-size: 10px; letter-spacing: .08em; text-transform: uppercase; vertical-align: 1px; }
    .blog-band { padding: 40px 0 44px; border-bottom: 1px solid var(--rule); }
    .bb-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 8px 24px; margin-bottom: 24px; }
    .bb-head .kicker { color: var(--accent); }
    .bb-sub { font-family: var(--serif); font-size: 18px; text-transform: none; letter-spacing: 0; color: var(--ink-3); margin-left: 12px; }
    .bb-all { font-family: var(--mono); font-size: 12.5px; }
    .bb-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); gap: 24px 48px; }
    .bb-item { display: block; color: var(--ink); border-left: 2px solid var(--accent); padding: 2px 0 2px 18px; }
    .bb-item:hover { text-decoration: none; }
    .bb-item:hover .bb-title { color: var(--accent); }
    .bb-meta { font-family: var(--mono); font-size: 12px; color: var(--muted); }
    .bb-title { display: block; font-size: 26px; line-height: 1.2; margin: 6px 0 8px; }
    .bb-sum { display: block; font-size: 16.5px; line-height: 1.55; color: var(--ink-3); }
    html[lang="en"] .bt-pt, html:not([lang="en"]) .bt-en { display: none; }
    @media (max-width: 720px) { .bb-sub { display: block; margin: 6px 0 0; font-size: 16px; } .bb-title { font-size: 22px; } }
  </style>"""
SUB = {"pt": "Ensaios sobre IA na medicina", "en": "Essays on AI in medicine"}
TODOS = {"pt": "Todos os ensaios &rarr;", "en": "All essays &rarr;"}


def faixa_destaque(grupos, ordem, n=2):
    """Faixa da home com os ensaios mais recentes, nas duas línguas (o CSS mostra a do html lang)."""
    e = html.escape
    blocos = []
    for lang in IDIOMAS:
        itens = []
        for slug in ordem[:n]:
            versoes = grupos[slug]
            p = versoes.get(lang) or versoes[OUTRO[lang]]
            aviso = "" if lang in versoes else f" · {T[lang]['outro_idioma']}"
            itens.append(f'      <a class="bb-item" href="{T[p["lang"]]["caminho"]}{slug}/" hreflang="{T[p["lang"]]["hreflang"]}">'
                         f'<span class="bb-meta"><time datetime="{p["data"]}">{data_longa(p["data"], lang)}</time>{aviso}</span>'
                         f'<span class="bb-title">{e(p["titulo"])}</span><span class="bb-sum">{e(p["resumo"])}</span></a>')
        blocos.append(f'    <div class="bb-grid bt-{lang}">\n' + "\n".join(itens) + "\n    </div>")
    cab = ("    <div class=\"bb-head\"><p class=\"kicker\" style=\"margin:0\">" + NOME_BLOG + " · blog"
           + "".join(f'<span class="bb-sub bt-{l}">{SUB[l]}</span>' for l in IDIOMAS) + "</p>"
           + "".join(f'<a class="bb-all bt-{l}" href="{T[l]["caminho"]}">{TODOS[l]}</a>' for l in IDIOMAS) + "</div>")
    return f"\n  {DESTAQUE_CSS}\n  <section class=\"blog-band\" aria-label=\"{NOME_BLOG}\">\n{cab}\n" + "\n".join(blocos) + "\n  </section>\n  "


def com_destaque(index_html, grupos, ordem):
    ini, fim = index_html.find(DESTAQUE_INI), index_html.find(DESTAQUE_FIM)
    if ini < 0 or fim < 0:
        raise SystemExit("index.html sem as marcas blog-destaque")
    miolo = faixa_destaque(grupos, ordem) if ordem else ""
    return index_html[:ini + len(DESTAQUE_INI)] + miolo + index_html[fim:]


def arquivos(grupos, ordem):
    saida = {RAIZ / "sitemap.xml": gera_sitemap(grupos, ordem),
             RAIZ / "index.html": com_destaque(com_link_no_menu((RAIZ / "index.html").read_text(encoding="utf-8"), bool(ordem)), grupos, ordem)}
    for lang in IDIOMAS:
        pasta = SAIDA / ("pt" if lang == "pt" else "")
        saida[pasta / "index.html"] = gera_indice(lang, grupos, ordem)
        saida[pasta / "feed.xml"] = gera_feed(lang, grupos, ordem)
    for slug in ordem:
        for lang, p in grupos[slug].items():
            pasta = SAIDA / ("pt" if lang == "pt" else "") / slug
            saida[pasta / "index.html"] = gera_post(p, grupos[slug])
    return saida


def pastas_de_post():
    """Pastas de post já geradas (perspectives/<slug>/ e perspectives/pt/<slug>/)."""
    achadas = [d for d in SAIDA.glob("*/") if d.is_dir() and d.name != "pt"]
    achadas += [d for d in (SAIDA / "pt").glob("*/") if d.is_dir()] if (SAIDA / "pt").exists() else []
    return achadas


def main():
    grupos, ordem = carrega()
    saida = arquivos(grupos, ordem)
    esperadas = {a.parent for a in saida if a.name == "index.html" and a.parent.parent in (SAIDA, SAIDA / "pt") and a.parent.name != "pt"}
    orfas = [d for d in pastas_de_post() if d not in esperadas]
    if "--check" in sys.argv:
        velhos = [str(a.relative_to(RAIZ)) for a, t in saida.items() if not a.exists() or a.read_text(encoding="utf-8") != t]
        velhos += [str(d.relative_to(RAIZ)) for d in orfas]
        if velhos:
            print("desatualizado:", ", ".join(velhos))
            sys.exit(1)
        n = sum(len(v) for v in grupos.values())
        print(f"ok: {len(ordem)} post(s), {n} versão(ões), tudo em dia")
        return
    for d in orfas:
        for f in d.glob("*"):
            f.unlink()
        d.rmdir()
    for arq, texto in saida.items():
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto, encoding="utf-8")
    n = sum(len(v) for v in grupos.values())
    print(f"{len(ordem)} post(s), {n} versão(ões); gerado em perspectives/ e perspectives/pt/")


if __name__ == "__main__":
    main()
