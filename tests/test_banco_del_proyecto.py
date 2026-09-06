"""
El banco que baja cuando el sistema se queda ciego.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«La nota del banco cae si el enjambre deja de ver el proyecto.»

Importa porque el 2026-09-05 el sistema falló `read_file` **8 de 8 veces** y
`default_bench` habría dado exactamente la misma nota que el día anterior: 47
por 23 sigue siendo 1081 aunque el sistema esté ciego. Un banco que no baja
cuando el sistema se rompe no mide el sistema, mide al modelo.

Y LA SEGUNDA, QUE ES LA QUE ME CORRIGE A MÍ
===========================================
«Las respuestas correctas no las escribe quien construye el banco.»

En mi propio megaplan propuse compararme con VeniceMAGI en un banco escrito
por mí — el mismo fallo del jurado circular que este repositorio ya cazó una
vez. Aquí cada respuesta se DERIVA del repositorio al construir el banco. Si
mañana `MUESTREO_FPS` pasa a 8.0, el banco espera 8.0 sin que nadie lo toque.
Y si alguien pudiera pasar el banco sin mirar el proyecto, este fichero
debería ponerse rojo.
"""
from __future__ import annotations

import pathlib

import pytest

from vmagi.core.eval import banco_del_proyecto as B


@pytest.fixture
def proyecto(tmp_path):
    """Un proyecto de mentira con las mismas formas que el de verdad."""
    (tmp_path / "vmagi/modules/studio").mkdir(parents=True)
    (tmp_path / "vmagi/core/providers/backends").mkdir(parents=True)
    (tmp_path / "vmagi/core").mkdir(exist_ok=True)
    (tmp_path / "vmagi/modules/studio/estilo.py").write_text(
        "MUESTREO_FPS = 5.0\nUMBRAL_CORTE = 0.38\n", encoding="utf-8")
    (tmp_path / "vmagi/core/providers/backends/g4f_backend.py").write_text(
        "MINIMO_UTIL = 12\n\ndef por_que_es_inservible(x):\n    return None\n",
        encoding="utf-8")
    (tmp_path / "vmagi/core/paths.py").write_text(
        "def fija_workspace(r):\n    return r\n", encoding="utf-8")
    (tmp_path / "vmagi/core/contrato.py").write_text(
        'X = (_p("a.b"), _p("c.d"), _i("e.f", "x", "y"))\n', encoding="utf-8")
    return tmp_path


# ================================== las respuestas salen del código

def test_EL_CENTRAL_la_solucion_se_lee_del_proyecto_no_la_escribo_yo(proyecto):
    """LA REFUTACIÓN DEL JURADO CIRCULAR.

    Se cambia el valor en el fichero y el banco tiene que cambiar de opinión
    solo. Si aprobara la respuesta vieja, las soluciones estarían escritas a
    mano en algún sitio y yo sería juez y parte.
    """
    tarea = next(t for t in B.construir(proyecto).tasks
                 if t.id == "lee_muestreo_fps")
    assert tarea.grade("vale 5.0")
    assert not tarea.grade("vale 8.0")

    (proyecto / "vmagi/modules/studio/estilo.py").write_text(
        "MUESTREO_FPS = 8.0\nUMBRAL_CORTE = 0.38\n", encoding="utf-8")
    tarea2 = next(t for t in B.construir(proyecto).tasks
                  if t.id == "lee_muestreo_fps")
    assert tarea2.grade("vale 8.0"), (
        "el banco sigue esperando el valor viejo: las respuestas están "
        "escritas a mano en vez de leídas, y entonces las escribí yo")
    assert not tarea2.grade("vale 5.0")


def test_una_constante_que_no_existe_no_genera_pregunta(tmp_path):
    """Si el fichero no está, la tarea no está.

    La alternativa —dejar la pregunta y suspenderla— bajaría la nota por un
    motivo equivocado: no por que el sistema no vea, sino por que le
    preguntamos algo que no tiene respuesta. Es la quinta regla otra vez.
    """
    (tmp_path / "vmagi").mkdir()
    ids = [t.id for t in B.construir(tmp_path).tasks]
    assert "lee_muestreo_fps" not in ids
    assert "cuenta_sucesos" not in ids


def test_un_banco_vacio_es_un_resultado_honesto(tmp_path):
    """Apuntado a una carpeta que no es un proyecto Python, sale vacío y lo
    dice en el registro. Cero tareas es una respuesta; inventarse tareas
    sobre una carpeta que no se conoce, no."""
    banco = B.construir(tmp_path)
    assert len(banco.tasks) == 0


# ================================== lo que el banco tiene que prohibir

