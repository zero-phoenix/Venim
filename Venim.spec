# -*- mode: python ; coding: utf-8 -*-
#
# PLAYWRIGHT ENTERO, Y NO ES OPCIONAL.
#
# La puerta de Venim abre el Edge REAL de la máquina con Playwright, y
# Playwright necesita SU PAQUETE COMPLETO —incluido el driver de Node que
# lanza el navegador—. Dentro del PYZ su `__file__` no apunta a ficheros
# reales y el driver no se encuentra: el .exe compila, arranca, y muere al
# primer `/magi` con «Executable doesn't exist». Es el fallo que la sexta
# regla del proyecto describe: el binario publicado no es el mismo programa
# que el de desarrollo.
from PyInstaller.utils.hooks import collect_all

_pw_datas, _pw_bins, _pw_hidden = collect_all('playwright')


a = Analysis(
    ['venim\\main.py'],
    pathex=[],
    binaries=_pw_bins,
    # LO QUE VIAJA DENTRO SE ENUMERA. NO SE METE UNA CARPETA A BULTO.
    #
    # Esta línea decía `('assets', 'assets')`, y esa comodidad tuvo un precio
    # concreto: dentro de `assets/` había una maqueta HTML COMPLETA de la
    # interfaz del proyecto del que salió este —«MAGI SYSTEM IDE»,
    # `modelo-interfaz/magi-interfaz-v6.html`— y se empaquetaba en cada
    # release. Nadie la importaba; no hacía falta. Un fichero que viaja dentro
    # del binario solo espera a que algo lo sirva.
    #
    # Enumerar es más largo de escribir y es la diferencia entre «creo que no
    # hay nada de más» y saberlo. Lo que se añada a `assets/` a partir de
    # ahora no entra en el .exe salvo que alguien lo ponga aquí, a mano, y
    # entonces la decisión tiene autor.
    #
    # `venim/data` lleva el catálogo de proveedores: sin él, el .exe arrancaría
    # con el respaldo de las constantes —funciona, pero se pierde justo lo que
    # se buscaba: poder arreglar un proveedor caído sin recompilar 143 MB.
    datas=_pw_datas + [
        ('assets/icon.ico', 'assets'),
        ('assets/icon.png', 'assets'),
        ('assets/sonido-icono', 'assets/sonido-icono'),
        ('assets/python-embed/extracted', 'assets/python-embed/extracted'),
        ('venim-gui/dist', 'venim-gui/dist'),
        ('venim/data', 'venim/data'),
    ],
    hiddenimports=_pw_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Pila de ML que MAGI NO usa y que entraba de polizón en el binario.
    #
    # La cadena, trazada instrumentando __import__:
    #   g4f/tools/files.py -> g4f.integration.markitdown -> markitdown
    #   -> magika -> onnxruntime  (y de ahí torch, transformers, tensorflow)
    #
    # Es la integración opcional de g4f para convertir documentos. Ninguna
    # línea de `venim/` importa torch, transformers, tensorflow, onnxruntime ni
    # PyQt5; lo único que se usa de esta zona es sklearn, en
    # venim/modules/skills/loader.py, y ese se queda.
    #
    # Excluirlos arregla ADEMÁS un cuelgue reproducible de la compilación.
    # Volcado de pila del proceso bloqueado (py-spy):
    #     _load_dll_libraries (torch/__init__.py:265)
    #     import_library (PyInstaller/building/build_main.py:227)
    #     run_next_command (PyInstaller/isolated/_child.py:63)
    # PyInstaller importa cada paquete recolectado en un proceso aislado para
    # resolver sus DLLs; al llegar a torch se quedaba parado indefinidamente en
    # el paso "Looking for dynamic libraries". Tres compilaciones seguidas se
    # colgaron ahí.
    #
    # Y encaja con §I.3: torch y onnxruntime son motores de inferencia LOCAL,
    # justo lo que el proyecto declara no usar. Verificado antes de excluirlos:
    # con estos módulos bloqueados en sys.meta_path, venim.main importa, los 11
    # proveedores se registran, el enjambre reparte gpt/gemini/command con
    # diversidad completa y la inferencia responde.
    #
    # SEGUNDO GRUPO: lo que se cuela desde el Python de quien compila.
    #
    # Auditado midiendo el bundle de una compilación local (Analysis-00.toc
    # contra el tamaño real de cada fichero). Los que más pesaban NO eran
    # dependencias del proyecto: eran extras opcionales de g4f que estaban
    # instalados en el Python global de la máquina de desarrollo.
    #
    #     29,2 MB  speech_recognition  (modelo de lenguaje de pocketsphinx)
    #     10,0 MB  yt_dlp
    #      8,1 MB  pandas
    #      7,2 MB  pypdfium2
    #      7,2 MB  sqlalchemy
    #      6,2 MB  openai
    #      4,2 MB  matplotlib
    #
    # Ninguno aparece en requirements.lock y ninguna línea de `venim/` los
    # importa: 55 MB de binario que dependían de qué tuviera instalado quien
    # le diera a compilar. El .exe del release ya salía sin ellos —se compila
    # desde el lock, en un runner limpio—, así que excluirlos NO cambia lo que
    # se publica: hace que una compilación local produzca el MISMO binario que
    # el release. Un binario que depende del entorno de quien lo genera no se
    # puede depurar contra el que descarga la gente.
    #
    # La regla, escrita para no tener que redescubrirla: si no está en
    # requirements.lock y venim/ no lo importa, no viaja dentro.
    # `tests/test_bundle_coherente.py` comprueba que esta lista y el código no
    # se contradigan.
    excludes=[
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'transformers', 'onnxruntime',
        'markitdown', 'magika',
        'PyQt5', 'PySide2', 'PySide6',
        'speech_recognition', 'pocketsphinx',
        'yt_dlp', 'pandas', 'pypdfium2', 'pypdfium2_raw',
        'sqlalchemy', 'openai', 'matplotlib',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Venim',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX NO, y el motivo NO es el que escribí primero aquí.
    #
    # El 2026-09-06 un .exe recién compilado moría en el arranque, antes de
    # ejecutar una línea del proyecto:
    #
    #     File "pyimod01_archive.py", line 134, in extract
    #     zlib.error: Error -3 while decompressing data: incorrect header check
    #
    # Escribí en este mismo sitio que la culpa era de UPX recomprimiendo el
    # archivo del arranque. Sonaba bien y era mentira: `Get-Command upx` dice
    # que UPX NO ESTÁ INSTALADO en esta máquina, así que `upx=True` nunca llegó
    # a aplicarse. La causa real era otra —dos instancias del programa abiertas
    # impedían a PyInstaller sobrescribir `dist/Venim.exe`, y lo que se
    # estaba probando era un binario viejo y a medio escribir—. Dejo escrito mi
    # error porque es el que más veces se repite: una explicación plausible que
    # nadie comprobó.
    #
    # El `False` se queda, con el argumento que sí se sostiene: `upx=True` no
    # significa «comprime», significa «comprime SI encuentras UPX en el PATH».
    # El runner de GitHub no lo tiene y esta máquina tampoco, pero basta con que
    # alguien lo instale para que su binario deje de ser el que se publica, sin
    # tocar una línea. Es la sexta regla del proyecto: el binario publicado
    # tiene que ser el mismo programa que el de desarrollo, y una bandera cuyo
    # efecto depende del PATH lo impide en silencio.
    #
    # Además UPX dispara antivirus con regularidad y aquí no compraría nada: el
    # peso lo domina el Python embebido, que ya viaja comprimido.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
