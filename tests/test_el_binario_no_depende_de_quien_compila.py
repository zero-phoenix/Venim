"""
El .exe de aquí y el .exe publicado tienen que ser el mismo programa.

LA AFIRMACIÓN QUE ESTE TEST PUEDE REFUTAR
=========================================
«Compilar VeniceMAGI produce el mismo binario en cualquier máquina.»

Sostenida hoy, y con una corrección mía dentro.

El 2026-09-06 un .exe recién compilado moría en el arranque:

    File "pyimod01_archive.py", line 134, in extract
    zlib.error: Error -3 while decompressing data: incorrect header check

Dije que era UPX recomprimiendo el archivo del arranque, lo escribí en el
`.spec` como si estuviera medido, y era falso: `Get-Command upx` no encuentra
UPX en esta máquina, así que `upx=True` nunca se aplicó. La causa real eran dos
instancias del programa abiertas que impedían a PyInstaller sobrescribir
`dist/VeniceMAGI.exe`; lo que se probaba era un binario viejo a medio escribir.

Antes de eso hubo otros dos diagnósticos equivocados —puerto ocupado por
SRManager, frontend sin compilar—, los tres plausibles y ninguno comprobado. La
quinta regla del proyecto dice que «no he podido comprobarlo» no es «está
bien»; esto es su reverso: **«suena razonable» tampoco es «está comprobado»**.

POR QUÉ EL TEST SE QUEDA AUNQUE LA CAUSA FUERA OTRA
===================================================
El argumento que sí se sostiene es de reproducibilidad: `upx=True` no significa
«comprime», significa «comprime SI encuentras UPX en el PATH». Hoy no lo tiene
nadie; basta con que alguien lo instale para que su binario deje de ser el que
se publica, sin tocar una línea de código. Es la sexta regla —el binario
publicado tiene que ser el mismo programa que el de desarrollo— y una bandera
cuyo efecto depende del PATH la rompe en silencio.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SPEC = RAIZ / "VeniceMAGI.spec"


@pytest.fixture(scope="module")
def spec() -> str:
    if not SPEC.is_file():
        pytest.skip("no está VeniceMAGI.spec en este árbol")
    return SPEC.read_text(encoding="utf-8")


def test_EL_CENTRAL_no_se_comprime_con_upx(spec):
    """LA REFUTACIÓN.

    Si esto vuelve a `True`, el binario de quien tenga UPX instalado deja de
    ser el que se publica — y el suyo es el que no arranca.
    """
    m = re.search(r"^\s*upx\s*=\s*(True|False)\s*,", spec, re.M)
    assert m, "el .spec ya no dice nada sobre upx: dilo explícitamente"
    assert m.group(1) == "False", (
        "upx=True no significa «comprime», significa «comprime SI encuentras "
        "UPX en el PATH». El resultado es un binario distinto según la "
        "máquina, y el comprimido muere en el arranque con "
        "`zlib.error: incorrect header check` sin dar la cara.")


def test_el_motivo_esta_escrito_al_lado(spec):
    """Un `False` sin explicación se revierte en el primer intento de adelgazar
    el binario, que es exactamente cuando alguien piensa en UPX."""
    i = spec.index("upx=False")
    contexto = spec[max(0, i - 2000):i]
    assert "PATH" in contexto, (
        "falta el argumento que sostiene esto: `upx=True` significa «comprime "
        "si encuentras UPX en el PATH», y eso hace que el binario dependa de "
        "lo que tenga instalado quien compila")


def test_el_icono_existe_y_es_el_que_el_spec_declara(spec):
    """Un icono que el .spec nombra y no está deja el binario con el icono por
    defecto de PyInstaller, y eso no da error: da un .exe genérico."""
    m = re.search(r"icon=\[['\"](.+?)['\"]\]", spec)
    assert m, "el .spec no declara icono"
    ruta = RAIZ / m.group(1).replace("\\\\", "/").replace("\\", "/")
    assert ruta.is_file(), f"el .spec declara {ruta.name} y no existe"
    assert ruta.stat().st_size > 1000, "el icono está vacío o truncado"


def test_el_icono_lleva_los_tamanos_que_windows_pide():
    """Windows escoge el tamaño según dónde lo dibuje: 16 px en la barra de
    título, 32 en la de tareas, 256 en el explorador con iconos grandes. Un
    `.ico` con una sola resolución se ve emborronado en todas las demás,
    porque Windows lo reescala él."""
    ico = RAIZ / "assets" / "icon.ico"
    if not ico.is_file():
        pytest.skip("no está el icono en este árbol")
    from PIL import Image
    with Image.open(ico) as im:
        tamanos = {w for w, _ in im.info.get("sizes", set())}
    for pedido in (16, 32, 48, 256):
        assert pedido in tamanos, (
            f"el .ico no trae {pedido}x{pedido}; Windows lo reescalará y se "
            f"verá sucio justo donde más se mira. Trae: {sorted(tamanos)}")


def test_el_icono_tiene_fondo_transparente():
    """Sobre la barra de tareas oscura, un icono con fondo opaco se ve como un
    recuadro pegado encima."""
    png = RAIZ / "assets" / "icon.png"
    if not png.is_file():
        pytest.skip("no está el icono en este árbol")
    from PIL import Image
    with Image.open(png) as im:
        im = im.convert("RGBA")
        w, h = im.size
        esquinas = [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]
        for x, y in esquinas:
            assert im.getpixel((x, y))[3] == 0, (
                f"la esquina ({x},{y}) no es transparente: el icono lleva "
                f"fondo y se verá como un recuadro sobre la barra de tareas")
