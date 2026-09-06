"""
El programa se llama igual en todos los sitios donde alguien lo lee.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«Venim se presenta como Venim en todas partes.»

Refutada el 2026-09-06, y no leyendo el código: **arrancando el binario y
pidiéndole la página**. El renombrado de 267 ficheros dejó el título de la
ventana diciendo `MAGI System IDE` —el nombre de DOS renombrados atrás— porque
esa cadena no contenía «VeniceMAGI» ni «vmagi», que era lo que mi búsqueda
sustituía. El `index.html` tampoco entró en el barrido: recorrí `venim-gui/src`
y el fichero vive un nivel más arriba.

POR QUÉ ESTE FALLO ES DEL TIPO QUE NO SE VE
===========================================
No da error. La aplicación arranca, funciona y hace todo lo que promete; solo
que la pestaña, la barra de tareas y el gestor de ventanas la llaman por el
nombre del proyecto del que salió. Es exactamente lo que este repositorio
decidió que no volvería a pasar cuando la interfaz se presentaba como «MAGI
SYSTEM IDE», y volvió a pasar por otro camino.

Un renombrado se comprueba con una lista de sitios, no con una búsqueda: la
búsqueda solo encuentra los nombres que ya sabías que existían.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
NOMBRE = "Venim"

#: Los nombres que este programa tuvo antes. Ninguno puede aparecer donde el
#: usuario lo lee.
NOMBRES_MUERTOS = ("VeniceMAGI", "MAGI System IDE", "MAGI SYSTEM IDE",
                   "MagiSystem", "vmagi")


def _texto(rel: str) -> str | None:
    p = RAIZ / rel
    return p.read_text(encoding="utf-8") if p.is_file() else None


def _sin_comentarios(texto: str) -> str:
    """El código, sin lo que solo se lee editando.

    Un comentario puede —y debe— explicar cómo se llamaba esto antes y por qué
    dejó de llamarse así. Lo que no puede es aparecer en pantalla. Este filtro
    salió de que estos mismos tests se pusieron rojos contra los comentarios
    escritos para explicar el renombrado.
    """
    t = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    t = re.sub(r'"""(?:.|\n)*?"""', "", t)
    return re.sub(r"^\s*(//|#).*$", "", t, flags=re.M)


def test_EL_CENTRAL_el_titulo_de_la_ventana():
    """LA REFUTACIÓN, y el sitio exacto donde falló.

    Este `<title>` es lo que Windows pone en la barra de tareas y lo que
    aparece en el gestor de ventanas. Se quedó en `MAGI System IDE`.
    """
    html = _texto("venim-gui/index.html")
    if html is None:
        pytest.skip("no está el fuente de la ventana en este árbol")
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    assert m, "la página no declara título: la ventana saldrá sin nombre"
    titulo = m.group(1).strip()
    assert titulo == NOMBRE, (
        f"el título de la ventana dice «{titulo}» y el programa se llama "
        f"{NOMBRE}. No da error, solo hace que la barra de tareas lo llame "
        f"por el nombre de otro proyecto.")


def test_el_titulo_de_la_ventana_nativa():
    """El otro título: el que pywebview pone en el marco de la ventana."""
    main = _texto("venim/main.py")
    if main is None:
        pytest.skip("no está main.py en este árbol")
    m = re.search(r'title\s*=\s*["\'](.+?)["\']', main)
    assert m and m.group(1) == NOMBRE, (
        f"la ventana nativa se titula «{m.group(1) if m else '(nada)'}»")


@pytest.mark.parametrize("rel", [
    "venim-gui/index.html",
    "venim-gui/package.json",
    "venim/main.py",
    "README.md",
    "Venim.spec",
])
def test_ningun_nombre_muerto_donde_se_lee(rel):
    """Los sitios que un usuario mira. La lista es corta y explícita a
    propósito: una búsqueda global encuentra los nombres que ya sabías que
    existían, y el que se escapó fue justamente el que no estaba en la
    búsqueda."""
    crudo = _texto(rel)
    if crudo is None:
        pytest.skip(f"no está {rel} en este árbol")
    t = _sin_comentarios(crudo)
    for muerto in NOMBRES_MUERTOS:
        # El README puede nombrar el pasado al explicar la mudanza de datos;
        # lo que no puede es presentarse con él.
        if rel == "README.md" and muerto == "VeniceMAGI":
            continue
        assert muerto not in t, (
            f"{rel} todavía dice «{muerto}». El programa se llama {NOMBRE}.")


def test_el_ejecutable_y_el_paquete_se_llaman_igual():
    """Un `.exe` con un nombre y un paquete con otro obliga a traducir mentalmente
    entre los dos cada vez que se lee una traza."""
    spec = _texto("Venim.spec")
    if spec is None:
        pytest.skip("no está el .spec en este árbol")
    m = re.search(r"name\s*=\s*['\"](.+?)['\"]", spec)
    assert m and m.group(1) == NOMBRE, (
        f"el .spec produce «{m.group(1) if m else '(nada)'}.exe»")
    assert (RAIZ / "venim").is_dir(), "el paquete Python no se llama venim/"


def test_el_paquete_de_la_interfaz_tambien():
    """`package.json` acaba en el `dist` y en cualquier error de npm."""
    p = _texto("venim-gui/package.json")
    if p is None:
        pytest.skip("no está package.json en este árbol")
    nombre = json.loads(p).get("name", "")
    assert "magi" not in nombre.lower() or "venim" in nombre.lower(), (
        f"el paquete de la interfaz se llama «{nombre}»")
