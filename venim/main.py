import argparse
import asyncio
import logging
import os
import signal
import sys
import threading

# §I.3 — ANTES QUE NADA. El cortafuegos de navegador se instala en la primera
# línea ejecutable del proceso, antes de importar webview, g4f o cualquier
# módulo que pueda arrastrarlos. La capa de subprocess.Popen no depende de g4f,
# así que instalarla aquí garantiza que ninguna ruta —conocida o futura— pueda
# lanzar una ventana de navegador durante el arranque ni durante la inferencia.
from venim.core.no_browser import install as _install_browser_guard

_install_browser_guard()

# Y la consola en UTF-8, por el mismo motivo de orden: escribir un acento en la
# consola cp1252 de Windows lanza UnicodeEncodeError, y esa excepción subía por
# el bucle de streaming y lo abortaba a mitad de respuesta —"streaming falló
# ('charmap' codec can't encode characters...)"—, forzando pedir la respuesta
# entera otra vez. Este proyecto habla español: no era un caso raro.
from venim.core.consola import configurar as _configurar_consola

_configurar_consola()

import webview

from venim.gui_server import GUIServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from venim.core.kernel import Kernel
from venim.modules.memory.composer import Composer
from venim.modules.resilience.selector import CloudSelector
from venim.modules.route.gateway import Gateway

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Venim")

class Venim:
    """
    Orquestador principal del Venim (Área 0 y Centro de Control).
    Amarra el bus de eventos, la pasarela de UI, la resiliencia cloud y los módulos operativos.
    """
    def __init__(self, host="127.0.0.1", port=20128, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        self.kernel = Kernel(host=self.host, port=self.port)
        self.bus = self.kernel.bus
        # Inicialización de Resiliencia Cloud-Only (Área 6)
        self.cloud_selector = CloudSelector(["cloud-openai-gpt4", "cloud-anthropic-claude", "cloud-google-gemini", "cloud-mistral", "cloud-cohere"])
        self._shutdown_event = asyncio.Event()

    async def _setup_signal_handlers(self):
        """Maneja el apagado limpio (Graceful Shutdown)"""
        if sys.platform != 'win32':
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._shutdown_event.set)
        else:
            # En Windows no podemos usar add_signal_handler directamente de la misma forma,
            # pero asyncio.run se encarga de KeyboardInterrupt.
            pass

    async def start(self):
        logger.info("Iniciando Venim...")

        # 1. Setup de señales
        await self._setup_signal_handlers()

        # Los suscriptores registrados en constructores síncronos (colector de
        # métricas, logger del bus) tienen su worker pendiente hasta aquí.
        self.bus.start_pending_workers()

        # 2. Levantar el Kernel (Área 0)
        await self.kernel.start()

        # 3. Levantar otros módulos base
        self.gateway = Gateway()
        from venim.modules.memory.record import MemoryRecord
        self.record = MemoryRecord("main_session")
        self.composer = Composer(self.record)

        # ---------------------------------------------------------------
        # MAGI 9.0 — Regla "conecta o borra".
        #
        # v5.0.28 instanciaba aquí doce subsistemas (MagiHive, SemanticRAG,
        # HierarchicalMemory, SymbolicVerifier, PromptCompiler, EvolverAgent,
        # CognitiveCore, QuantumOracle, HyperdimensionalMemory, SkinMembrane,
        # MarketDigitalTwin...). Conteo real de sitios de llamada:
        #
        #     self.semantic_rag.*        -> 0     self.cognitive_core.*  -> 0
        #     self.hierarchical_memory.* -> 0     self.quantum_oracle.*  -> 0
        #     self.prompt_compiler.*     -> 0     self.hdc_memory.*      -> 0
        #     self.evolver.*             -> 0     self.quant_simulator.* -> 0
        #     self.hive.*                -> 1  (solo .shutdown())
        #     self.cellular_router.*     -> 1  (solo .shutdown())
        #
        # Los dos únicos que se usaban, se usaban para APAGARLOS. Existían para
        # que se imprimieran las líneas "MAGI 5.0 Bio-Quantum", "MAGI 7.0
        # Predictive Twin", etc.
        #
        # Se retiran. Lo que queda está conectado y tiene tests.
        # ---------------------------------------------------------------
        from venim.core.context import refresh_context
        from venim.core.providers.cloud import get_registry

        self.provider_registry = await get_registry()
        self.exec_context = refresh_context(
            provider_health=self.provider_registry.telemetry())

        assignment = self.provider_registry.select_for_swarm()
        logger.info("Enjambre: %s", " · ".join(
            f"{r}={assignment.families.get(r, 'n/d')}" for r in assignment.by_role))
        if assignment.diversity != "full":
            logger.warning("Diversidad %s: %s", assignment.diversity, assignment.note)

        fams = self.provider_registry.families_available()
        logger.info("Inferencia: %d familias de nube gratuita sanas -> %s",
                    len(fams), ", ".join(fams) or "NINGUNA")
        logger.info("Datos en: %s", __import__("venim.core.paths", fromlist=["x"]).data_dir())

        logger.info("SISTEMA MAGI OPERATIVO Y ESPERANDO CONEXIONES.")

        # 4. Mantener vivo hasta apagado
        try:
            if sys.platform == 'win32':
                # Bucle de espera compatible con Windows
                while not self._shutdown_event.is_set():
                    await asyncio.sleep(1)
            else:
                await self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado detectada.")

        await self.stop()

    async def stop(self):
        logger.info("Deteniendo el sistema MAGI...")
        if hasattr(self, 'bus') and self.bus:
            await self.bus.shutdown()
        if hasattr(self, 'kernel') and self.kernel:
            await self.kernel.shutdown()
            logger.info("Sistema apagado correctamente.")

