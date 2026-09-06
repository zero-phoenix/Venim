"""
VAINA DE MIELINA — Acelerador neuro-computacional de MAGI (megaplan v13).

METÁFORA BIOLÓGICA Y FUNCIÓN
============================
En el sistema nervioso, la mielina envuelve los axones para permitir la
conducción saltatoria (transmisión hasta 100 veces más veloz).

En MAGI, Lilim actúa como la vaina de mielina: una capa local ultrarrápida
(Qwen 2.5 1.5B Instruct en KoboldCpp + memoria EPD) que envuelve a:
  - MELCHIOR:  Especulación y andamiaje preliminar (<250 ms) antes de la nube.
  - BALTHASAR: Pre-auditoría local y chequeo estático de defectos obvios.
  - CASPER:    Destilación y compresión de contexto de debates extensos.
  - NAOKO:     Visión multimodal local para inspección de capturas web/DOM.
  - RITSUKO:   Enrutamiento semántico instantáneo y caché sin latencia.
"""
from __future__ import annotations

import ast
import logging

from .cliente_kobold import ClienteKobold

logger = logging.getLogger(__name__)

_cliente_singleton: ClienteKobold | None = None


def _obtener_cliente() -> ClienteKobold:
    """Devuelve el cliente singleton de KoboldCpp."""
    global _cliente_singleton
    if _cliente_singleton is None:
        _cliente_singleton = ClienteKobold()
    return _cliente_singleton



def pre_auditoria_estatica(codigo: str) -> list[str]:
    """
    Inspección estática determinista en 0 ms para asistir a Balthasar.
    Detecta problemas de sintaxis, funciones vacías o recursos no manejados.
    """
    defectos: list[str] = []
    if not codigo or not codigo.strip():
        return ["Código vacío o ausente"]

    try:
        arbol = ast.parse(codigo)
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef):
                if len(nodo.body) == 1 and isinstance(nodo.body[0], ast.Pass):
                    defectos.append(f"Función '{nodo.name}' solo contiene 'pass' sin implementar.")
            elif isinstance(nodo, ast.Try):
                for handler in nodo.handlers:
                    if handler.type is None:
                        defectos.append("Uso de 'except:' desnudo sin atrapar excepción específica.")
    except SyntaxError as err:
        defectos.append(f"SyntaxError en línea {err.lineno}: {err.msg}")
    except Exception:
        pass

    return defectos


#: Lo que se supo la última vez sobre si KoboldCpp está levantado, y cuándo.
#:
#: EL ARREGLO QUE ESTA CAPA NECESITABA PARA NO SER UN IMPUESTO
#: ==========================================================
#: `esta_disponible(timeout=0.8)` cuesta hasta 0,8 s cuando NO hay nada
#: escuchando, que es el caso de cualquiera que no haya instalado KoboldCpp —
#: es decir, el caso por defecto. Preguntarlo en cada turno convertía un
#: acelerador opcional en un peaje de 0,8 s por crítica para quien no lo usa.
#:
#: Con memoria, el que no lo tiene lo paga UNA vez por minuto en vez de
#: siempre, y el que sí lo tiene no nota nada. El minuto es corto a propósito:
#: levantar KoboldCpp a mitad de sesión tiene que funcionar sin reiniciar.
_ULTIMA_SONDA: tuple[float, bool] | None = None
_VALIDEZ_SONDA_S = 60.0


async def _kobold_esta_vivo() -> bool:
    """Si hay un KoboldCpp al que preguntar. Apagado salvo que se pida.

    LA SONDA NO SE HACE «POR SI ACASO», Y ESO LO ENSEÑÓ LA SUITE
    ===========================================================
    La primera versión sondeaba siempre, memoizando un minuto. Parecía barato
    y no lo era: `esta_disponible(timeout=0.8)` solo cuesta poco cuando el
    sistema operativo RECHAZA la conexión al instante. Donde el puerto está
    filtrado en vez de cerrado —un cortafuegos, un contenedor— se agota el
    plazo entero, y la suite de tests pasó de correr en minutos a arrastrarse.

    Un acelerador opcional que cobra peaje al que no lo usa está mal diseñado,
    por pequeño que sea el peaje. Así que la capa neuronal se ACTIVA
    explícitamente: quien levanta KoboldCpp lo dice, y quien no, no paga nada
    ni una vez por minuto.

    La parte que de verdad rinde —`pre_auditoria_estatica`, AST puro— nunca
    dependió de esto y sigue funcionando siempre.
    """
    import os
    if not os.getenv("VENICEMAGI_KOBOLD"):
        return False

    global _ULTIMA_SONDA
    import time
    ahora = time.monotonic()
    if _ULTIMA_SONDA is not None and (ahora - _ULTIMA_SONDA[0]) < _VALIDEZ_SONDA_S:
        return _ULTIMA_SONDA[1]
    vivo = await _obtener_cliente().esta_disponible(timeout=0.8)
    _ULTIMA_SONDA = (ahora, vivo)
    if not vivo:
        logger.warning(
            "[mielina] VENICEMAGI_KOBOLD está puesto pero KoboldCpp no "
            "responde en %s. La crítica neuronal local queda desactivada "
            "durante %.0f s.", _obtener_cliente().url_base, _VALIDEZ_SONDA_S)
    return vivo


async def lubricar_critica(
    propuesta: str, ejes: list[str] | None = None
) -> list[str]:
    """
    Pre-auditoría rápida para Balthasar.
    Combina escaneo estático local con evaluación neural si KoboldCpp está activo.

    La parte estática funciona SIEMPRE y no depende de nada. La neuronal es un
    extra que aparece solo si hay un KoboldCpp levantado; sin él, esta función
    devuelve exactamente lo que devolvería `pre_auditoria_estatica`, sin
    penalización de tiempo apreciable.
    """
    defectos = pre_auditoria_estatica(propuesta)

    cliente = _obtener_cliente()
    if await _kobold_esta_vivo():
        ejes_txt = ", ".join(ejes) if ejes else "seguridad, rendimiento, coherencia"
        prompt = (
            f"Como crítico técnico implacable, evalúa la siguiente propuesta bajo "
            f"los ejes: {ejes_txt}.\n"
            f"Propuesta:\n{propuesta[:1200]}\n\n"
            f"Lista hasta 3 objeciones o defectos técnicos severos en viñetas cortas. "
            f"Si el código es óptimo, responde exactamente: SIN OBJECIONES."
        )
        res = await cliente.generar(prompt, max_tokens=200, temperature=0.1, timeout=10.0)
        if res and "SIN OBJECIONES" not in res.upper():
            for linea in res.splitlines():
                ln = linea.strip("- *").strip()
                if ln and len(ln) > 10:
                    defectos.append(ln)

    return defectos[:5]




def clasificar_intencion_local(texto: str) -> str:
    """
    Enrutamiento semántico ultraveloz (0 ms):
      - 'memoria_epd': Respuestas instantáneas curadas de Lilim.
      - 'comando_directo': Ejecución de orden / CLI.
      - 'deliberacion_enjambre': Tareas complejas de programación y diseño.
    """
    t = texto.strip().lower()
    if not t:
        return "vacio"
    if t.startswith(("/", "run ", "git ", "python ", "npm ", "task.cancel")):
        return "comando_directo"
    palabras_epd = ("controles", "decomp", "repos", "novedades", "mando", "vita")
    if any(p in t for p in palabras_epd) and len(t.split()) < 12:
        return "memoria_epd"
    return "deliberacion_enjambre"