def test_no_se_puede_aprobar_sin_mirar_el_proyecto(proyecto):
    """LA PRUEBA QUE JUSTIFICA QUE ESTE BANCO EXISTA.

    Se simula un sistema ciego pero elocuente: contesta con seguridad y sin
    haber abierto un fichero. `default_bench` le habría dado buena nota —47
    por 23 no depende del proyecto—; este tiene que suspenderlo entero.
    """
    respuestas_de_ciego = [
        "El valor de la constante es 42.",
        "Está definida en el módulo principal del proyecto.",
        "Hay unos veinte sucesos declarados.",
        "El fichero implementa un perito cuántico para análisis visual.",
    ]
    banco = B.construir(proyecto)
    assert banco.tasks, "el proyecto de prueba no generó tareas"
    for t in banco.tasks:
        for r in respuestas_de_ciego:
            assert not t.grade(r), (
                f"la tarea {t.id} aprueba «{r}», que se puede escribir sin "
                f"haber abierto un solo fichero")


def test_inventarse_un_fichero_que_no_existe_suspende(proyecto):
    """Peor que no encontrarlo es inventárselo, porque suena igual de bien.

    `default_bench` ya mide esta virtud con el número de serie de una consola
    imaginaria; aquí se mide sobre un fichero inexistente DE ESTE proyecto,
    que es donde el sistema tiene tentación de rellenar el hueco.
    """
    t = next(x for x in B.construir(proyecto).tasks
             if x.id == "no_inventa_ficheros")
    assert t.grade("Ese fichero no existe en el proyecto.")
    assert t.grade("No lo encontré en el árbol.")
    assert not t.grade(
        "Implementa un perito cuántico que analiza fotogramas con "
        "superposición de estados y devuelve un veredicto probabilístico.")


def test_el_corrector_mira_el_contenido_y_no_la_forma(proyecto):
    """Da igual cómo lo diga; no da igual qué diga. La obediencia de formato ya
    la mide `default_bench` en su propia categoría."""
    t = next(x for x in B.construir(proyecto).tasks
             if x.id == "lee_umbral_corte")
    for forma in ("0.38", "vale 0.38", "UMBRAL_CORTE = 0.38",
                  "Es 0.38, definido en estilo.py"):
        assert t.grade(forma), forma


def test_contar_exige_recorrer(proyecto):
    """La respuesta sale de contar, así que no se acierta de memoria."""
    t = next(x for x in B.construir(proyecto).tasks if x.id == "cuenta_sucesos")
    assert t.grade("Declara 3 sucesos.")
    assert not t.grade("Declara 50 sucesos.")


# ================================== el corredor, que es media prueba

def test_EL_OTRO_CENTRAL_el_corredor_del_examen_puede_leer(proyecto):
    """UN EXAMEN CON LOS OJOS TAPADOS NO MIDE CEGUERA.

    El banco que ya existía se corre con un modelo PELADO:

        content, _ = await llm.generate("Responde de forma directa.", prompt)

    Sin `read_file`, sin `grep`. Para «cuánto es 47 por 23» da igual. Para
    «¿cuánto vale MUESTREO_FPS?» sale 0 siempre, y ese 0 no distingue las dos
    únicas cosas que importan: que el sistema esté ciego, o que le hayamos
    tapado los ojos nosotros al examinarlo. Distinguirlas es lo único que este
    banco hace, así que el corredor va con el banco.
    """
    from vmagi.core.eval.banco_del_proyecto import HERRAMIENTAS_DEL_EXAMEN

    assert "read_file" in HERRAMIENTAS_DEL_EXAMEN, (
        "sin leer ficheros, todas las tareas de este banco salen 0 por un "
        "motivo que no es el que el banco quiere medir")


def test_el_examen_no_puede_modificar_lo_que_examina(proyecto):
    """Solo lectura, y no por seguridad.

    Un banco que puede escribir deja de medir dos veces seguidas lo mismo: la
    segunda pasada encontraría el proyecto que cambió la primera. Y la
    auto-mejora corre el banco ANTES y DESPUÉS del cambio, o sea justo dos
    veces seguidas.
    """
    from vmagi.core.eval.banco_del_proyecto import HERRAMIENTAS_DEL_EXAMEN

    prohibidas = {"write_file", "edit_file", "delete_path", "run_command",
                  "python_exec", "undo"}
    assert not (set(HERRAMIENTAS_DEL_EXAMEN) & prohibidas), (
        "el corredor del examen puede modificar el proyecto que examina")


