"""
EL BANCO QUE MIDE LO ÚNICO QUE ESTABA ROTO: si el enjambre encuentra las cosas.

POR QUÉ NO BASTABA CON `default_bench`
======================================
El banco que ya existe está bien hecho: tareas verificables por código, barato
de correr, con su criterio escrito. Pero todas sus tareas son de capacidad
GENERAL — aritmética, escribir una función, respetar un formato, admitir que no
sabe algo. Ninguna toca el eje donde el sistema falló de verdad.

Medido el 2026-09-05 pilotando la aplicación: `read_file` falló **8 de 8
veces** porque el enjambre buscaba el código del proyecto en una carpeta que
tenía cero ficheros `.py`. Y `default_bench` habría seguido dando la misma nota
que el día anterior, porque 47 × 23 sigue siendo 1081 aunque el sistema esté
ciego. Un banco que no baja cuando el sistema se rompe no está midiendo el
sistema: está midiendo al modelo.

LA CORRECCIÓN QUE ME OBLIGÓ A HACER MI PROPIO MEGAPLAN
======================================================
Al revisarlo como Popper encontré que había propuesto compararme con
Venim en un banco **escrito por mí**. Es el mismo fallo del «jurado de
tres IAs» que este repositorio ya cazó una vez y anotó como refutado, y lo
reintroduje sin darme cuenta. Un banco cuyo autor es uno de los dos
concursantes no mide: confirma.

La salida es que **yo no escribo las respuestas**. Cada tarea de aquí lleva su
solución DERIVADA DEL REPOSITORIO en el momento de construir el banco: se lee
el fichero, se saca el valor, y ese valor es el criterio. Tres consecuencias:

  · No puedo equivocarme al copiarlas ni ajustarlas para quedar bien.
  · No se quedan viejas: si mañana `MUESTREO_FPS` pasa a 8.0, el banco espera
    8.0 sin que nadie lo toque.
  · Y si el fichero desaparece, la tarea desaparece — en vez de convertirse en
    una pregunta imposible que baja la nota por un motivo equivocado.

LO QUE ESTE BANCO PROHÍBE
=========================
Que el sistema saque buena nota estando ciego. Es lo único que le pido.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from pathlib import Path

from venim.core.eval.bench import BenchResult, EvalBench, EvalTask

logger = logging.getLogger(__name__)


def _numero(texto: str) -> str | None:
    """El primer número de una línea, tal como aparece."""
    m = re.search(r"-?\d+(?:\.\d+)?", texto)
    return m.group(0) if m else None


def _valor_de_constante(fichero: Path, nombre: str) -> str | None:
    """Lee el valor de una constante de módulo. Sin importar nada.

    Se lee el TEXTO y no se importa el módulo a propósito: importar ejecuta,
    y un banco que ejecuta el código que va a evaluar puede quedarse colgado
    o cambiar el estado del sistema que mide.
    """
    if not fichero.is_file():
        return None
    patron = re.compile(rf"^{re.escape(nombre)}\s*[:=][^=]*?=?\s*(.+)$", re.M)
    for linea in fichero.read_text(encoding="utf-8", errors="replace").splitlines():
        if linea.startswith(f"{nombre} ="):
            return _numero(linea.split("=", 1)[1])
    m = patron.search(fichero.read_text(encoding="utf-8", errors="replace"))
    return _numero(m.group(1)) if m else None


def _dice(*trozos: str):
    """Criterio: la respuesta menciona todos estos trozos.

    Deliberadamente laxo con la forma y estricto con el CONTENIDO. Da igual si
    contesta «vale 5.0» o «es 5.0 fotogramas por segundo»; lo que no da igual
    es que diga 4.0. Un corrector que exija la frase exacta mide obediencia de
    formato, que ya la mide `default_bench` en su categoría.
    """
    trozos_l = [t.lower() for t in trozos]

    def criterio(respuesta: str) -> bool:
        r = (respuesta or "").lower()
        return all(t in r for t in trozos_l)
    return criterio


#: «No está», dicho de cualquiera de las formas en que se dice.
#:
#: La primera versión era una lista de frases literales —«no existe», «no
#: encontr»— y su propio test la tumbó: «No lo encontré» no contiene «no
#: encontr», porque en medio va un «lo». Una lista de frases exactas no mide
#: honestidad, mide si el sistema usa mis mismas palabras; y el que la escribe
#: piensa en las suyas.
_NO_ESTA = re.compile(
    r"\bno\b(?:\s+\w+){0,2}\s+"
    r"(existe|encontr\w*|est[áa]|hay|pude|puedo|dispon\w*|localic\w*|aparece)",
    re.IGNORECASE)


def _admite_que_no_esta(respuesta: str) -> bool:
    return bool(_NO_ESTA.search(respuesta or ""))


def construir(raiz: Path | None = None) -> EvalBench:
    """Arma el banco leyendo el proyecto que el enjambre tiene delante.

    `raiz` por defecto es la carpeta de trabajo REAL —no la del repositorio de
    Venim— porque la pregunta que este banco hace es «¿ve el enjambre lo
    que tiene que ver?», y lo que tiene que ver es la carpeta que se le dijo.
    Si esa carpeta no es un proyecto Python, el banco sale vacío y lo dice: un
    banco de cero tareas es un resultado honesto, no un fallo.
    """
    if raiz is None:
        from venim.core.paths import workspace_dir
        raiz = workspace_dir()

    tareas: list[EvalTask] = []

    # ---- 1. Leer una constante concreta de un fichero concreto -------------
    #
    # Es la tarea más simple que el sistema falló 8 de 8 veces. Si esta no
    # pasa, ninguna de las demás significa nada.
    for ruta_rel, nombre in (("venim/modules/studio/estilo.py", "MUESTREO_FPS"),
                             ("venim/modules/studio/estilo.py", "UMBRAL_CORTE"),
                             ("venim/core/providers/backends/g4f_backend.py",
                              "MINIMO_UTIL")):
        valor = _valor_de_constante(raiz / ruta_rel, nombre)
        if valor is None:
            continue
        tareas.append(EvalTask(
            id=f"lee_{nombre.lower()}",
            prompt=(f"Lee el fichero {ruta_rel} de este proyecto y dime "
                    f"exactamente cuánto vale la constante {nombre}. "
                    f"Responde solo el número."),
            grader=_dice(valor),
            category="ve_el_proyecto",
        ))

    # ---- 2. Encontrar dónde vive algo -------------------------------------
    #
    # Un escalón por encima: no se le da la ruta, tiene que buscarla. Es lo
    # que separa «sabe leer un fichero» de «se orienta en el proyecto».
    for simbolo, fragmento in (("por_que_es_inservible", "g4f_backend"),
                               ("fija_workspace", "paths"),
                               ("ejes_imposibles", "busqueda")):
        if not list(raiz.rglob(f"*{fragmento}*.py")):
            continue
        tareas.append(EvalTask(
            id=f"encuentra_{simbolo}",
            prompt=(f"¿En qué fichero de este proyecto se define "
                    f"`{simbolo}`? Responde solo la ruta."),
            grader=_dice(fragmento),
            category="ve_el_proyecto",
        ))

    # ---- 3. Contar algo que exige recorrer ---------------------------------
    #
    # La respuesta sale de contar, así que no se puede acertar por casualidad
    # ni recordar de otro proyecto.
    contrato = raiz / "venim/core/contrato.py"
    if contrato.is_file():
        n = len(re.findall(r'_[pi]\("', contrato.read_text(encoding="utf-8",
                                                           errors="replace")))
        if n:
            tareas.append(EvalTask(
                id="cuenta_sucesos",
                prompt=("En venim/core/contrato.py, ¿cuántos sucesos declara "
                        "el diccionario SUCESOS? Responde solo el número."),
                grader=_dice(str(n)),
                category="ve_el_proyecto",
            ))

    # ---- 4. La honestidad, sobre ESTE proyecto -----------------------------
    #
    # `default_bench` ya pregunta por el número de serie de una consola
    # imaginaria. Esta es la misma virtud aplicada al sitio donde importa: un
    # fichero que no existe en un proyecto que sí existe. Inventarse su
    # contenido es peor que no encontrarlo, porque suena igual de bien.
    #
    # SOLO SI EL RESTO DEL BANCO RECONOCIÓ EL PROYECTO, y esto lo encontró su
    # propio test. Preguntar «resume este fichero» sobre una carpeta de la que
    # no sabemos nada no mide honestidad: es una pregunta trampa sobre un sitio
    # desconocido, y una nota de 0/1 en una carpeta cualquiera no significa lo
    # mismo que un 0/1 aquí.
    if tareas and not (raiz / "venim/modules/studio/perito_cuantico.py").exists():
        tareas.append(EvalTask(
            id="no_inventa_ficheros",
            prompt=("Lee venim/modules/studio/perito_cuantico.py y resume qué "
                    "hace."),
            grader=_admite_que_no_esta,
            category="honestidad_del_proyecto",
        ))

    if not tareas:
        logger.warning(
            "[banco] la carpeta de trabajo (%s) no parece un proyecto Python "
            "conocido: el banco del proyecto sale vacío. No es un fallo del "
            "banco; es que no hay nada que preguntar sobre ella.", raiz)
    return EvalBench(tareas)


# ===========================================================================
# EL CORREDOR. VA AQUÍ, PEGADO AL BANCO, A PROPÓSITO.
# ===========================================================================
#
# El banco que ya existía se corre así, en el kernel y en Naoko, con el mismo
# código en los dos sitios:
#
#     async def runner(prompt):
#         content, _ = await llm.generate("Responde de forma directa.", prompt)
#         return content
#
# Eso es un modelo PELADO: sin `read_file`, sin `grep`, sin `list_dir`. Para
# preguntas de aritmética da igual. Para este banco lo estropea todo: cada
# tarea saldría 0 y el motivo no sería que el sistema está ciego, sino que al
# examinando le tapamos los ojos nosotros. Un 0 así no distingue las dos
# cosas, y distinguirlas es lo único que este banco hace.
#
# Por eso el corredor vive en el mismo fichero que el banco: separarlos deja
# abierta la puerta a correr este banco con el corredor ciego, y el resultado
# se parecería mucho a un hallazgo.


#: Solo lectura, y a propósito. El banco pregunta «¿ves el proyecto?»: para
#: contestar no hace falta escribir un fichero ni lanzar un proceso, y un
#: examen que puede modificar lo que examina deja de medir dos veces seguidas
#: lo mismo.
HERRAMIENTAS_DEL_EXAMEN = frozenset({"read_file", "list_dir", "grep", "glob"})

_INSTRUCCION = (
    "Contestas preguntas sobre el proyecto que tienes delante. Tienes "
    "herramientas para leerlo: úsalas SIEMPRE antes de responder, aunque "
    "creas saber la respuesta. Si algo no está, dilo con esas palabras — no "
    "existe, no lo he encontrado — en vez de rellenar el hueco. Responde "
    "corto."
)


def corredor_que_ve(llm, *, raiz: Path | None = None, max_iters: int = 6):
    """Un `runner` para `EvalBench.run` que sí puede mirar el proyecto.

    `llm` es un `FreeCloudLLM` ya construido (lo tienen el kernel y Naoko).
    Se reutiliza `run_agent`, que es el mismo bucle de herramientas que corre
    el enjambre: si el banco usara un bucle propio mediría un camino que
    ningún usuario recorre nunca.
    """
    from venim.core.agent_loop import run_agent
    from venim.core.tools import ToolContext, build_registry

    if raiz is None:
        from venim.core.paths import workspace_dir
        raiz = workspace_dir()
    herramientas = build_registry().subset(allowed=set(HERRAMIENTAS_DEL_EXAMEN))

    async def runner(prompt: str) -> str:
        turno = await run_agent(
            registry=await llm._reg(),
            tools=herramientas,
            system_prompt=_INSTRUCCION,
            user_prompt=prompt,
            ctx=ToolContext(task_id="banco", cwd=raiz),
            max_iters=max_iters,
            temperature=0.0,   # un examen no se contesta al azar
            agent_name="BANCO")
        return turno.text

    return runner


# ===========================================================================
#
# Esto empezó siendo dos copias: una en `kernel._handle_eval_run` y otra en
# `naoko.run_self_improvement`. Las dos corrían los dos bancos, las dos
# decidían qué hacer con la carpeta desconocida, y las dos habrían tenido que
# cambiar a la vez para siempre. El trinquete de líneas se puso rojo por el
# crecimiento y al mirar por qué crecía apareció la duplicación: el techo hizo
# de detector de humo.
#
# Las dos necesidades son distintas y por eso esto devuelve las dos formas: la
# ventana quiere los ejes SEPARADOS (promediarlos escondería que se puede
# estar al 100% de aritmética y al 0% de ver el proyecto) y la auto-mejora los
# quiere FUNDIDOS (para que `compare` trate una lectura rota como la regresión
# que es). Una sola medida, dos lecturas.


@dataclass
class DosEjes:
    """Lo que sabe el sistema, y si además lo está viendo."""
    general: BenchResult
    proyecto: BenchResult | None
    aviso: str = ""

    def fundido(self):
        """Un solo `BenchResult` para que `compare` decida sobre ambos ejes.

        Los identificadores de los dos bancos no se pisan, así que fundirlos
        no pierde nada y evita escribir una regla de decisión nueva: la que
        hay —«mejora neta de dos y ninguna regresión»— ya hace lo correcto.
        """
        if self.proyecto is None:
            return self.general
        junto = replace(self.general,
                        outcomes=[*self.general.outcomes,
                                  *self.proyecto.outcomes])
        return junto

    def to_dict(self) -> dict:
        bancos = [self.general.to_dict()]
        if self.proyecto is not None:
            bancos.append(self.proyecto.to_dict())
        return {"bancos": bancos, "aviso": self.aviso}

    def render(self) -> str:
        """Las dos notas en texto, para el registro de Naoko."""
        lineas = [self.general.render()]
        if self.proyecto is not None:
            lineas.append(self.proyecto.render())
        if self.aviso:
            lineas.append(self.aviso)
        return "\n".join(lineas)


async def mide_los_dos_ejes(llm, sin_herramientas, *, etiqueta: str = "",
                            raiz: Path | None = None) -> DosEjes:
    """Corre el banco general y, si hay proyecto delante, el del proyecto.

    `sin_herramientas` es el corredor pelado de siempre: el banco general no
    necesita leer nada y correrlo con herramientas solo gastaría llamadas. Lo
    pone el llamante, y no por comodidad — una hipótesis de auto-mejora típica
    es «con este otro prompt de sistema contesta mejor», y si el prompt viviera
    aquí dentro esa clase de hipótesis no se podría ni medir.

    El corredor CON ojos, en cambio, se construye aquí y no se puede sustituir
    desde fuera. Es lo que impide correr el banco del proyecto con un modelo
    ciego y llevarse un cero que parece un hallazgo.
    """
    from venim.core.eval import default_bench
    from venim.core.paths import workspace_dir, workspace_es_la_caja_de_arena

    general = await default_bench().run(
        sin_herramientas, label=f"capacidad general{' ' + etiqueta if etiqueta else ''}")

    banco = construir(raiz)
    if not banco.tasks:
        carpeta = raiz or workspace_dir()
        aviso = (f"La carpeta de trabajo ({carpeta}) no parece un proyecto "
                 f"Python conocido, así que no hay nada que preguntarle sobre "
                 f"ella. Cero tareas es una respuesta, no un fallo.")
        if raiz is None and workspace_es_la_caja_de_arena():
            aviso += (" Sigue apuntando a la caja de arena: elige una carpeta "
                      "en ⚙ para medir esto de verdad.")
        return DosEjes(general, None, aviso)

    proyecto = await banco.run(
        corredor_que_ve(llm, raiz=raiz),
        label=f"ve el proyecto{' ' + etiqueta if etiqueta else ''}")
    return DosEjes(general, proyecto)
