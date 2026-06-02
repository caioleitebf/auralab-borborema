"""Extrai logos e cores do Modelo de Cores.pptx."""
from __future__ import annotations

import zipfile
from pathlib import Path


def main():
    pptx = Path(r"C:\Users\caio.ferreira\OneDrive - Aura Minerals\Área de Trabalho\Modelo de Cores.pptx")
    out_dir = Path(__file__).parent / "_pptx_imgs"
    out_dir.mkdir(exist_ok=True)

    print(f"Conteudo do PPTX:")
    with zipfile.ZipFile(pptx) as z:
        for name in z.namelist():
            info = z.getinfo(name)
            if "media" in name.lower() or "image" in name.lower() or "logo" in name.lower():
                dest = out_dir / Path(name).name
                with z.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                print(f"  EXTRAI: {name} ({info.file_size} bytes) -> {dest}")


if __name__ == "__main__":
    main()