def _start_magi_background(venim, loop):
    """Ejecuta el loop asyncio en un hilo secundario"""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(venim.start())
    except Exception as e:
        logger.error(f"Error fatal en el loop secundario: {e}")

def main():
    parser = argparse.ArgumentParser(description="Venim Bootstrapper")
    parser.add_argument("--host", default="127.0.0.1", help="Host para el GUI Server (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=20128, help="Puerto para el GUI Server (default: 20128)")
    parser.add_argument("--gui-port", type=int, default=1420, help="Puerto HTTP local para el Frontend (default: 1420)")
    parser.add_argument("--debug", action="store_true", help="Habilitar logs de depuración")
    parser.add_argument("--consola", action="store_true",
                        help="Arranca el REPL de consola en vez de la ventana")

    args = parser.parse_args()

    # `--consola`, y ANTES de levantar nada de la GUI.
    #
    # El manifiesto lo promete: «`Venim.exe` abre la ventana; `--consola`
    # mantiene el REPL». Y no es solo una preferencia de interfaz: si pywebview
    # no levanta, si el frontend no compiló o si la ventana sale en blanco, la
    # consola sigue dando `/salud`, `/historial` y `/galeria`. Un diagnóstico
    # que necesita la interfaz averiada no sirve para diagnosticarla.
    #
    # Va aquí arriba a propósito: arrancar el servidor GUI y el hilo del kernel
    # para luego no usarlos dejaría dos puertos ocupados y un hilo vivo detrás
    # de un REPL que no los toca.
    if args.consola:
        from venim.repl import main as repl_main
        return asyncio.run(repl_main())

    venim = Venim(host=args.host, port=args.port, debug=args.debug)

    # 1. Iniciar Servidor GUI Estático
    #
    # `start()` DEVUELVE EL PUERTO, y hay que usar ese y no el pedido.
    #
    # El 2026-09-06 la ventana de Venim mostró la interfaz de MAGI System IDE
    # porque `MAGI-IDE-v5.exe` ya tenía el 1420: el servidor de Venim falló al
    # tomarlo, se tragó el error en un log, y esta función siguió adelante
    # abriendo la ventana sobre lo que respondiera ahí. Con el puerto
    # conseguido —no el deseado— esa confusión deja de ser posible.
    gui = GUIServer(port=args.gui_port)
    puerto_gui = gui.start()

    # 2. Iniciar el Kernel MAGI en un Hilo Secundario
    magi_loop = asyncio.new_event_loop()
    magi_thread = threading.Thread(target=_start_magi_background, args=(venim, magi_loop), daemon=True)
    magi_thread.start()

    import os
    import sys

    def get_resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    # La última comprobación antes de mirar: que quien contesta ahí somos
    # nosotros. `start()` ya lo garantiza, pero esto es lo que convierte la
    # garantía en algo que se puede ver fallar en vez de suponer.
    from venim.gui_server import es_de_venim
    if not es_de_venim(puerto_gui):
        raise RuntimeError(
            f"en el puerto {puerto_gui} contesta algo que no es Venim. No se "
            f"abre la ventana: mostrarla sobre la interfaz de otro programa "
            f"es peor que no abrirla, porque parece que funciona.")

    logger.info("Abriendo la ventana de Venim en el puerto %d", puerto_gui)
    webview.create_window(
        title="Venim",
        url=f"http://127.0.0.1:{puerto_gui}",
        width=1280,
        height=800,
        frameless=False,
        easy_drag=False,
        # El lienzo que pywebview pinta ANTES de que cargue nada.
        #
        # Por defecto es blanco, así que abrir la aplicación era un fogonazo
        # blanco a pantalla completa y después el tema oscuro. Molesta de
        # noche, que es cuando más se usa esto, y hace parecer que la ventana
        # se ha colgado y recargado. Es `--paper` de `theme/magi.css`, el
        # mismo fondo que va a aparecer: así no hay transición visible.
        background_color="#1F1E1C",
    )

    # Esto bloqueará hasta que el usuario cierre la ventana
    webview.start(debug=args.debug)

    # 4. Apagado Limpio al cerrar la ventana
    logger.info("Ventana cerrada. Apagando sistemas...")
    gui.stop()

    # Señalizar al loop que se detenga
    if sys.platform != 'win32':
        magi_loop.call_soon_threadsafe(venim._shutdown_event.set)
    else:
        # Hack simple para despertar y apagar en Windows
        magi_loop.call_soon_threadsafe(venim._shutdown_event.set)

    magi_thread.join(timeout=3)
    logger.info("MAGI cerrado por completo. Adiós.")
    sys.exit(0)

if __name__ == "__main__":
    main()
