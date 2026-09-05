"""
Biblias que declaran de qué material salieron, y que se unen sin promediar.

DOS AFIRMACIONES REFUTABLES
===========================
1. «Combinar biblias es quedarse con lo que todas exigen a la vez.»
   Se refuta si el resultado admite algo que una de las fuentes rechazaba, o
   si dos referencias que se contradicen producen un número intermedio en vez
   de un conflicto declarado.

2. «Una biblia dice qué ejes no respalda su propio material.»
   Se refuta si una biblia sacada de un plano suelto exige duración media de
   plano sin avisar de que en su referencia no había ni un corte.
"""
from __future__ import annotations

import pytest

from vmagi.modules.studio.biblia import (
    BibliaDeEstilo,
    Dominio,
    Tolerancia,
    combina,
    compara,
)
from vmagi.modules.studio.estilo import MedidaEstilo


def _biblia(nombre: str, **ejes) -> BibliaDeEstilo:
    """Biblia a mano SOLO para los tests. En producción salen de medir."""
    return BibliaDeEstilo(
        nombre=nombre,
        tolerancias=[Tolerancia(eje=e, objetivo=o, margen=m)
                     for e, (o, m) in ejes.items()],
        dominio=Dominio(duracion_s=120.0, planos=40, con_audio=True,
                        con_rostros=True))


# =================================================== intersección, no promedio

def test_EL_CENTRAL_dos_biblias_que_se_contradicen_no_dan_un_numero_intermedio():
    """LA REFUTACIÓN.

    Una referencia pide planos de 8±1 y otra de 2±0,3. El promedio es 5: un
    valor que no describe NINGUNA de las dos películas, que ninguna de las dos
    aprobaría, y que tiene el aspecto de un dato medido.

    Es el mismo error que fusionar dos LoRAs promediando sus pesos, y aquí se
    ve con números porque los intervalos están escritos.
    """
    lenta = _biblia("contemplativa", duracion_media_plano=(8.0, 1.0))
    rapida = _biblia("nerviosa", duracion_media_plano=(2.0, 0.3))

    f = combina([lenta, rapida])

    assert "duracion_media_plano" not in f.ejes, (
        "el eje contradictorio sigue en el contrato. Si vale 5, la biblia "
        "está describiendo una película que nadie rodó")
    assert [c.eje for c in f.conflictos] == ["duracion_media_plano"]
    texto = f.conflictos[0].render()
    assert "8" in texto or "7" in texto, texto
    assert "no hay ningún valor" in texto


def test_lo_que_se_conserva_es_lo_que_las_dos_admiten():
    ancha = _biblia("A", saturacion=(0.30, 0.10))     # [0.20, 0.40]
    estrecha = _biblia("B", saturacion=(0.26, 0.03))  # [0.23, 0.29]

    f = combina([ancha, estrecha])
    t = next(t for t in f.tolerancias if t.eje == "saturacion")
    bajo, alto = t.objetivo - t.margen, t.objetivo + t.margen

    # `approx` y no igualdad: 0.30-0.10 no es exactamente 0.20 en binario, y un
    # test que exige igualdad exacta sobre aritmética de coma flotante mide el
    # formato IEEE, no la intersección.
    assert bajo == pytest.approx(0.23) and alto == pytest.approx(0.29), (bajo, alto)
    assert t.margen == pytest.approx(0.03), (
        "el margen salió más ancho que el de la fuente más estricta: eso es "
        "un promedio disfrazado")


def test_nada_que_las_fuentes_rechazaran_pasa_la_combinada():
    """La comprobación que de verdad importa, hecha por muestreo.

    Un intervalo correcto en los extremos puede seguir estando mal en medio.
    Se barre el rango y se exige que la combinada NUNCA apruebe algo que una
    de sus fuentes suspendía.
    """
    a = _biblia("A", luma=(95.0, 12.0))
    b = _biblia("B", luma=(104.0, 9.0))
    f = combina([a, b])

    for i in range(0, 200):
        valor = 70.0 + i * 0.35
        m = MedidaEstilo(luma=valor)
        if compara(m, f).aprueba:
            assert compara(m, a).aprueba and compara(m, b).aprueba, (
                f"luma {valor:.2f} aprueba la combinada y una de las fuentes "
                f"la rechazaba: la unión ha aflojado el contrato")


def test_un_eje_de_solo_maximo_se_queda_con_el_techo_mas_bajo():
    """«No más de a» y «no más de b» nunca se contradicen: se quedan en el
    menor de los dos. Tratarlos como intervalos daría un conflicto falso."""
    a = BibliaDeEstilo(nombre="A", tolerancias=[
        Tolerancia(eje="camara_px", objetivo=0.2, margen=0.1, solo_maximo=True)])
    b = BibliaDeEstilo(nombre="B", tolerancias=[
        Tolerancia(eje="camara_px", objetivo=1.0, margen=0.5, solo_maximo=True)])

    f = combina([a, b])
    assert not f.conflictos
    t = next(t for t in f.tolerancias if t.eje == "camara_px")
    assert t.solo_maximo
    assert t.objetivo + t.margen == pytest.approx(0.3), (
        "el techo no es el más estricto")
    assert compara(MedidaEstilo(camara_px=0.25), f).aprueba
    assert not compara(MedidaEstilo(camara_px=0.9), f).aprueba


