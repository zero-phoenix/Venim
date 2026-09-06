"""
Venim nunca abre su ventana sobre el servidor de otro programa.

LA AFIRMACIÓN QUE ESTOS TESTS PUEDEN REFUTAR
============================================
«La ventana de Venim muestra la interfaz de Venim.»

Parece que no hace falta comprobarla. Fue refutada el 2026-09-06 con una
captura de pantalla: marco titulado «Venim», contenido diciendo «MAGI SYSTEM
IDE — Supercomputadora Táctica Autónoma». Dentro de la ventana de Venim estaba
corriendo, entera, la interfaz de otro programa.

LA CADENA, MEDIDA
=================
  1. `MAGI-IDE-v5.exe` escuchaba en el puerto 1420
     (`C:\\Users\\D\\Documents\\GitHub\\MAGI-System-IDE\\dist\\unpacked\\`).
  2. Venim arrancó y su servidor pidió ese mismo puerto.
  3. Falló con «address already in use».
  4. **El error se escribió en un log y `start()` volvió como si nada.**
  5. `main.py` abrió la ventana en `http://127.0.0.1:1420`.
  6. Contestó MAGI.

Los dos programas comparten antepasado, así que comparten los números que
alguien eligió una vez. El puerto fijo no era una decisión: era una herencia.

Y HUBO UN SEGUNDO FALLO, EN EL INSTRUMENTO
==========================================
Mi propio script de compilación daba la compilación por buena comprobando que
«algo responde en el 1420». Respondía MAGI. El verificador confirmaba que
Venim arrancaba usando como prueba la respuesta del programa que impedía que
Venim arrancase. Es el corolario que este repositorio se repite: **el
instrumento de medida es el mejor escondite**.
"""
from __future__ import annotations

import json
import socket
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from venim.gui_server import RUTA_IDENTIDAD, GUIServer, es_de_venim


class _Impostor(BaseHTTPRequestHandler):
    """Otro programa cualquiera escuchando. Contesta 200 a todo, como MAGI."""

    def do_GET(self):                              # noqa: N802
        cuerpo = b"<html><title>MAGI System IDE</title></html>"
        self.send_response(200)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


@pytest.fixture
def impostor():
    """Ocupa un puerto libre imitando al programa que causó el fallo."""
    srv = HTTPServer(("127.0.0.1", 0), _Impostor)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield srv.server_address[1]
    srv.shutdown()
    srv.server_close()


# ====================================== la refutación, reproducida

def test_EL_CENTRAL_no_se_confunde_un_servidor_ajeno_con_el_nuestro(impostor):
    """LA REFUTACIÓN.

    Un servidor que contesta 200 a todo está «escuchando», y con eso bastaba
    para que la ventana se abriera encima. La pregunta correcta no es «¿hay
    algo?» sino «¿eres tú?».
    """
    assert not es_de_venim(impostor), (
        "un servidor ajeno que contesta 200 se toma por el de Venim. Con esto "
        "la ventana de Venim mostró la interfaz de MAGI System IDE entera.")


def test_si_el_puerto_esta_ocupado_se_usa_otro(impostor, tmp_path, monkeypatch):
    """Rendirse con el puerto pedido era la mitad del fallo.

    Un programa que solo sabe vivir en un número concreto deja de funcionar en
    cuanto alguien más lo quiere — y en esta máquina había dos candidatos.
    """
    dist = tmp_path / "venim-gui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<title>Venim</title>", encoding="utf-8")

    gui = GUIServer(port=impostor)
    monkeypatch.setattr(gui, "_dist", lambda: str(dist))
    try:
        puerto = gui.start()
        assert puerto != impostor, (
            "el servidor se quedó con el puerto ocupado por otro programa")
        assert es_de_venim(puerto), "lo que levantó no se identifica como Venim"
    finally:
        gui.stop()


def test_el_servidor_dice_quien_es(tmp_path, monkeypatch):
    """La identidad es un endpoint y no una cabecera para que se pueda
    comprobar desde un test, desde el navegador y desde la línea de comandos
    sin herramientas."""
    dist = tmp_path / "venim-gui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<title>Venim</title>", encoding="utf-8")

    gui = GUIServer(port=0 or 8931)
    monkeypatch.setattr(gui, "_dist", lambda: str(dist))
    try:
        puerto = gui.start()
        with urllib.request.urlopen(
                f"http://127.0.0.1:{puerto}{RUTA_IDENTIDAD}", timeout=3) as r:
            datos = json.loads(r.read().decode("utf-8"))
        assert datos["programa"] == "Venim"
        assert datos["puerto"] == puerto
    finally:
        gui.stop()


def test_sin_interfaz_no_se_arranca_en_silencio(tmp_path, monkeypatch):
    """Si no está el `dist`, antes se escribía un log y se seguía adelante.

    Seguir adelante es lo que dejaba la ventana apuntando a cualquier cosa.
    """
    gui = GUIServer(port=8941)
    monkeypatch.setattr(gui, "_dist", lambda: str(tmp_path / "no-existe"))
    with pytest.raises(RuntimeError, match="interfaz de Venim"):
        gui.start()


def test_si_no_hay_ningun_puerto_libre_se_dice(monkeypatch, tmp_path):
    """El caso extremo: todo ocupado. La respuesta correcta es negarse, no
    abrir la ventana sobre el primero que conteste."""
    dist = tmp_path / "venim-gui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<title>Venim</title>", encoding="utf-8")

    import venim.gui_server as gs
    monkeypatch.setattr(gs, "_esta_libre", lambda p: False)
    gui = GUIServer(port=8951)
    monkeypatch.setattr(gui, "_dist", lambda: str(dist))
    with pytest.raises(RuntimeError, match="ningún puerto libre"):
        gui.start()


# ====================================== y que main.py lo use

def test_la_ventana_usa_el_puerto_CONSEGUIDO_y_no_el_pedido():
    """El eslabón que cerraba la cadena.

    Aunque el servidor busque otro puerto, si `main.py` construye la URL con
    el que pidió, la ventana sigue apuntando a donde escucha el otro programa.
    """
    # Se lee el FICHERO, no se importa el módulo: `main.py` importa
    # `webview`, que solo existe en Windows, y este test tiene que correr
    # también en el Ubuntu del CI — que es justo donde se decide si hay
    # release.
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    fuente = (raiz / "venim" / "main.py").read_text(encoding="utf-8")
    assert "puerto_gui = gui.start()" in fuente, (
        "main.py ignora el puerto que devuelve el servidor")
    assert "http://127.0.0.1:{puerto_gui}" in fuente, (
        "la ventana se abre con el puerto PEDIDO. Si el servidor tuvo que "
        "usar otro, esta URL apunta a lo que ocupaba el primero.")
    assert "es_de_venim(puerto_gui)" in fuente, (
        "nadie comprueba que quien contesta sea Venim antes de mirar")


def test_el_puerto_libre_se_comprueba_de_verdad():
    """`_esta_libre` con un puerto que acabamos de ocupar tiene que decir que
    no. Un detector de puertos libres que siempre dice «sí» reintroduce el
    fallo entero sin tocar nada más."""
    from venim.gui_server import _esta_libre
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        ocupado = s.getsockname()[1]
        assert not _esta_libre(ocupado)
