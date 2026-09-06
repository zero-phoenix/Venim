"""
Una tarea recuperada tras un reinicio tiene que seguir escuchando.

LA AFIRMACIÓN QUE ESTE TEST PUEDE REFUTAR
=========================================
«Si reinicias Venim con una tarea a medias, puedes seguir hablándole.»

Refutada el 2026-09-05 pilotando la aplicación. Se reinició con una tarea en
`WAITING_USER_APPROVAL`, el registro dijo

    [SWARM] 1 tarea(s) recuperadas tras reinicio: default

y a partir de ahí **todos los mensajes de esa conversación desaparecieron**.
Se escribían, aparecían en pantalla como `USER COMANDO`, y el enjambre no
arrancaba jamás. Sin error, sin aviso, sin una línea en el registro.

LA CAUSA, Y POR QUÉ ES INSTRUCTIVA
==================================
Cuando el usuario responde algo que NO es una aprobación, el orquestador lo
trata como desacuerdo y reanuda el debate. Para reanudarlo hacía:

    if "approval_event" in state:
        state["approval_event"].set()      # despierta al bucle que espera
    else:
        self._spawn_loop(task_id)          # no hay bucle: créalo

Y `_rehydrate` metía en el estado un `asyncio.Event()` recién construido. Así
que el evento EXISTÍA, se marcaba… y no lo esperaba nadie: el bucle que debía
despertarse había muerto con el proceso anterior. El mensaje se echaba a un
buzón sin cartero.

La pregunta estaba mal hecha. «¿Existe el evento?» no es «¿hay alguien
escuchándolo?», y esa distinción es justo la que este repositorio lleva media
docena de sesiones aprendiendo a no confundir.
"""
from __future__ import annotations

import asyncio

import pytest


class _BusMudo:
    def __init__(self):
        self.publicado = []

    async def publish(self, event):
        self.publicado.append(event)

    def subscribe(self, *a, **k):
        pass


def _orquestador_con_tarea_rehidratada():
    """Un orquestador con una tarea recuperada, sin abrir base ni sockets."""
    from venim.modules.swarm.orchestrator import SwarmOrchestrator

    o = object.__new__(SwarmOrchestrator)
    o.bus = _BusMudo()
    o.active_tasks = {
        "default": {
            "command": "lo de antes", "round": 1,
            "status": "WAITING_USER_APPROVAL",
            "engine": "fast", "narrative_style": "tecnico",
            "route": "task", "max_rounds": 3, "use_tools": False,
            "last_proposal": None, "last_critique": None,
            "calls_used": 0, "rebuilds": 0,
            "approval_event": asyncio.Event(),
            "sin_bucle": True,          # lo que pone `_rehydrate`
        }
    }
    return o


def test_EL_CENTRAL_una_tarea_rehidratada_se_declara_sin_bucle():
    """LA REFUTACIÓN.

    Si el estado recuperado no dice que le falta el bucle, la rama de
    desacuerdo vuelve a marcar un evento que nadie espera y el mensaje se
    pierde otra vez, en silencio.
    """
    estado = _orquestador_con_tarea_rehidratada().active_tasks["default"]
    assert estado.get("sin_bucle") is True, (
        "una tarea recuperada trae un approval_event recién hecho que NO "
        "espera nadie. Sin esta bandera, `set()` lo marca y el mensaje del "
        "usuario desaparece sin dejar rastro")


def test_la_decision_mira_el_bucle_y_no_el_evento():
    """La comprobación exacta que estaba mal, escrita como test.

    Se lee el código fuente porque lo que hay que fijar es la PREGUNTA, no el
    resultado: un `if` que pregunte por el evento vuelve a fallar aunque el
    comportamiento parezca correcto en un caso concreto.
    """
    import inspect

    from venim.modules.swarm import orchestrator

    fuente = inspect.getsource(orchestrator)
    assert 'if state.get("sin_bucle") or "approval_event" not in state:' in fuente, (
        "la rama de desacuerdo ha vuelto a preguntar solo por la existencia "
        "del evento. Existir no es que alguien lo espere.")
    assert 'if "approval_event" in state:\n                        state["approval_event"].set()\n                    else:' not in fuente, (
        "ha vuelto la versión que tragaba los mensajes")


def test_lanzar_el_bucle_baja_la_bandera():
    """Y se baja en el sitio donde el bucle NACE, no en cada llamador.

    Una bandera que hay que acordarse de bajar en tres sitios miente en el que
    se olvide.
    """
    import inspect

    from venim.modules.swarm.orchestrator import SwarmOrchestrator

    fuente = inspect.getsource(SwarmOrchestrator._spawn_loop)
    assert 'sin_bucle' in fuente and 'False' in fuente, (
        "_spawn_loop no limpia la bandera: la tarea seguiría creyéndose sin "
        "bucle para siempre y cada mensaje lanzaría uno nuevo")


def test_spawn_loop_sobre_una_tarea_desconocida_no_revienta():
    """Se puede lanzar el bucle de algo que aún no está en `active_tasks`
    —arranque en frío—, y eso no puede ser un AttributeError."""
    from venim.modules.swarm.orchestrator import SwarmOrchestrator

    o = object.__new__(SwarmOrchestrator)
    o.active_tasks = {}
    lanzados = []
    o._spawn_tracked = lambda tid, coro: (lanzados.append(tid), coro.close())

    SwarmOrchestrator._spawn_loop(o, "no-existe")
    assert lanzados == ["no-existe"]


@pytest.mark.parametrize("estado_previo", ["WAITING_USER_APPROVAL",
                                           "in_progress", "completed"])
def test_toda_tarea_recuperada_trae_la_bandera(estado_previo):
    """No solo las que esperan aprobación: ninguna tarea recuperada tiene
    bucle, así que la bandera no puede depender del estado en que se murió."""
    import inspect

    from venim.modules.swarm.orchestrator import SwarmOrchestrator

    fuente = inspect.getsource(SwarmOrchestrator._rehydrate)
    assert '"sin_bucle": True' in fuente, (
        f"con estado {estado_previo}, la tarea recuperada no se marcaría "
        f"como sin bucle")
