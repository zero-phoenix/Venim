"""
EL CONTRATO DEL BUS: todo lo que el sistema cuenta de sí mismo, declarado.

LA CIFRA QUE OBLIGÓ A ESCRIBIR ESTO
===================================
Contado el 2026-09-05 cruzando los `topic=` del núcleo con los `topic ===` de
la ventana: **el sistema publica 43 clases de suceso y la interfaz atendía
25**. Las otras 18 —descontando dos que son órdenes, no avisos— se emitían,
viajaban por el socket y se tiraban al llegar.

No eran sucesos menores:

    swarm.budget_exhausted      se acabó el presupuesto de la tarea
    swarm.entrega_incompleta    lo entregado no cubre lo que se pidió
    swarm.verificacion_agotada  no se pudo verificar y se dejó de intentar
    error.critical              error crítico
    ritsuko.veto_de_deriva      Ritsuko ha vetado: el sistema se desvía
    swarm.task_completed        la tarea terminó

Y los dos que más duelen, porque son exactamente la señal que faltaba en los
veinte segundos de pantalla en blanco que se midieron pilotando la ventana:

    swarm.entrada_encolada   {pendientes, texto}
        «tu mensaje está en cola, hay N por delante»
    swarm.ronda              {round, count, calls_used, techo}
        «ronda 2, 3 variantes, 12 llamadas de 40»

O sea: el sistema estaba anunciando su progreso con un contador de
presupuesto incluido, y la ventana lo tiraba mientras el usuario miraba una
pantalla vacía preguntándose si se había colgado.

POR QUÉ UN MÓDULO Y NO UNA LISTA EN UN COMENTARIO
=================================================
Porque una lista en un comentario no rompe nada cuando se queda vieja. Esto
sí: `tests/test_contrato_del_bus.py` recorre el código, encuentra cada
`topic=` publicado y exige que esté aquí; y de los que aquí se declaran
visibles, exige que la ventana los atienda. Publicar algo que nadie escucha
deja de ser posible sin que un test se ponga en rojo.

LA DISTINCIÓN QUE HACE ESTO HONESTO
===================================
No todo lo que viaja por el bus tiene que verse: hay órdenes que van de la
ventana al núcleo y maquinaria interna. Así que cada suceso declara su
destino, y `INTERNO` obliga a escribir POR QUÉ no se pinta. «No se ve» deja
de ser un descuido silencioso y pasa a ser una decisión firmada.
"""
from __future__ import annotations

from dataclasses import dataclass

#: El suceso tiene que llegar a la persona que está mirando.
PANTALLA = "pantalla"
#: El suceso es maquinaria u orden; no se pinta, y el motivo va escrito.
INTERNO = "interno"


@dataclass(frozen=True)
class Suceso:
    tema: str
    destino: str
    #: Qué significa, en la lengua del usuario y no en la del bus.
    dice: str
    #: Si es INTERNO, por qué no se pinta. Obligatorio: sin motivo, el test
    #: lo rechaza. Es la diferencia entre una decisión y un olvido.
    motivo: str = ""


def _p(tema: str, dice: str) -> Suceso:
    return Suceso(tema, PANTALLA, dice)


def _i(tema: str, dice: str, motivo: str) -> Suceso:
    return Suceso(tema, INTERNO, dice, motivo)


