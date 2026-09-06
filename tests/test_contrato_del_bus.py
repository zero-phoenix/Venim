"""
El contrato del bus: nada se publica sin que alguien lo escuche.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«Todo lo que VeniceMAGI cuenta de sí mismo llega a alguien.»

Refutada el 2026-09-05 contando sobre el código: el núcleo publicaba 43 clases
de suceso y la ventana atendía 25. Dieciocho avisos —descontando dos órdenes—
se emitían, viajaban por el socket y se tiraban. Entre ellos «se acabó el
presupuesto», «la entrega está incompleta», «Ritsuko ha vetado» y «error
crítico».

Y los dos que explican los veinte segundos de pantalla en blanco que se
midieron pilotando la aplicación:

    swarm.entrada_encolada   {pendientes, texto}
    swarm.ronda              {round, count, calls_used, techo}

El sistema anunciaba su progreso con contador de presupuesto incluido, y la
ventana lo tiraba mientras el usuario se preguntaba si se había colgado.

ESTE FICHERO ES EL TRINQUETE QUE LO IMPIDE
==========================================
Un número que se arregla una vez vuelve. Una lista en un comentario no rompe
nada cuando envejece. Esto sí.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from vmagi.core.contrato import (
    INTERNO,
    PANTALLA,
    SUCESOS,
    Suceso,
    internos,
    visibles,
)

RAIZ = pathlib.Path(__file__).resolve().parents[1]
NUCLEO = RAIZ / "vmagi"
VENTANA = RAIZ / "vmagi-gui" / "src"

#: Cómo se publica un suceso. SON DOS FORMAS, y la segunda es la que se me
#: escapó al contar.
#:
#: La primera versión de este censo solo buscaba `topic="..."` y dio «43
#: publicados». Pero el bucle de agente no publica así: llama a `emit(...)` y
#: `agents.py` reenvía al bus lo que reciba. Siete sucesos enteros —entre
#: ellos `agent.thought`, que es el razonamiento visible del nodo— quedaban
#: fuera del recuento. El número real era 50.
#:
#: La lección no es «se me olvidó un patrón». Es que **medí con un
#: instrumento que no había auditado**, en un repositorio que tiene un módulo
#: entero dedicado a auditar instrumentos. Y el error iba en la dirección que
#: me hacía quedar mejor, que es la que hay que buscar primero.
_PUBLICA = re.compile(r'topic\s*=\s*"([A-Za-z_.]+)"'
                      r'|(?<![A-Za-z_])emit\(\s*"([A-Za-z_.]+)"')
#: `topic === '...'` en el TypeScript de la ventana.
_ATIENDE = re.compile(r"topic\s*===\s*'([A-Za-z_.]+)'")


def _publicados() -> set[str]:
    fuera: set[str] = set()
    for f in NUCLEO.rglob("*.py"):
        if "_attic" in f.parts or "__pycache__" in f.parts:
            continue
        texto = f.read_text(encoding="utf-8", errors="replace")
        for grupos in _PUBLICA.findall(texto):
            # Se exige al menos una letra: un `emit("...")` de un ejemplo en
            # un docstring casaba con el patron y entraba al censo como si
            # fuera un topico. Un censo que cuenta ejemplos no es un censo.
            fuera |= {g for g in grupos if g and any(c.isalpha() for c in g)}
    return fuera


def _atendidos() -> set[str]:
    if not VENTANA.is_dir():
        pytest.skip("no está el fuente de la ventana en este árbol")
    fuera: set[str] = set()
    for f in list(VENTANA.rglob("*.ts")) + list(VENTANA.rglob("*.tsx")):
        fuera |= set(_ATIENDE.findall(f.read_text(encoding="utf-8",
                                                  errors="replace")))
    return fuera


# ============================================ el contrato está completo

def test_todo_lo_que_se_publica_esta_declarado():
    """Publicar un suceso nuevo obliga a decidir si se ve o no.

    Sin esto, añadir un `topic=` es gratis y no cuesta nada olvidarse del
    otro lado del cable. Así fue como llegaron a ser dieciocho.
    """
    sin_declarar = _publicados() - set(SUCESOS)
    assert not sin_declarar, (
        f"estos tópicos se publican y no están en vmagi/core/contrato.py: "
        f"{sorted(sin_declarar)}.\n"
        f"Decláralos con lo que significan y con su destino. Si no se pintan, "
        f"PANTALLA no vale: usa INTERNO y escribe por qué — «no se ve» tiene "
        f"que ser una decisión firmada, no un descuido.")


def test_no_se_declara_lo_que_ya_nadie_publica():
    """Un contrato con cláusulas muertas protege menos de lo que aparenta.

    Mismo fallo que un techo de líneas apuntando a un fichero borrado: parece
    una garantía y no lo es.
    """
    publicados = _publicados()
    atendidos = _atendidos()
    # Un tópico puede publicarse con el nombre en una variable y aun así ser
    # real: si la ventana lo atiende, existe. Lo que sobra es lo que no
    # aparece en ninguno de los dos lados.
    fantasmas = set(SUCESOS) - publicados - atendidos
    assert not fantasmas, (
        f"declarados y sin publicar por nadie: {sorted(fantasmas)}. "
        f"Bórralos del contrato o encuentra quién debía emitirlos.")


# ================================ EL CENTRAL: nada se emite al vacío

def test_EL_CENTRAL_todo_lo_visible_lo_atiende_la_ventana():
    """LA REFUTACIÓN.

    Si esto falla, hay algo que el sistema te está contando y que no vas a
    ver nunca. Es exactamente el estado en el que estaba el 2026-09-05, con
    dieciocho avisos cayendo al vacío.
    """
    mudos = sorted(visibles() - _atendidos())
    assert not mudos, (
        "el sistema publica esto y la ventana no lo escucha:\n  "
        + "\n  ".join(f"{t}  —  {SUCESOS[t].dice}" for t in mudos)
        + "\n\nCada uno es algo que el usuario tendría que estar viendo y no "
          "ve. O le das una vista, o lo marcas INTERNO con su motivo — pero "
          "no se queda a medias.")


def test_lo_interno_dice_por_que_no_se_ve():
    """`INTERNO` sin motivo sería una puerta trasera para callar cualquier
    cosa: bastaría con marcarla y el test dejaría de mirar."""
    sin_motivo = [s.tema for s in SUCESOS.values()
                  if s.destino == INTERNO and len(s.motivo) < 30]
    assert not sin_motivo, (
        f"marcados como internos sin explicar por qué: {sin_motivo}. "
        f"«No se ve» tiene que ser una decisión firmada.")


def test_cada_suceso_se_explica_en_la_lengua_del_usuario():
    """El contrato lo lee una persona, y `swarm.entrega_incompleta` no dice
    nada. «Lo entregado no cubre lo que pediste» sí. La ventana puede pintar
    esa frase cuando un suceso todavía no tiene vista propia."""
    pobres = [s.tema for s in SUCESOS.values() if len(s.dice) < 15]
    assert not pobres, f"sin explicar: {pobres}"


def test_lo_interno_no_lo_pinta_nadie():
    """El complemento del test central, y no es simetría por simetría.

    Si la ventana atendiera algo declarado INTERNO, una de las dos partes está
    mal: o el motivo escrito es falso —resulta que sí hacía falta verlo— o la
    ventana está pintando una orden suya como si fuera un aviso del sistema,
    que es cómo se acaba enseñando al usuario el eco de su propio clic.
    """
    pintados = internos() & _atendidos()
    assert not pintados, (
        f"declarados internos y sin embargo atendidos: {sorted(pintados)}. "
        f"O el motivo que justifica callarlos es falso, o la ventana está "
        f"pintando sus propias órdenes como si vinieran del sistema.")


def test_todo_destino_es_uno_de_los_dos():
    for s in SUCESOS.values():
        assert isinstance(s, Suceso)
        assert s.destino in (PANTALLA, INTERNO), (s.tema, s.destino)


# ==================================== los dos que explican la pantalla vacía

@pytest.mark.parametrize("tema", ["swarm.entrada_encolada", "swarm.ronda"])
def test_la_señal_de_progreso_es_visible(tema):
    """Estos dos no son un suceso más.

    `swarm.ronda` lleva `{round, count, calls_used, techo}`: una barra de
    progreso con contador de presupuesto, ya calculada. `entrada_encolada`
    lleva `{pendientes}`: la respuesta exacta a «¿por qué no pasa nada?».

    Los veinte segundos de pantalla en blanco que se midieron no eran falta de
    información. Eran esta información, tirada.
    """
    assert SUCESOS[tema].destino == PANTALLA
    assert tema in _atendidos(), (
        f"{tema} sigue sin atenderse: la ventana vuelve a estar muda "
        f"mientras el sistema trabaja")
