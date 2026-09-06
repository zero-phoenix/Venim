"""
EL ATAJO LOCAL: cuando la respuesta ya está escrita, no se convoca un debate.

EL COSTE QUE ESTO ATACA
=======================
Una vuelta del enjambre son TRES llamadas de red como mínimo —Melchior propone,
Balthasar refuta, Casper sintetiza— y los proveedores gratuitos tardan entre 3
y 22 segundos cada una, con fallos frecuentes que obligan a reintentar. El
coste dominante de este sistema no es pensar: es ESPERAR.

Y una parte de esa espera se paga por nada. «¿Qué controles tiene la Vita?» es
un dato que está escrito en `vmagi/data/memoria/controles.json` desde hace
semanas. Deliberarlo entre tres modelos no lo mejora: lo retrasa treinta
segundos y gasta cupo que hará falta para lo siguiente.

POR QUÉ ESTE ATAJO NO ES EL ATAJO PELIGROSO
===========================================
El fallo obvio de una capa así es contestar rápido lo que había que pensar. Un
índice que rellena huecos es peor que no tener índice, porque su respuesta
llega con la misma cara de seguridad que una buena.

Tres frenos, y los tres son estrechos a propósito:

  1. **Solo lo que Lilim sabe.** `responde_si_sabe` devuelve `None` cuando no
     tiene la respuesta indexada. No hay generación, no hay modelo, no hay
     inferencia: es una búsqueda. Lo que no está, no se inventa.
  2. **Solo si el clasificador local lo reconoce** como consulta de memoria.
     Cualquier cosa que huela a trabajo —escribir, compilar, arreglar,
     analizar— va al enjambre aunque Lilim creyera saber algo.
  3. **La respuesta dice que es local.** Lleva su procedencia y el aviso de
     que no ha pasado por el enjambre. Si el atajo se equivoca, se ve en la
     pantalla, no en un registro que nadie abre.

CÓMO SE REFUTA ESTO
===================
`tests/test_atajo_local.py` lo intenta por los dos lados: que no atajen los
encargos de trabajo, y que un atajo indebido sea detectable. Si un encargo que
exige deliberación acaba aquí, el mecanismo se retira — la velocidad que cuesta
una respuesta equivocada no es velocidad.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Lo que NUNCA ataja, aunque Lilim creyera tener la respuesta.
#:
#: No es una lista de temas: es una lista de VERBOS DE TRABAJO. Un encargo que
#: pide construir, cambiar o comprobar algo no se satisface con un dato, por
#: correcto que sea el dato. La diferencia entre «qué controles tiene la Vita»
#: y «arregla el mapeo de controles de la Vita» es exactamente esta lista.
VERBOS_DE_TRABAJO = (
    "arregla", "arreglar", "corrige", "corregir", "implementa", "implementar",
    "escribe", "escribir", "crea", "crear", "haz", "hacer", "construye",
    "construir", "compila", "compilar", "ejecuta", "ejecutar", "prueba",
    "probar", "analiza", "analizar", "revisa", "revisar", "refactoriza",
    "optimiza", "optimizar", "porta", "portar", "traduce el código",
    "depura", "depurar", "diagnostica", "borra", "borrar", "instala",
    "actualiza", "actualizar", "genera", "generar", "añade", "agrega",
    "modifica", "modificar", "mejora", "mejorar", "explica por qué",
)


def _pide_trabajo(texto: str) -> bool:
    t = (texto or "").lower()
    return any(v in t for v in VERBOS_DE_TRABAJO)


def consultar(command: str) -> dict | None:
    """La respuesta local si la hay, o `None` para que hable el enjambre.

    Devuelve un diccionario con el texto ya formado y la clasificación que lo
    justificó, para que quien lo entregue no tenga que volver a decidir nada.
    """
    texto = (command or "").strip()
    if len(texto) < 4:
        return None

    # Freno 1: los verbos de trabajo mandan sobre todo lo demás.
    if _pide_trabajo(texto):
        return None

    try:
        from vmagi.modules.lilim import responde_si_sabe
        from vmagi.modules.lilim.mielina import clasificar_intencion_local
    except Exception as e:                            # pragma: no cover
        logger.debug("[atajo] la capa local no está disponible: %s", e)
        return None

    # Freno 2: el clasificador local, que es puro texto y cuesta 0 ms.
    intencion = clasificar_intencion_local(texto)
    if intencion != "memoria_epd":
        return None

    # Freno 3: y aun así, solo si de verdad lo sabe.
    try:
        respuesta = responde_si_sabe(texto)
    except Exception as e:                            # pragma: no cover
        logger.warning("[atajo] la consulta local falló: %s", e)
        return None
    if not respuesta or not respuesta.strip():
        return None

    return {"texto": respuesta.strip(), "intencion": intencion}


def redactar(command: str, atajo: dict) -> str:
    """El texto que ve el usuario, con la etiqueta de que no hubo debate.

    La etiqueta no es cortesía: es lo que permite que el usuario detecte un
    atajo indebido. Sin ella, una respuesta de índice y una deliberada se leen
    igual, y entonces el error de esta capa sería invisible justo para quien
    puede corregirlo.
    """
    return (
        f"{atajo['texto']}\n\n"
        f"---\n"
        f"*Respondido por la capa local en milisegundos, sin consultar a los "
        f"modelos: este dato ya estaba indexado con su procedencia. El enjambre "
        f"no ha deliberado. Si esperabas un análisis y no un dato, vuelve a "
        f"pedirlo diciendo qué quieres que se haga con él.*"
    )


async def intentar(orq, task_id: str, command: str, entrada=None) -> bool:
    """Resuelve la tarea en local si se puede. Devuelve si lo hizo.

    Todo el mecanismo vive aquí y el orquestador solo pregunta, por dos
    motivos. Uno de diseño: el porqué va pegado a la pieza, no al sitio desde
    donde se la llama. Y uno medido: el trinquete de líneas de
    `orchestrator.py` se puso rojo cuando metí ahí los dos métodos, e hizo de
    detector de humo — el fichero no tenía que crecer, la pieza tenía que
    tener casa propia.

    Un atajo que revienta NO puede tumbar la tarea: su promesa es ahorrar
    tiempo, y fallar hacia el enjambre cuesta lo de siempre.
    """
    try:
        encontrado = consultar(command)
    except Exception as e:                            # pragma: no cover
        logger.warning("[atajo] falló; sigue el enjambre: %s", e)
        return False
    if encontrado is None:
        return False

    from vmagi.core.bus import BusEvent
    orq.latest_task_id = task_id
    await publicar(orq.bus, BusEvent, task_id, command, encontrado)
    orq._cerrar_entrada(entrada, task_id)
    return True


async def publicar(bus, BusEvent, task_id: str, command: str,
                   atajo: dict) -> None:
    """Entrega la respuesta local con el MISMO contrato que usa Casper.

    Se reusa `AGENT_POST` con `role="resultado_final"` a propósito: la ventana
    ya sabe pintar eso, ya lo guarda en el historial y ya lo cuenta como
    respuesta. Un suceso nuevo habría obligado a tocar el contrato del bus, la
    interfaz y el almacén para no ganar nada — y habría dejado la respuesta
    local fuera del historial hasta que alguien se acordara de las tres.

    `BusEvent` llega por argumento en vez de importarse aquí porque el
    orquestador ya lo tiene cargado y este módulo no debe arrastrar el núcleo
    del bus solo para publicar.
    """
    texto = redactar(command, atajo)
    logger.info("[SWARM] %s resuelta en local: cero llamadas de red", task_id)
    await bus.publish(BusEvent(
        topic="TERMINAL_OUT",
        payload={"content": "[LILIM] Respondido en local: el dato ya estaba "
                            "indexado. Cero llamadas de red."}))
    await bus.publish(BusEvent(
        topic="AGENT_POST",
        payload={"type": "AGENT_POST", "task_id": task_id, "agent": "LILIM",
                 "role": "resultado_final", "provider": "local",
                 "family": "lilim", "family_expected": "lilim",
                 "degraded": None, "inservible": None, "content": texto,
                 "changes": 0, "stats": "LOCAL"}))