SUCESOS: dict[str, Suceso] = {s.tema: s for s in (
    # ---------------------------------------------------- el enjambre trabaja
    _p("swarm.entrada_encolada",
       "Tu mensaje está en cola; hay N por delante."),
    _p("swarm.ronda",
       "Ronda N: tantas variantes, tantas llamadas de tu techo."),
    _p("swarm.routed", "Por qué ruta va tu petición y con cuánta confianza."),
    _p("swarm.style", "Con qué estilo va a responder."),
    _p("agent.delta", "Un nodo está escribiendo, palabra a palabra."),
    _p("agent.delta_end", "Ese nodo terminó de escribir."),
    _p("agent.tool_use", "Un nodo va a usar una herramienta, y con qué."),
    _p("agent.tool_result", "Qué devolvió esa herramienta."),
    # LOS SIETE QUE MI PROPIO RECUENTO NO VIO.
    #
    # La primera versión de este contrato decía «43 tópicos, 25 atendidos».
    # El 43 lo contó un grep de `topic="..."`, y el bucle de agente no publica
    # así: llama a `emit(...)`, y `agents.py` reenvía al bus lo que reciba.
    # Siete sucesos enteros quedaban fuera del censo — y el error iba en la
    # dirección que me hacía quedar mejor, que es la que hay que buscar
    # primero. La cifra real era 50 publicados y 25 atendidos.
    _p("agent.thought",
       "Lo que el nodo está razonando ahora mismo."),
    _p("agent.done", "El nodo terminó su turno, con cuántas iteraciones."),
    _p("agent.turn_done", "Resumen del turno: proveedor, iteraciones, tiempo."),
    _p("agent.timeout", "Un proveedor tardó demasiado y se cambió."),
    _p("agent.slow_iteration",
       "Esta iteración va lenta; el sistema no se ha colgado."),
    _p("AGENT_POST", "Un nodo entrega su propuesta, crítica o resolución."),
    _p("swarm.task_completed", "La tarea terminó."),
    _p("task.usage", "Lo que costó: tokens, tiempo, iteraciones."),
    _p("task.titled", "La conversación ya tiene nombre."),
    _p("task.cancelled", "La tarea se canceló."),
    _p("task.archived", "La conversación se archivó."),
    _p("task.deleted", "La conversación se borró."),

    # ------------------------------------------- cuando algo va mal, se dice
    _p("error.critical",
       "Ha fallado algo grave y la tarea puede no seguir."),
    _p("swarm.budget_exhausted",
       "Se acabó el presupuesto de la tarea antes de terminarla."),
    _p("swarm.entrega_incompleta",
       "Lo entregado no cubre todo lo que pediste."),
    _p("swarm.verification_failed", "La verificación falló."),
    _p("swarm.verificacion_agotada",
       "No se pudo verificar y se dejó de intentar."),
    _p("swarm.approval_required", "Hay algo esperando tu decisión."),
    _p("obs.alert", "Una alarma del sistema."),
    _p("provider.model_drift",
       "Un proveedor ha cambiado el modelo por debajo."),

    # ------------------------------------------------ Naoko: la supervisión
    _p("naoko.status", "En qué está Naoko."),
    _p("naoko.log", "Lo que Naoko va anotando."),
    _p("naoko.trace", "Cómo llegó Naoko a su conclusión."),
    _p("naoko.diagnostico", "El diagnóstico de Naoko sobre el sistema."),
    _p("naoko.improvement", "Un ciclo de mejora en curso."),
    _p("naoko.user_message",
       "El eco de lo que le acabas de decir a Naoko."),

    # ---------------------------------------------- Ritsuko: la auditoría
    _p("ritsuko.status", "En qué está Ritsuko."),
    _p("ritsuko.log", "Lo que Ritsuko va anotando."),
    _p("ritsuko.informe", "Ritsuko ha terminado un informe."),
    _p("ritsuko.user_message",
       "El eco de lo que le acabas de decir a Ritsuko."),
    _p("ritsuko.veto_de_deriva",
       "Ritsuko ha vetado: el sistema se está desviando."),

    # ------------------------------------------------------- el resto del mundo
    _p("sonda.actualizada", "Hay medidas nuevas de los proveedores."),
    _p("swarm.artefacto_listo", "Hay un artefacto construido y observable."),
    _p("knowledge.recorded", "Se aprendió algo y quedó guardado."),
    _p("memgraph.status", "Estado del grafo de memoria."),
    _p("eval.result", "Resultado de una evaluación."),
    _p("system.started", "El sistema arrancó y con qué reparto."),
    _p("system.project_created", "Se creó un proyecto."),
    _p("TERMINAL_OUT", "Salida cruda del sistema, para el terminal."),

    # ------------------------------------------------------------- maquinaria
    _i("SYS_EXEC", "Orden de ejecutar algo.",
       "Va de la ventana al núcleo, no al revés: es lo que el usuario acaba "
       "de pulsar, así que ya lo ha visto. Lo que sí se pinta es su efecto."),
    _i("EMERGENCY_STOP", "Orden de parada de emergencia.",
       "Igual que SYS_EXEC: la dispara el usuario desde el botón PARAR TODO. "
       "La confirmación llega por EMERGENCY_STOP_TRIGGERED, que sí se pinta."),
    _i("sys.terminal.out", "Salida cruda del sistema.",
       "Duplicado histórico de TERMINAL_OUT, que es el que la ventana "
       "atiende. Se declara para que el test no lo dé por olvidado, y está "
       "marcado para unificar: dos nombres para lo mismo son dos sitios donde "
       "arreglar el día que cambie."),
)}


def visibles() -> set[str]:
    """Los que TIENEN que llegar a la pantalla."""
    return {s.tema for s in SUCESOS.values() if s.destino == PANTALLA}


def internos() -> set[str]:
    return {s.tema for s in SUCESOS.values() if s.destino == INTERNO}


# AQUÍ HABÍA UN `describe(tema)` Y LO BORRÉ EN EL MISMO COMMIT EN QUE LO
# ESCRIBÍ, porque el trinquete de huérfanos lo cazó y tenía razón.
#
# Su docstring decía «sirve para que la ventana pinte un suceso sin vista
# propia». La ventana es TypeScript. Esta función es Python. **Su único
# llamador previsto no puede alcanzarla jamás.** Era código correcto,
# comentado con esmero, y estructuralmente imposible de usar.
#
# El día que la ventana necesite estos textos, la forma es exportar `SUCESOS`
# a JSON en el arranque y que el TypeScript lo lea — no una función que mira
# al otro lado de una frontera de lenguaje y saluda.