@pytest.mark.asyncio
async def test_el_corredor_usa_las_herramientas_y_no_su_memoria(proyecto,
                                                                monkeypatch):
    """El corredor tiene que ACABAR llamando a `run_agent` con herramientas.

    Se comprueba interceptando la llamada: si algún día alguien lo sustituye
    por un `llm.generate` pelado «para que corra más rápido», esto se pone
    rojo. Es exactamente el cambio que parece una optimización y rompe la
    medida.
    """
    from vmagi.core.eval import banco_del_proyecto as B

    visto = {}

    async def falso_run_agent(**kw):
        visto.update(kw)

        class Turno:
            text = "5.0"
        return Turno()

    import vmagi.core.agent_loop as AL
    monkeypatch.setattr(AL, "run_agent", falso_run_agent)

    class FalsoLLM:
        async def _reg(self):
            return object()

    runner = B.corredor_que_ve(FalsoLLM(), raiz=proyecto)
    assert await runner("¿cuánto vale MUESTREO_FPS?") == "5.0"
    assert "read_file" in visto["tools"].names(), (
        "el corredor no lleva herramientas de lectura: contestaría de memoria")
    assert visto["ctx"].cwd == proyecto, (
        "el corredor mira otra carpeta distinta de la que se está midiendo")
    assert visto["temperature"] == 0.0, "un examen no se contesta al azar"


# ================================== el lazo, que es lo que se pidió

def test_EL_LAZO_un_cambio_que_ciega_al_sistema_se_rechaza():
    """LA REFUTACIÓN DE LA FASE 6.

    Se simula la decisión de la auto-mejora ante un cambio que mejora TRES
    tareas de capacidad general y rompe UNA de ver el proyecto. Con el banco
    viejo salía ACEPTADO —las tres suben, no hay regresión visible— y el
    sistema se quedaba con un cambio que lo deja ciego.

    Los dos bancos se funden en un `BenchResult` para que `compare` decida
    sobre los dos ejes sin necesitar ninguna regla nueva: su norma es «mejora
    neta de dos y NINGUNA regresión», y una lectura rota ya es una regresión.
    """
    from vmagi.core.eval.bench import BenchResult, TaskOutcome, compare

    def resultado(pares):
        return BenchResult([TaskOutcome(i, ok, 1.0) for i, ok in pares])

    antes = resultado([("suma", False), ("codigo", False), ("formato", False),
                       ("lee_muestreo_fps", True)])
    despues = resultado([("suma", True), ("codigo", True), ("formato", True),
                         ("lee_muestreo_fps", False)])

    c = compare(antes, despues)
    assert c.delta > 0, "el cambio sube la nota global: por eso engaña"
    assert not c.significant, (
        "aceptado un cambio que dejó al sistema sin encontrar los ficheros; "
        "es justo el fallo del 2026-09-05, aprobado por el propio banco")
    assert "lee_muestreo_fps" in c.broken


# ================================== una medida, dos lecturas

def _resultado(etiqueta, pares):
    from vmagi.core.eval.bench import BenchResult, TaskOutcome
    return BenchResult([TaskOutcome(i, ok, 1.0) for i, ok in pares],
                       label=etiqueta)


def test_la_ventana_ve_los_ejes_separados_y_la_decision_los_ve_juntos():
    """LAS DOS LECTURAS SON DISTINTAS A PROPÓSITO, Y LAS DOS HACEN FALTA.

    La ventana los quiere SEPARADOS: promediarlos escondería que se puede
    estar al 100% de aritmética y al 0% de ver el proyecto, que es exactamente
    lo que pasaba el 2026-09-05.

    La auto-mejora los quiere FUNDIDOS: `compare` decide por identificador y su
    regla es «mejora neta de dos y ninguna regresión». Fundiéndolos, una
    lectura rota cuenta como regresión sin escribir ninguna regla nueva.
    """
    from vmagi.core.eval.banco_del_proyecto import DosEjes

    medida = DosEjes(_resultado("capacidad general",
                                [("suma", True), ("codigo", True)]),
                     _resultado("ve el proyecto",
                                [("lee_muestreo_fps", False)]))

    d = medida.to_dict()
    assert [b["label"] for b in d["bancos"]] == ["capacidad general",
                                                 "ve el proyecto"]
    assert d["bancos"][0]["score"] == 1.0 and d["bancos"][1]["score"] == 0.0, (
        "los dos ejes salen mezclados: el número bueno tapa al malo")

    junto = medida.fundido()
    assert junto.total == 3 and junto.passed == 2
    assert set(junto.by_task()) == {"suma", "codigo", "lee_muestreo_fps"}
    assert medida.general.total == 2, (
        "fundir ha modificado el resultado original; la segunda vez que se "
        "lea daría otra cosa")


