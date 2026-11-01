# /// script
# requires-python = ">=3.9"
# dependencies = ["pillow"]
# ///
"""Gera favicon.png (192), favicon-64.png (64) e favicon.ico (16, 32, 48) na raiz do site.

Uso, na raiz do repo:
    uv run scripts/gera_favicon.py

A fonte é img/fermes-icone.png (512x512), o retrato do Fermes já recortado em
quadrado sobre o fundo escuro original. O favicon do domínio raiz é o que o
claude.ai mostra como ícone do conector Fermes (vps.fabianofilho.com vira
fabianofilho.com no serviço de favicon do Google), por isso o site usa o
mesmo ícone.
"""
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "img" / "fermes-icone.png"


def main():
    im = Image.open(FONTE).convert("RGB")
    if im.size[0] != im.size[1]:
        raise SystemExit(f"{FONTE.name} precisa ser quadrado, veio {im.size}")
    im.resize((192, 192), Image.LANCZOS).save(RAIZ / "favicon.png", optimize=True)
    im.resize((64, 64), Image.LANCZOS).save(RAIZ / "favicon-64.png", optimize=True)
    im.save(RAIZ / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("favicon.png, favicon-64.png e favicon.ico gerados de", FONTE.relative_to(RAIZ))


if __name__ == "__main__":
    main()
