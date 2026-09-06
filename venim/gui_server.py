"""
El servidor que sirve la ventana de Venim. Y solo la de Venim.

EL FALLO QUE ESTE MÓDULO EXISTE PARA NO REPETIR
===============================================
El 2026-09-06 David abrió Venim y la ventana mostró **la interfaz de MAGI
System IDE**: marco titulado «Venim», contenido diciendo «MAGI SYSTEM IDE —
Supercomputadora Táctica Autónoma». No era un texto olvidado en el código: era
otro programa.

La cadena de sucesos, medida:

  1. `MAGI-IDE-v5.exe` estaba corriendo y escuchando en el puerto 1420.
  2. Venim arrancó y su servidor intentó tomar ese mismo puerto.
  3. Falló, con `OSError: address already in use`.
  4. **El error se escribió en un log y la función devolvió como si nada.**
  5. `main.py`, que no tenía forma de enterarse, abrió su ventana en
     `http://127.0.0.1:1420`.
  6. Ahí contestó MAGI. Venim pintó la interfaz de otro programa dentro de su
     propia ventana, sin un solo error visible.

Dos proyectos que comparten antepasado comparten también los números que
alguien eligió una vez. El puerto fijo no era una decisión: era una herencia.

LAS TRES COSAS QUE LO ARREGLAN DE RAÍZ
======================================
Ninguna basta sola, y por eso están las tres:

  · **Buscar puerto.** Si el preferido está ocupado, se prueban los
    siguientes. Un programa que solo sabe vivir en un número concreto deja de
    funcionar en cuanto alguien más lo quiere.
  · **Identificarse.** El servidor responde en `/venim.json` con su marca, y
    quien vaya a apuntar una ventana puede preguntar «¿eres tú?» antes de
    mirar. Sin esto, «hay algo escuchando» se confunde con «está el mío».
  · **Fallar ruidosamente.** Si no se puede levantar el servidor propio, se
    lanza una excepción. Abrir una ventana sobre un servidor ajeno es peor
    que no abrirla: el usuario cree que está usando Venim.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

logger = logging.getLogger(__name__)

#: La ruta por la que el servidor de Venim dice que es el de Venim.
#:
#: Un endpoint y no una cabecera porque así se puede comprobar desde el
#: navegador, desde un test y desde la línea de comandos sin herramientas.
RUTA_IDENTIDAD = "/venim.json"

#: Cuántos puertos se prueban a partir del preferido antes de rendirse.
#:
#: Doce y no tres: la máquina donde nació este fallo tenía dos programas de la
#: misma familia y un servidor de desarrollo, y los tres viven en este rango.
PUERTOS_A_PROBAR = 12


def _identidad(puerto: int) -> dict:
    return {"programa": "Venim", "papel": "interfaz", "puerto": puerto}


def es_de_venim(puerto: int, timeout: float = 1.5) -> bool:
    """¿El que escucha en ese puerto es el servidor de Venim?

    Se pregunta ANTES de apuntar una ventana a un puerto. La respuesta «hay
    algo escuchando» no vale: eso era exactamente lo que pasaba cuando la
    ventana de Venim mostraba la interfaz de MAGI.
    """
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{puerto}{RUTA_IDENTIDAD}", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")).get("programa") == "Venim"
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return False


def _esta_libre(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", puerto))
            return True
        except OSError:
            return False


class GUIServer:
    """Sirve `venim-gui/dist`, y se identifica como Venim al hacerlo."""

    def __init__(self, port: int = 1420):
        self.port_preferido = port
        #: El puerto REAL en el que se acabó escuchando. Puede no ser el
        #: preferido, y quien abra la ventana tiene que usar este.
        self.port = port
        self.httpd: TCPServer | None = None
        self.thread: threading.Thread | None = None

    def _dist(self) -> str:
        base = (sys._MEIPASS if hasattr(sys, "_MEIPASS")
                else os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        return os.path.join(base, "venim-gui", "dist")

    def start(self) -> int:
        """Levanta el servidor y devuelve el puerto real. Lanza si no puede.

        Devolver el puerto no es un detalle: `main.py` construye la URL de la
        ventana con él, y con el valor pedido en vez del conseguido volvería a
        apuntar a donde escucha otro.
        """
        dist_path = self._dist()
        if not os.path.exists(dist_path):
            raise RuntimeError(
                f"no está la interfaz de Venim en {dist_path}. Sin ella no hay "
                f"nada que servir: compila con `npm run build` en venim-gui/.")

        identidad = _identidad

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=dist_path, **kwargs)

            def do_GET(self):                      # noqa: N802 (API de la clase base)
                if self.path.split("?")[0] == RUTA_IDENTIDAD:
                    cuerpo = json.dumps(
                        identidad(self.server.server_address[1])).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(cuerpo)))
                    self.end_headers()
                    self.wfile.write(cuerpo)
                    return
                super().do_GET()

            def log_message(self, format, *args):
                pass

        for intento in range(PUERTOS_A_PROBAR):
            puerto = self.port_preferido + intento
            if not _esta_libre(puerto):
                quien = "otro Venim" if es_de_venim(puerto) else "otro programa"
                logger.info("[GUIServer] el puerto %d lo tiene %s; pruebo el "
                            "siguiente", puerto, quien)
                continue
            try:
                self.httpd = TCPServer(("127.0.0.1", puerto), Handler)
            except OSError:                        # pragma: no cover
                # Alguien tomó el puerto entre la comprobación y el bind. Se
                # sigue probando: no es un error, es una carrera perdida.
                continue
            self.port = puerto
            self.thread = threading.Thread(target=self.httpd.serve_forever,
                                           daemon=True)
            self.thread.start()
            if puerto != self.port_preferido:
                logger.warning(
                    "[GUIServer] el puerto %d estaba ocupado por otro "
                    "programa; Venim sirve su interfaz en el %d",
                    self.port_preferido, puerto)
            logger.info("[GUIServer] interfaz de Venim en http://127.0.0.1:%d",
                        puerto)
            return puerto

        raise RuntimeError(
            f"no hay ningún puerto libre entre {self.port_preferido} y "
            f"{self.port_preferido + PUERTOS_A_PROBAR - 1}. Venim NO abre la "
            f"ventana: apuntarla a un puerto ajeno mostraría la interfaz de "
            f"otro programa dentro del marco de Venim, que es exactamente lo "
            f"que pasó el 2026-09-06 con MAGI-IDE-v5.")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
