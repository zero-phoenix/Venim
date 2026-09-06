"""
La última puerta: nada llega a pantalla como resultado sin ser un resultado.

LA AFIRMACIÓN QUE ESTE TEST PUEDE REFUTAR
=========================================
«Lo que Venim presenta como RESULTADO_FINAL es una respuesta.»

Refutada el 2026-09-05 pilotando la ventana: tras deliberar, lo que apareció
en pantalla —dos veces, con el mismo formato que una respuesta buena— fue la
palabra `tud.`. Cuatro caracteres. Y el sistema ya lo sabía: la capa de
proveedores lo había marcado minutos antes con estas palabras exactas,

    [WARNING] Perplexity devolvió una respuesta inservible
              (4 caracteres ('tud.')); probando otro

`por_que_es_inservible` existía y funcionaba. Lo que no había era una
comprobación en la salida.
"""
from __future__ import annotations

import pytest

from venim.core.providers.backends.g4f_backend import (
    MINIMO_UTIL,
    por_que_es_inservible,
)

# ============================================ el juez que ya existía

def test_el_fragmento_exacto_que_llego_a_pantalla_se_reconoce():
    motivo = por_que_es_inservible("tud.")
    assert motivo, "«tud.» pasó por bueno: es literalmente lo que se entregó"
    assert "4 caracteres" in motivo and "tud." in motivo, (
        "el motivo tiene que decir QUÉ llegó. Acaba en el log y en la "
        "pantalla, y «inservible» a secas no se puede investigar")


@pytest.mark.parametrize("basura", ["", "   ", "\n\n", ".", "ok", None])
def test_lo_que_no_es_una_respuesta_no_pasa(basura):
    assert por_que_es_inservible(basura) is not None


def test_una_respuesta_corta_pero_de_verdad_sí_pasa():
    """El juez tiene que cazar el fallo evidente sin volverse un crítico
    literario: rechazar algo válido cuesta una llamada de red y confunde."""
    assert por_que_es_inservible("MUESTREO_FPS vale 5.0 fotogramas/s.") is None
    assert len("MUESTREO_FPS vale 5.0") > MINIMO_UTIL


# ==================================== la puerta, en el sitio donde faltaba

async def test_EL_CENTRAL_una_respuesta_inservible_no_se_publica_como_resultado():
    """LA REFUTACIÓN.

    Se monta el nodo con un modelo que devuelve exactamente `tud.` y se
    comprueba que lo que sale al bus NO es eso. Si vuelve a salir, el fallo
    del 2026-09-05 ha vuelto.
    """
    from venim.core.bus import BusEvent, MagiBus
    from venim.modules.swarm.agents import CasperAgent

    publicado: list[dict] = []

    class BusFalso(MagiBus):
        def __init__(self):
            pass

        async def publish(self, event: BusEvent):
            publicado.append(dict(event.payload))

    agente = object.__new__(CasperAgent)
    agente.bus = BusFalso()
    agente.family = "gemini"

    async def responde_basura(*a, **k):
        return "tud.", "g4f-gemini", "gemini"

    agente._ask_stream = responde_basura
    agente._ask_with_tools = responde_basura
    agente._build_system_prompt = lambda *a, **k: "sys"

    devuelto = await CasperAgent.generate_final_resolution(
        agente, task_id="t1", command="da igual",
        proposal={"content": "p"}, critique={"content": "c"})

    assert publicado, "no se publicó nada al bus"
    post = publicado[-1]
    assert post["role"] == "resultado_final"
    assert post["content"] != "tud.", (
        "se volvió a entregar el fragmento tal cual. Este es exactamente el "
        "fallo que se midió en pantalla el 2026-09-05")
    assert "No llegó una respuesta utilizable" in post["content"]
    assert "4 caracteres" in post["content"], (
        "no dice QUÉ llegó, así que no se puede investigar")

    # Y el fallo viaja como DATO, no solo como texto: la ventana tiene que
    # poder pintarlo distinto sin leer el contenido para adivinarlo.
    assert post["inservible"]
    assert post["stats"] == "SIN RESPUESTA"
    assert devuelto == post["content"], (
        "lo que se devuelve al llamador y lo que se enseña al usuario tienen "
        "que ser la misma cosa; si divergen, uno de los dos miente")


async def test_una_respuesta_buena_sigue_saliendo_intacta():
    """La puerta no puede cobrarse respuestas legítimas. Si el camino bueno se
    estropea, el arreglo cuesta más de lo que valía."""
    from venim.core.bus import BusEvent, MagiBus
    from venim.modules.swarm.agents import CasperAgent

    publicado: list[dict] = []

    class BusFalso(MagiBus):
        def __init__(self):
            pass

        async def publish(self, event: BusEvent):
            publicado.append(dict(event.payload))

    buena = "MUESTREO_FPS vale 5.0 fotogramas por segundo en estilo.py."
    agente = object.__new__(CasperAgent)
    agente.bus = BusFalso()
    agente.family = "gemini"

    async def responde_bien(*a, **k):
        return buena, "g4f-gemini", "gemini"

    agente._ask_stream = responde_bien
    agente._ask_with_tools = responde_bien
    agente._build_system_prompt = lambda *a, **k: "sys"

    await CasperAgent.generate_final_resolution(
        agente, task_id="t2", command="x",
        proposal={"content": "p"}, critique={"content": "c"})

    post = publicado[-1]
    assert post["content"] == buena
    assert post["inservible"] is None
    assert post["stats"] == "FINALIZADO"
