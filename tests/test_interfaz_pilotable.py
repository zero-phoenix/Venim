"""
Que la ventana se pueda pilotar sin ratón, y sin adivinar píxeles.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«Todo lo que se puede pulsar en Venim se puede alcanzar con el teclado y
se puede nombrar en voz alta.»

Refutada el 2026-09-05 contando sobre el código. Las doce pestañas del panel
derecho eran `<div onClick>`. Los dos controles más consecuentes de toda la
aplicación —PARAR ESTA y PARAR TODO— eran `<span onClick>`. Cambiar de
conversación, lo que más se hace, era otro `<div>`. Archivar y borrar, spans
anidados dentro de otro span con `stopPropagation` para que no se abriera la
conversación al pulsarlos: un botón dentro de otro botón, resuelto a mano.

Nada de eso existe para `Tab`, ni para un lector de pantalla, ni para nadie
que quiera automatizar la ventana. Y explica lo que David dijo con otras
palabras —«es engorroso de controlar»— y lo que a mí me pasaba: pulsar por
coordenadas, y en una ocasión restaurar la ventana sin querer al fallar por
dos píxeles, moviéndome todas las demás.

POR QUÉ ESTO SE COMPRUEBA CON UN TEST Y NO CON BUENA VOLUNTAD
=============================================================
Porque un `<div onClick>` funciona. Se ve bien, responde al ratón y nadie se
da cuenta de lo que falta hasta que intenta usar el teclado. Es el tipo de
defecto que no duele al que lo escribe.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
VENTANA = RAIZ / "venim-gui" / "src"

#: Un elemento no interactivo al que se le cuelga un `onClick`. React lo
#: acepta y el navegador lo pinta; el teclado no lo ve.
_MUDO = re.compile(r"<(div|span|li|td|img|p)\b[^>]*\bonClick=", re.DOTALL)


def _fuentes():
    if not VENTANA.is_dir():
        pytest.skip("no está el fuente de la ventana en este árbol")
    return sorted(list(VENTANA.rglob("*.tsx")))


#: Lo que todavía no se ha convertido, con su motivo. La lista SOLO PUEDE
#: MENGUAR: es el mismo mecanismo que el trinquete de huérfanos, y por la
#: misma razón — un número que se arregla una vez vuelve.
DEUDA = {
    # PreviewPanel: la rejilla de artefactos. Cada celda abre una vista
    # previa. Se convierte cuando se toque ese panel; no antes, para no
    # mezclar un cambio de accesibilidad con uno de comportamiento.
    "components/PreviewPanel.tsx": 1,
}


def test_EL_CENTRAL_no_hay_controles_que_el_teclado_no_vea():
    """LA REFUTACIÓN.

    Si esto crece, la ventana ha vuelto a llenarse de cosas que parecen
    botones y no lo son.
    """
    encontrados: dict[str, int] = {}
    for f in _fuentes():
        n = len(_MUDO.findall(f.read_text(encoding="utf-8", errors="replace")))
        if n:
            encontrados[str(f.relative_to(VENTANA)).replace("\\", "/")] = n

    nuevos = {k: v for k, v in encontrados.items()
              if v > DEUDA.get(k, 0)}
    assert not nuevos, (
        f"elementos no interactivos con onClick: {nuevos}.\n"
        f"Un `<div onClick>` funciona con el ratón y no existe para `Tab`, ni "
        f"para un lector de pantalla, ni para quien quiera automatizar la "
        f"ventana. Usa <button type=\"button\"> — y si hace falta que no "
        f"parezca un botón, eso lo arregla el CSS.")


def test_la_deuda_no_se_queda_apuntando_a_lo_ya_arreglado():
    """Una lista de excepciones que ya no hacen falta protege menos de lo que
    aparenta. Mismo fallo que un techo de líneas para un fichero borrado."""
    for ruta, tope in DEUDA.items():
        f = VENTANA / ruta
        if not f.is_file():
            pytest.fail(f"la deuda apunta a {ruta}, que no existe")
        real = len(_MUDO.findall(f.read_text(encoding="utf-8", errors="replace")))
        assert real == tope, (
            f"{ruta}: la deuda dice {tope} y hay {real}. Si lo has arreglado, "
            f"baja el número en este mismo commit.")


# ============================================ las pestañas, con su patrón

def test_las_pestanas_son_pestanas_de_verdad():
    """El patrón de ARIA no es burocracia: es lo que hace que las flechas
    funcionen y que se pueda decir «la pestaña Terminal» en vez de «el cuarto
    div de la fila de arriba»."""
    app = (VENTANA / "App.tsx").read_text(encoding="utf-8")
    assert 'role="tablist"' in app
    assert 'role="tab"' in app
    assert "aria-selected" in app
    assert "ArrowRight" in app and "ArrowLeft" in app, (
        "sin flechas, un tablist es una fila de botones con nombre elegante")
    assert "tabIndex={activeTab === tab ? 0 : -1}" in app, (
        "las doce pestañas en el recorrido de Tab son doce paradas para "
        "llegar al campo de texto: así es como se deja de usar el teclado")


def test_los_botones_de_parada_se_pueden_nombrar():
    """Los dos controles más consecuentes de la aplicación. Un botón de
    emergencia al que solo se llega con el ratón es medio botón."""
    app = (VENTANA / "App.tsx").read_text(encoding="utf-8")
    assert 'aria-label="Parar esta conversación"' in app
    assert 'aria-label="Parar todo el sistema"' in app
    assert "<span className=\"stop\"" not in app, (
        "PARAR TODO ha vuelto a ser un span")


def test_hay_UN_sistema_de_foco_y_no_dos():
    """EL ERROR QUE COMETÍ AL HACER ESTO, Y QUE ESTE TEST IMPIDE REPETIR.

    Convertí los divs en botones y les puse a cada uno su propio
    `outline: 2px solid`. Funcionaba. Y estaba mal: `theme/magi.css` ya define

        :focus-visible { outline: none; box-shadow: var(--foco); }

    con un anillo doble que se ve sobre cualquier superficie. Mis reglas eran
    más específicas, así que lo pisaban con algo peor y montaban un segundo
    sistema de foco encima del que había. Es el mismo error contra el que el
    propio `App.css` avisa en su cabecera a propósito de los colores.

    Lo comprobé leyendo el DOM real de la ventana en marcha, no el fichero:
    `getComputedStyle` decía `outline: 2px solid` donde el tema mandaba
    `box-shadow`.
    """
    tema = (VENTANA / "theme" / "magi.css").read_text(encoding="utf-8")
    assert ":focus-visible" in tema and "--foco" in tema, (
        "el tema ha dejado de definir el foco; entonces sí haría falta que "
        "cada control se lo pusiera")

    css = (VENTANA / "App.css").read_text(encoding="utf-8")
    # Se permiten excepciones, pero cada una tiene que estar justificada al
    # lado. Hoy hay una: `.traza` lleva `overflow: hidden` y recorta el anillo
    # de box-shadow, así que ahí sí hace falta un outline.
    excepciones = css.count(":focus-visible")
    assert excepciones <= 2, (
        f"{excepciones} reglas de foco en App.css. Cada una pisa el anillo del "
        f"tema. Solo valen las que un `overflow: hidden` obligue, y con el "
        f"motivo escrito al lado.")
    assert "overflow: hidden" in css or "recorta" in css, (
        "la excepción que queda tiene que explicar por qué existe")


def test_lo_que_se_mueve_solo_respeta_a_quien_pide_que_no():
    """Tres animaciones nuevas —el pulso, el latido de la traza y el de la
    conversación viva— y las tres se paran si el sistema lo pide."""
    css = (VENTANA / "App.css").read_text(encoding="utf-8")
    assert css.count("prefers-reduced-motion") >= 3


# ======================================= el pulso por conversación

def test_una_conversacion_que_trabaja_se_nota_desde_otra():
    """Se podía dejar una corriendo, irse a otra y no tener forma de saber que
    seguía viva. La barra lateral no decía nada."""
    app = (VENTANA / "App.tsx").read_text(encoding="utf-8")
    assert "conv-vivo" in app
    assert "streaming" in app and "startsWith" in app, (
        "el indicador tiene que salir de si ESA conversación está recibiendo "
        "algo, no de una bandera global")