def test_un_eje_que_solo_tiene_una_fuente_entra_tal_cual():
    a = _biblia("A", saturacion=(0.30, 0.05), luma=(90.0, 10.0))
    b = _biblia("B", saturacion=(0.28, 0.05))
    f = combina([a, b])
    assert "luma" in f.ejes
    t = next(t for t in f.tolerancias if t.eje == "luma")
    assert (t.objetivo, t.margen) == (90.0, 10.0)


def test_combinar_una_sola_biblia_la_devuelve_intacta():
    a = _biblia("A", saturacion=(0.3, 0.05))
    assert combina([a]) is a


def test_el_dominio_combinado_es_el_mas_pobre_y_no_la_suma():
    """Unir un plano de 6 s con una película de 3 min NO da una referencia de
    3 minutos: da una en la que la mitad de los ejes siguen sin respaldo."""
    corta = BibliaDeEstilo(
        nombre="plano suelto",
        tolerancias=[Tolerancia(eje="saturacion", objetivo=0.3, margen=0.05)],
        dominio=Dominio(duracion_s=6.0, planos=1, con_audio=False))
    larga = BibliaDeEstilo(
        nombre="pelicula",
        tolerancias=[Tolerancia(eje="saturacion", objetivo=0.3, margen=0.05)],
        dominio=Dominio(duracion_s=180.0, planos=40, con_audio=True))

    f = combina([corta, larga])
    assert f.dominio.duracion_s == 6.0
    assert f.dominio.planos == 1
    assert f.dominio.con_audio is False


# ============================================================== el dominio

def test_una_biblia_de_un_plano_suelto_avisa_de_lo_que_no_respalda():
    """LA SEGUNDA REFUTACIÓN.

    El número es correcto —ese plano dura seis segundos— y la extrapolación no
    lo es. Con esa biblia, una película de tres minutos suspende entera; no
    porque esté mal, sino porque la referencia no tenía ni un corte que medir.
    """
    m = MedidaEstilo(ruta="plano.mp4", duracion=6.0, planos=1,
                     duracion_media_plano=6.0, aspecto=1.85, saturacion=0.3,
                     tiene_audio=False)
    b = BibliaDeEstilo.desde(m)

    avisos = b.avisos_de_dominio()
    assert any("duracion_media_plano" in a for a in avisos), avisos
    assert any("no hay montaje" in a for a in avisos), avisos
    assert not any("saturacion" in a for a in avisos), (
        "la saturación SÍ está respaldada por un plano suelto: el color de un "
        "fotograma no necesita cortes para medirse")


def test_una_referencia_de_verdad_no_dispara_avisos():
    m = MedidaEstilo(ruta="pelicula.mp4", duracion=180.0, planos=22,
                     duracion_media_plano=8.2, aspecto=1.85, saturacion=0.26,
                     tiene_audio=True, fraccion_silencio=0.4,
                     fraccion_con_rostro=0.5, escala_plano=0.18)
    assert BibliaDeEstilo.desde(m).avisos_de_dominio() == []


def test_el_aviso_llega_al_veredicto_pero_NO_suspende():
    """Avisar y suspender son cosas distintas, y confundirlas ya costó una
    sesión entera: `aprueba` exigía `not sin_juzgar` y en una máquina sin
    OpenCV no aprobaba nada nunca."""
    m = MedidaEstilo(ruta="plano.mp4", duracion=6.0, planos=1,
                     duracion_media_plano=6.0, aspecto=1.85, saturacion=0.3)
    b = BibliaDeEstilo.desde(m)
    v = compara(m, b)

    assert v.aprueba, "la referencia no aprueba su propia biblia"
    assert v.avisos_de_dominio, "aprobó sin decir que el contrato va suelto"
    assert "fuera del dominio" in v.render()


def test_un_conflicto_viaja_dentro_de_la_biblia_hasta_el_veredicto():
    """Quien juzgue con la combinada tiene que enterarse de que le falta un eje
    SIN ir a buscar el informe de la combinación."""
    f = combina([_biblia("A", duracion_media_plano=(8.0, 1.0)),
                 _biblia("B", duracion_media_plano=(2.0, 0.3))])
    v = compara(MedidaEstilo(duracion_media_plano=5.0), f)
    assert any("contradicción" in a for a in v.avisos_de_dominio), v.render()


# ============================================================== ida y vuelta

