# /// script
# requires-python = ">=3.9"
# dependencies = ["cairosvg", "pillow"]
# ///
"""Gera favicon.png (192), favicon-64.png (64) e favicon.ico (16, 32, 48) na raiz do site.

Uso, na raiz do repo:
    uv run scripts/gera_favicon.py

O SVG vem do <link rel="icon"> em data URI do index.html, para os arquivos
sempre acompanharem o ícone inline. Fundo transparente. Nos tamanhos de 32 px
ou menos o traço fica mais grosso (stroke-width 2.4 em vez de 1.5), senão some
em 16 px.
"""
import io
import re
import urllib.parse
from pathlib import Path

import cairosvg
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
TRACO_PEQUENO = "2.4"
LIMITE_PEQUENO = 32


def svg_do_head():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<link rel="icon" href="data:image/svg\+xml,([^"]+)"', html)
    if not m:
        raise SystemExit("index.html sem o ícone SVG em data URI")
    return urllib.parse.unquote(m.group(1))


def render(svg, tamanho):
    if tamanho <= LIMITE_PEQUENO:
        svg, n = re.subn(r"stroke-width='[^']*'", f"stroke-width='{TRACO_PEQUENO}'", svg, count=1)
        assert n == 1, "stroke-width não encontrado no SVG"
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=tamanho, output_height=tamanho)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def main():
    svg = svg_do_head()
    render(svg, 192).save(RAIZ / "favicon.png", optimize=True)
    render(svg, 64).save(RAIZ / "favicon-64.png", optimize=True)
    imgs = [render(svg, t) for t in (48, 32, 16)]
    imgs[0].save(RAIZ / "favicon.ico", format="ICO", sizes=[(48, 48), (32, 32), (16, 16)], append_images=imgs[1:])
    print("favicon.png, favicon-64.png e favicon.ico gerados")


if __name__ == "__main__":
    main()
