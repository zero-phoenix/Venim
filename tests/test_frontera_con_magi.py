"""
Venim es un proyecto, no una capa de pintura sobre otro.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«Venim solo usa su propia interfaz, y nada de MAGI System viaja dentro del
binario que se publica.»

Refutada el 2026-09-06 mirando una captura de la ventana en marcha. El marco
decía «Venim» y el contenido decía, literalmente:

    MAGI SYSTEM IDE — Supercomputadora Táctica Autónoma
    (independiente de Venim). Interfaz horizontal fija.
    ...
    MAGI SYSTEM IDE v0.0.0

Un programa presentándose con el nombre de otro, y encima declarándose
«independiente» de sí mismo.

QUÉ HABÍA DEBAJO, QUE ES EL FALLO DE VERDAD
===========================================
No era un texto olvidado: eran CUATRO restos del proyecto del que salió este,
y todos viajaban dentro del `.exe`.

  1. `assets/modelo-interfaz/magi-interfaz-v6.html` — una maqueta COMPLETA de
     la interfaz de MAGI. Nadie la importaba, pero el `.spec` mete `assets/`
     entera en el binario, así que se empaquetaba y podía servirse.
  2. `venim/gui/` — una SEGUNDA interfaz, con su `magi.proto`, su `src-tauri`
     y su propio `server.py`. Ningún módulo de producción la importaba.
  3. Dos clases `GUIServer` en el árbol: la que usa `main.py` y esa otra.
     Dos servidores para una ventana es uno que sirve lo que no toca.
  4. `magi_sound.mp3`, `tauri.svg` y `vite.svg` en `venim-gui/public/`, que
     Vite copia al `dist` y el servidor sirve tal cual.

Ninguno daba error. Un fichero de más no rompe nada: solo espera a que algo lo
sirva. Y mientras esté dentro, «Venim usa solo su interfaz» es una intención,
no una propiedad.

POR QUÉ ESTO ES UN TEST Y NO UNA LIMPIEZA
=========================================
Porque limpiar es una vez y esto vuelve. La primera regla del proyecto —todo
se conecta o se borra— existe justamente para lo que no molesta: lo que
molesta ya se borra solo. Esta es esa regla aplicada a la frontera entre dos
proyectos que comparten antepasado.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

#: Las marcas del otro proyecto. Si alguna aparece en algo que el usuario ve o
#: que viaja en el binario, Venim ha vuelto a ser una capa de pintura.
MARCAS_AJENAS = ("MAGI SYSTEM IDE", "MAGI System IDE", "MagiSystem",
                 "EVANGELION TACTICAL", "magi-interfaz", "magi_sound")


def _sin_comentarios(texto: str) -> str:
    """El código, sin lo que solo se lee editando.

    Los comentarios SÍ pueden nombrar el pasado —explicar por qué algo se fue
    es medio valor de este repositorio— y de hecho estos tests fallaron dos
    veces contra los comentarios que yo mismo acababa de escribir para
    explicar la limpieza. Lo que no puede aparecer es en pantalla o en el
    empaquetado.
    """
    t = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)        # /* */ y {/* */}
    t = re.sub(r'"""(?:.|\n)*?"""', "", t)                 # docstrings
    return re.sub(r"^\s*(//|#).*$", "", t, flags=re.M)     # // y #


def test_EL_CENTRAL_no_queda_ninguna_maqueta_de_magi():
    """LA REFUTACIÓN.

    Una interfaz entera de otro proyecto, empaquetada dentro del binario de
    este. No hacía falta que nadie la importara para que apareciera: bastaba
    con que algo la sirviera.
    """
    activos = RAIZ / "assets"
    if not activos.is_dir():
        pytest.skip("no hay carpeta de activos en este árbol")

    # `assets/python-embed/` es el intérprete de Python que viaja dentro del
    # .exe, no contenido nuestro: mirar ahí no dice nada de Venim.
    #
    # Y no es teórico. La primera versión de este test barría `assets/` entera
    # buscando cualquier nombre con «magi» dentro, se puso VERDE en mi caja de
    # arena y ROJA en el CI — porque mi copia excluía `python-embed` y la del
    # CI no. Dentro hay `hook-magic.py`, `hook-puremagic.py` y una docena de
    # `vtkImagingCore.py` de PyInstaller: diecisiete falsos positivos.
    #
    # Dos lecciones, y la segunda es la cara: un patrón que casa por subcadena
    # encuentra lo que no busca, y **una caja de pruebas que no es igual que
    # el CI no prueba lo que el CI va a probar**.
    def _nuestro(p) -> bool:
        return "python-embed" not in str(p).replace("\\", "/")

    # Lo que se busca es una MAQUETA: una página servible de otro programa.
    sobras = [p for p in activos.rglob("*.html") if _nuestro(p)]
    sobras += [p for p in activos.rglob("*interfaz*") if _nuestro(p)]
    assert not sobras, (
        f"vuelve a haber una maqueta ajena empaquetada: "
        f"{sorted(str(s.relative_to(RAIZ)) for s in sobras)}. Un HTML aquí "
        f"dentro se publica con cada release y solo espera a que algo lo "
        f"sirva — así fue como la interfaz de MAGI acabó dentro de Venim.")


def test_hay_UNA_interfaz_y_no_dos():
    """Dos árboles de interfaz es uno que se sirve cuando no toca.

    `venim/gui/` era una segunda interfaz completa con su propio servidor.
    """
    assert not (RAIZ / "venim" / "gui").exists(), (
        "ha vuelto `venim/gui/`. La interfaz de Venim es `venim-gui/` y solo "
        "esa; un segundo árbol acaba servido por accidente y nadie sabe cuál "
        "está mirando.")
    assert (RAIZ / "venim-gui" / "src" / "App.tsx").is_file(), (
        "no está la interfaz de Venim donde debe")


def test_hay_UN_servidor_de_interfaz():
    """El que sirve la ventana. Si hay dos, el `.exe` puede levantar el otro."""
    servidores = [p for p in (RAIZ / "venim").rglob("*.py")
                  if re.search(r"^class GUIServer\b", p.read_text(encoding="utf-8",
                                                                  errors="replace"), re.M)]
    rutas = sorted(str(p.relative_to(RAIZ)).replace("\\", "/") for p in servidores)
    assert rutas == ["venim/gui_server.py"], (
        f"hay {len(rutas)} servidores de interfaz: {rutas}. Solo `main.py` "
        f"levanta uno, y el resto son candidatos a servir otra cosa.")


def test_lo_que_se_sirve_es_de_venim():
    """`venim-gui/public/` se copia entero al `dist` y el servidor lo publica.

    Ahí estaban `tauri.svg`, `vite.svg` y `magi_sound.mp3`: dos de un
    andamiaje que ya no se usa y uno con el nombre del otro proyecto.
    """
    publico = RAIZ / "venim-gui" / "public"
    if not publico.is_dir():
        pytest.skip("no está el fuente de la ventana en este árbol")
    ajenos = [p.name for p in publico.iterdir()
              if any(m.lower() in p.name.lower() for m in ("magi", "tauri", "vite"))]
    assert not ajenos, (
        f"{ajenos} se sirven junto a la interfaz de Venim. Lo que se publica "
        f"en la ventana lleva el nombre de Venim o no está.")


def test_el_spec_enumera_lo_que_empaqueta():
    """La causa mecánica de que la maqueta llegara al binario.

    `('assets', 'assets')` mete la carpeta ENTERA. Con eso, cualquier cosa que
    alguien deje ahí —una maqueta de otro proyecto, unas pruebas, un vídeo de
    referencia de 200 MB— se publica sin que nadie lo decida. Enumerar cuesta
    tres líneas más y convierte «creo que no hay nada de más» en saberlo.
    """
    spec = RAIZ / "Venim.spec"
    if not spec.is_file():
        pytest.skip("no está el .spec en este árbol")
    assert "('assets', 'assets')" not in _sin_comentarios(
        spec.read_text(encoding="utf-8")), (
        "el .spec vuelve a empaquetar `assets/` entera. Así fue como una "
        "maqueta de la interfaz de MAGI acabó dentro de cada release.")


@pytest.mark.parametrize("rel", [
    "venim-gui/src/App.tsx",
    "venim-gui/index.html",
    "venim/main.py",
])
def test_ninguna_marca_ajena_donde_el_usuario_lee(rel):
    """Los tres sitios de la captura: la franja de arriba, la marca de la barra
    y el pie. Los tres decían MAGI SYSTEM IDE."""
    p = RAIZ / rel
    if not p.is_file():
        pytest.skip(f"no está {rel} en este árbol")
    texto = p.read_text(encoding="utf-8")
    # Los comentarios SÍ pueden nombrar el pasado —explicar por qué algo se
    # fue es medio valor de este repositorio—; lo que no puede es aparecer en
    # pantalla. Así que se quitan los comentarios de verdad antes de mirar.
    #
    # La primera versión filtraba «líneas que empiezan por //» y su propio
    # test la tumbó: un bloque `{/* ... */}` de JSX tiene líneas interiores
    # que no empiezan por nada de eso, y este fichero explica en uno de ellos
    # justamente cómo se llamaba antes.
    vivas = _sin_comentarios(texto)
    for marca in MARCAS_AJENAS:
        assert marca not in vivas, (
            f"{rel} muestra «{marca}». Venim y MAGI System son dos proyectos "
            f"distintos: el usuario tiene que poder saber cuál ha abierto.")