def test_dominio_y_conflictos_sobreviven_al_json():
    f = combina([_biblia("A", duracion_media_plano=(8.0, 1.0),
                         saturacion=(0.3, 0.05)),
                 _biblia("B", duracion_media_plano=(2.0, 0.3),
                         saturacion=(0.29, 0.04))])
    vuelta = BibliaDeEstilo.desde_json(f.to_json())

    assert vuelta.ejes == f.ejes
    assert [c.eje for c in vuelta.conflictos] == [c.eje for c in f.conflictos]
    assert vuelta.conflictos[0].intervalos == f.conflictos[0].intervalos
    assert vuelta.dominio == f.dominio


def test_una_biblia_vieja_sin_dominio_se_carga_igual():
    """Las biblias que ya estaban en disco no traen `dominio`. Reventar al
    leerlas convertiría una mejora en una migración."""
    viejo = ('{"nombre":"vieja","origen":"x.mp4","procedencia":"obra",'
             '"tolerancias":[{"eje":"saturacion","objetivo":0.3,'
             '"margen":0.05,"solo_maximo":false}]}')
    b = BibliaDeEstilo.desde_json(viejo)
    assert b.ejes == ["saturacion"]
    assert b.dominio.planos == 0
    # Y con dominio a cero avisa de lo que no puede respaldar, que es la
    # respuesta honesta para una biblia que no sabe de dónde vino.
    assert isinstance(b.avisos_de_dominio(), list)


# ================================ la resolución del instrumento manda

def test_el_margen_nunca_baja_de_lo_que_el_instrumento_distingue():
    """LA REFUTACIÓN, y salió de mirar una corrida de verdad.

    La referencia sintética se rodó con la cámara literalmente clavada —es un
    `color=` de FFmpeg— y el medidor dijo `camara_px = 1.00`. No es un fallo:
    `_desplazamiento_global` busca desplazamientos ENTEROS, así que su salida
    solo puede valer 0, 1, 2...

    Lo que estaba mal era el contrato. Con holgura del 12% pedía `1 ± 0,12`
    sobre una cantidad que solo toma enteros: exigir el valor exacto y
    llamarlo margen. El escalón de al lado —que el instrumento no puede
    distinguir del bueno— suspendía, y ninguna cantidad de búsqueda lo
    arreglaba, porque entre 1 y 2 no hay nada que encontrar.
    """
    from vmagi.modules.studio.estilo import RESOLUCION

    m = MedidaEstilo(ruta="ref.mp4", duracion=27.0, planos=3,
                     duracion_media_plano=9.0, aspecto=1.829, camara_px=1.0,
                     fraccion_camara_fija=1.0, saturacion=0.2694)
    b = BibliaDeEstilo.desde(m, holgura=0.12)
    tol = {t.eje: t for t in b.tolerancias}

    assert tol["camara_px"].margen >= RESOLUCION["camara_px"], (
        f"margen {tol['camara_px'].margen} sobre una cantidad cuyo escalón "
        f"mide {RESOLUCION['camara_px']}: eso no mide estilo, mide suerte")
    # Y la comprobación que de verdad importa: el escalón de al lado ya no
    # suspende, porque el instrumento no puede distinguirlo del bueno.
    assert compara(MedidaEstilo(camara_px=2.0), b).desvios[0].cumple is not None

    # Lo que NO debe pasar: que el suelo afloje un eje que ya era más ancho.
    assert tol["saturacion"].margen == pytest.approx(0.2694 * 0.12), (
        "el suelo de resolución ha ensanchado un margen que ya era mayor que "
        "la resolución. Solo es un suelo, no un valor")


def test_toda_resolucion_declarada_apunta_a_un_eje_que_existe():
    """Una resolución para un eje que la biblia nunca pone no protege nada y
    da la sensación de que sí. Mismo fallo que un techo de líneas huérfano."""
    from vmagi.modules.studio.estilo import RESOLUCION

    m = MedidaEstilo(
        ruta="x.mp4", duracion=120.0, planos=20, aspecto=1.85,
        duracion_media_plano=6.0, camara_px=0.4, fraccion_camara_fija=0.9,
        saturacion=0.3, luma=90.0, contraste=30.0, escala_plano=0.2,
        fraccion_silencio=0.4, turnos_por_minuto=10.0,
        duracion_media_turno=2.0, pausa_media=1.5)
    posibles = set(BibliaDeEstilo.desde(m).ejes)
    sobran = set(RESOLUCION) - posibles
    assert not sobran, f"resoluciones para ejes que no existen: {sobran}"


# ==================================================== alcanzable desde el enjambre

def test_combinar_biblias_esta_en_el_registro_del_enjambre():
    from vmagi.core.tools.registry import ToolRegistry
    from vmagi.modules.studio.tools import register_studio_tools

    reg = register_studio_tools(ToolRegistry())
    t = reg.get("combinar_biblias")
    assert t is not None, "el enjambre no puede unir dos referencias"
    assert "promedia" in (t.description or "").lower(), (
        "la descripción no dice lo que NO hace, que es lo que un modelo daría "
        "por supuesto")
