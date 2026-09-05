"""
La carpeta de trabajo: elegirla, guardarla, y no mentir sobre ella.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«El enjambre trabaja sobre la carpeta que se le dice, y cuando trabaja sobre
una vacía lo advierte.»

Se refuta si `fija_workspace` acepta una ruta que no existe, si la elección no
sobrevive a un reinicio, o si el sistema trabaja sobre la caja de arena vacía
sin decirlo. Ese último caso no es hipotético: es exactamente lo que pasó el
2026-09-05, con `read_file` fallando 8 de 8 veces contra un árbol sin un solo
fichero `.py`, y la ventana sin decir nada.
"""
from __future__ import annotations

import pytest

from vmagi.core import paths


@pytest.fixture(autouse=True)
def datos_aislados(tmp_path, monkeypatch):
    """Cada test con su propio directorio de datos.

    Sin esto, el primer test que llame a `fija_workspace` escribiría en el
    VeniceMAGI real del usuario. Un test que toca los datos de quien lo corre
    no es un test, es un efecto secundario.
    """
    monkeypatch.setenv("VENICEMAGI_DATA_DIR", str(tmp_path / "datos"))
    monkeypatch.delenv("VENICEMAGI_WORKSPACE", raising=False)
    paths.data_dir.cache_clear()
    paths.workspace_dir.cache_clear()
    yield
    paths.data_dir.cache_clear()
    paths.workspace_dir.cache_clear()


def test_por_defecto_es_la_caja_de_arena_y_se_dice():
    assert paths.workspace_dir() == paths.workspace_por_defecto()
    assert paths.workspace_es_la_caja_de_arena()


def test_elegir_una_carpeta_la_cambia_de_verdad(tmp_path):
    proyecto = tmp_path / "mi-proyecto"
    proyecto.mkdir()

    elegido = paths.fija_workspace(proyecto)

    assert elegido == proyecto.resolve()
    assert paths.workspace_dir() == proyecto.resolve()
    assert not paths.workspace_es_la_caja_de_arena()


def test_la_eleccion_sobrevive_al_reinicio(tmp_path):
    """Una elección que hay que repetir cada arranque no es una elección: es
    una molestia que la gente deja de hacer."""
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    paths.fija_workspace(proyecto)

    paths.workspace_dir.cache_clear()          # como si arrancara de nuevo
    assert paths.workspace_dir() == proyecto.resolve()


def test_volver_a_la_caja_de_arena(tmp_path):
    proyecto = tmp_path / "p"
    proyecto.mkdir()
    paths.fija_workspace(proyecto)
    assert paths.fija_workspace(None) == paths.workspace_por_defecto()
    assert paths.workspace_es_la_caja_de_arena()


def test_EL_CENTRAL_una_ruta_que_no_existe_se_rechaza(tmp_path):
    """LA REFUTACIÓN.

    Apuntar el enjambre a algo que no está es el fallo que todo esto viene a
    cerrar. Aceptarlo en silencio y volver a fallar 8 de 8 veces, pero ahora
    contra otra ruta, sería haber movido el problema en vez de arreglarlo.
    """
    with pytest.raises(ValueError) as e:
        paths.fija_workspace(tmp_path / "no-existe")
    assert "no es una carpeta que exista" in str(e.value)
    # Y NO se queda a medias: la carpeta activa sigue siendo la de antes.
    assert paths.workspace_es_la_caja_de_arena()


def test_un_fichero_no_vale_como_carpeta(tmp_path):
    f = tmp_path / "algo.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        paths.fija_workspace(f)


def test_el_entorno_manda_sobre_la_eleccion(tmp_path, monkeypatch):
    """`VENICEMAGI_WORKSPACE` gana, porque lo usan los scripts y el CI y
    tienen que poder fijar la carpeta sin tocar los datos del usuario."""
    elegido, forzado = tmp_path / "elegido", tmp_path / "forzado"
    elegido.mkdir()
    forzado.mkdir()
    paths.fija_workspace(elegido)

    monkeypatch.setenv("VENICEMAGI_WORKSPACE", str(forzado))
    paths.workspace_dir.cache_clear()
    assert paths.workspace_dir() == forzado.resolve()


def test_una_eleccion_apuntando_a_algo_borrado_no_revienta(tmp_path):
    """Se elige una carpeta y luego se borra. Arrancar tiene que seguir
    funcionando: caer a la caja de arena es peor que nada, pero mucho mejor
    que no arrancar."""
    p = tmp_path / "efimera"
    p.mkdir()
    paths.fija_workspace(p)
    p.rmdir()

    paths.workspace_dir.cache_clear()
    assert paths.workspace_dir() == paths.workspace_por_defecto()


# ======================================= lo que la ventana llega a preguntar

async def test_el_retrato_avisa_cuando_la_carpeta_esta_vacia(tmp_path):
    """EL AVISO QUE NO EXISTÍA.

    La ventana mostraba un panel de configuración con proveedores, latencias y
    prioridades, y ni una palabra sobre la única ruta que decidía si el sistema
    servía para algo.
    """
    from vmagi.core.rpc.ws_server import WSServer

    s = object.__new__(WSServer)                # sin abrir sockets ni base
    retrato = s._retrato_workspace()

    assert retrato["es_caja_de_arena"]
    assert retrato["ficheros_py"] == 0
    assert "no ve tu proyecto" in retrato["aviso"]
    assert retrato["ruta"] and retrato["por_defecto"]


async def test_el_retrato_calla_cuando_hay_material(tmp_path):
    """Y no avisa cuando no hay de qué: un aviso que sale siempre es ruido, y
    el ruido enseña a saltarse los avisos."""
    from vmagi.core.rpc.ws_server import WSServer

    proyecto = tmp_path / "con-codigo"
    (proyecto / "sub").mkdir(parents=True)
    (proyecto / "sub" / "modulo.py").write_text("x = 1\n", encoding="utf-8")
    paths.fija_workspace(proyecto)

    retrato = object.__new__(WSServer)._retrato_workspace()
    assert retrato["ficheros_py"] == 1
    assert retrato["aviso"] == ""
    assert not retrato["es_caja_de_arena"]