def test_la_ventana_lee_los_campos_que_el_banco_escribe():
    """EL FALLO QUE COMETÍ AL HACER ESTO, Y QUE ESTE TEST IMPIDE REPETIR.

    Cambié la forma del payload de `eval.result` —de un banco a dos— y dejé en
    `useMagiSocket.ts` el código que leía `payload.passed`. Compilaba, no
    lanzaba ningún error, y habría escrito en la terminal:

        [BANCO] undefined/undefined (0%)

    El contrato del bus declara qué sucesos existen, no qué campos llevan, así
    que nada lo habría cazado. Aquí se fija la FORMA que la ventana lee, con
    los nombres escritos: si cambia, esto se pone rojo y dice dónde mirar.
    """
    from vmagi.core.eval.banco_del_proyecto import DosEjes

    d = DosEjes(_resultado("capacidad general", [("suma", True)]),
                _resultado("ve el proyecto", [("lee", False)])).to_dict()

    assert set(d) >= {"bancos", "aviso"}, "useMagiSocket.ts:eval.result"
    for b in d["bancos"]:
        assert set(b) >= {"label", "passed", "total", "score",
                          "mean_latency_s", "tasks"}, (
            "la ventana (SystemPanel.tsx y useMagiSocket.ts) lee estos campos "
            "de cada banco; el que falte se pinta como «undefined»")


def test_sin_proyecto_delante_la_medida_sigue_siendo_una_medida():
    """Si la carpeta no es un proyecto conocido, queda el eje general y un
    aviso. Lo que no puede pasar es que el hueco cuente como suspenso: sería
    bajar la nota por un motivo que no es del sistema."""
    from vmagi.core.eval.banco_del_proyecto import DosEjes

    medida = DosEjes(_resultado("capacidad general", [("suma", True)]),
                     None, aviso="la carpeta no parece un proyecto")
    assert len(medida.to_dict()["bancos"]) == 1
    assert medida.to_dict()["aviso"]
    assert medida.fundido().total == 1


# ================================== el corredor tiene que tener ojos

def test_EL_CORREDOR_LLEVA_HERRAMIENTAS_DE_LECTURA():
    """EL FALLO QUE ESTUVE A PUNTO DE COMETER AL CONECTAR ESTO.

    El banco que ya existía se corre con un modelo PELADO — `llm.generate` y
    nada más — en el kernel y en Naoko, con el mismo código copiado en los dos
    sitios. Para preguntas de aritmética da igual. Para este banco lo estropea
    todo: cada tarea saldría 0 y el motivo no sería que el sistema está ciego,
    sino que le tapamos los ojos nosotros. Un 0 así no distingue las dos
    cosas, y distinguirlas es lo ÚNICO que este banco hace.

    Es la quinta regla otra vez: «no he podido comprobarlo» no es «está mal».
    """
    assert "read_file" in B.HERRAMIENTAS_DEL_EXAMEN, (
        "el corredor del banco no puede leer ficheros: entonces sus ceros no "
        "significan que el sistema no vea, significan que no le dejamos")
    assert {"list_dir", "grep", "glob"} <= B.HERRAMIENTAS_DEL_EXAMEN


def test_el_corredor_no_puede_tocar_lo_que_examina():
    """Solo lectura. Un examen que puede modificar el proyecto deja de medir
    dos veces seguidas lo mismo, y además tendría permiso para «arreglar» el
    fichero que no encuentra."""
    prohibidas = {"write_file", "edit_file", "delete_path", "run_command",
                  "python_exec", "undo"}
    assert not (prohibidas & B.HERRAMIENTAS_DEL_EXAMEN)


def test_el_corredor_usa_el_mismo_bucle_que_el_enjambre():
    """Se reutiliza `run_agent`. Un bucle de herramientas propio para el banco
    mediría un camino que ningún usuario recorre nunca — y podría estar verde
    mientras el de verdad está roto."""
    fuente = pathlib.Path(B.__file__).read_text(encoding="utf-8")
    assert "run_agent" in fuente
    assert "agent_loop" in fuente


# ================================== alcanzable desde el sistema

def test_el_banco_del_proyecto_es_un_EvalBench_de_verdad(proyecto):
    """Se acopla al mecanismo que ya existe en vez de montar uno paralelo: la
    auto-mejora de Naoko corre `EvalBench`, y un banco que ella no sepa correr
    no serviría para cerrar el lazo."""
    from vmagi.core.eval.bench import EvalBench, EvalTask

    banco = B.construir(proyecto)
    assert isinstance(banco, EvalBench)
    assert all(isinstance(t, EvalTask) for t in banco.tasks)
    assert {t.category for t in banco.tasks} <= {"ve_el_proyecto",
                                                 "honestidad_del_proyecto"}
