"""
El atajo local: que ahorre llamadas SIN contestar lo que había que pensar.

LAS DOS AFIRMACIONES QUE ESTOS TESTS PUEDEN REFUTAR
===================================================
1. «Una pregunta cuyo dato ya está indexado se contesta sin gastar red.»
2. «Un encargo que exige trabajo NUNCA se contesta con un dato.»

La segunda es la que importa. La primera solo hace el sistema rápido; la
segunda es la que impide que sea rápido y equivocado, que es peor que lento.

POR QUÉ ESTE MECANISMO NECESITA UN TEST HOSTIL
==============================================
Un atajo que se equivoca no da error: da una respuesta plausible, corta y a
tiempo. El usuario no puede distinguirla de una deliberada salvo por la
etiqueta, y quien escribe el atajo siempre cree que su condición es estrecha.
Así que aquí se le empujan encargos de trabajo que CONTIENEN las palabras que
el índice reconoce, que es exactamente el caso donde una condición floja se
rompe.
"""
from __future__ import annotations

import pytest

from venim.modules.swarm import atajo

# ============================== lo que SÍ debe atajar

def test_una_pregunta_de_dato_se_resuelve_en_local():
    """Si esto deja de pasar, la capa local no está ahorrando nada y el
    mecanismo entero sobra."""
    r = atajo.consultar("controles de vita")
    assert r is not None, (
        "«controles de vita» es un dato indexado con procedencia; resolverlo "
        "con tres llamadas de red es pagar 30 segundos por leer un fichero")
    assert r["texto"].strip()


def test_el_atajo_es_de_verdad_rapido():
    """La razón de existir del mecanismo, medida y no supuesta.

    El umbral es generoso —200 ms— porque el punto no es el número exacto: es
    la diferencia de ORDEN con una llamada de nube, que son de 3 a 22 SEGUNDOS.
    """
    import time
    t0 = time.perf_counter()
    atajo.consultar("controles de vita")
    ms = (time.perf_counter() - t0) * 1000
    assert ms < 200, (
        f"el atajo tardó {ms:.0f} ms. Si se acerca al coste de una llamada de "
        f"red, deja de compensar y hay que quitarlo")


# ============================== lo que NUNCA debe atajar

@pytest.mark.parametrize("encargo", [
    # Los peligrosos: llevan DENTRO las palabras que el índice reconoce.
    "arregla el mapeo de controles de vita",
    "implementa los controles de vita en el emulador",
    "analiza los repos de saturn y dime cuál conviene portar",
    "escribe un test para las novedades de vita3k",
    "compila el proyecto y comprueba los controles",
    "optimiza el dynarec de vita",
])
def test_EL_CENTRAL_un_encargo_de_trabajo_jamas_se_ataja(encargo):
    """LA REFUTACIÓN.

    Cada uno de estos contiene un término que Lilim sabe buscar. Si la
    condición del atajo fuera «¿reconozco alguna palabra?», todos pasarían y el
    sistema contestaría con un dato a quien pidió que se hiciera algo.
    """
    assert atajo.consultar(encargo) is None, (
        f"«{encargo}» pide TRABAJO y se resolvió con un dato del índice. Un "
        f"atajo que hace esto no acelera el sistema: lo rompe rápido")


@pytest.mark.parametrize("texto", ["", "  ", "ok", "sí"])
def test_lo_vacio_o_trivial_no_ataja(texto):
    """Un «sí» es una respuesta a otra cosa, no una consulta."""
    assert atajo.consultar(texto) is None


def test_lo_que_no_sabe_no_se_inventa():
    """La mitad que casi nadie implementa: cuando no sabe, se calla y deja
    hablar al enjambre. Un índice que rellena huecos es peor que ninguno,
    porque su invención llega con la misma cara que un dato bueno."""
    assert atajo.consultar("cuál es la capital de Marte") is None
    assert atajo.consultar("qué opinas de la arquitectura hexagonal") is None


# ============================== y que el error sea VISIBLE

def test_la_respuesta_dice_que_no_hubo_debate():
    """Si un atajo indebido se colara, esto es lo único que permite verlo desde
    la pantalla. Sin la etiqueta, una respuesta de índice y una deliberada se
    leen igual — y el fallo de esta capa sería invisible justo para quien puede
    corregirlo."""
    r = atajo.consultar("controles de vita")
    assert r is not None
    texto = atajo.redactar("controles de vita", r)
    t = texto.lower()
    assert "local" in t
    assert "no ha deliberado" in t or "sin consultar" in t


def test_los_verbos_de_trabajo_estan_escritos_y_no_adivinados():
    """La lista es la frontera entera del mecanismo. Si alguien la vacía, todo
    ataja; conviene que su tamaño sea una decisión visible."""
    assert len(atajo.VERBOS_DE_TRABAJO) >= 30
    for imprescindible in ("arregla", "implementa", "compila", "analiza"):
        assert imprescindible in atajo.VERBOS_DE_TRABAJO


# ============================== enganchado al sistema, no en una esquina

def test_el_orquestador_lo_consulta_antes_de_gastar_red():
    """Regla 2 del proyecto: un test sobre una pieza aislada no prueba que el
    sistema la use. En el proyecto de origen, la capa neuronal equivalente
    tenía tests verdes y CERO llamantes en producción."""
    import inspect

    from venim.modules.swarm.orchestrator import SwarmOrchestrator

    fuente = inspect.getsource(SwarmOrchestrator)
    assert "_intentar_atajo" in fuente
    i_atajo = fuente.index("await _intentar_atajo(")
    i_bucle = fuente.index("self._spawn_loop(task_id)\n        return task_id")
    assert i_atajo < i_bucle, (
        "el atajo se consulta DESPUÉS de arrancar el enjambre: para entonces "
        "las llamadas ya están gastadas y no ahorra nada")
