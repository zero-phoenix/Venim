# Venim — el plan completo: lo hecho, lo que falta y por qué

**Estado a 6 de septiembre de 2026.** Repositorio `zero-phoenix/Venim`,
publicado en `v3.0.1`.

Este documento existe para que cualquiera —persona o agente— pueda continuar el
trabajo sin repetir los errores que ya se pagaron. Cada cosa hecha viene con la
**evidencia** que la sostiene; cada cosa pendiente, con el **criterio que la
refutaría**. Lo que no está comprobado se dice, no se supone.

---

## 1. Qué es Venim, en una frase que decide

**Venim crea imagen, vídeo y cine de alta calidad, y mide la calidad en vez de
suponerla.** Todo lo demás que lleva dentro —desensamblar binarios, pilotar
emuladores, consultar datos macroeconómicos— **existe para servir a esa
imagen**: son las formas de conseguir material real cuando lo que se pide tiene
que parecer real.

Esa frase no es marketing: es el criterio para decidir qué entra y qué no. Una
capacidad nueva se justifica diciendo qué imagen ayuda a hacer.

### Lo que Venim NO es

No es MAGI System IDE. Son dos proyectos distintos que comparten antepasado, y
esa herencia ya causó un fallo grave (§4.1). Venim no usa la interfaz de MAGI,
no comparte sus puertos y no empaqueta sus ficheros. Hay tests que lo
comprueban en cada push.

---

## 2. El estado, medido hoy

| | |
|---|---|
| Python | 49.336 líneas · 257 ficheros |
| Interfaz | 7.000 líneas · 42 ficheros |
| Tests | 27.617 líneas · 130 ficheros · ~1.950 casos |
| Herramientas del enjambre | 80 |
| Handlers RPC | 23 |
| Sucesos del bus declarados | 50 |
| Automodelo | 39 afirmaciones: 24 sostenidas, **10 refutadas**, 5 sin comprobar |

**Las 10 refutadas y las 5 sin comprobar son la parte honesta.** Están en
`docs/AUTOMODELO.json` con la prueba que las tumbó. Un sistema que solo declara
lo que funciona no está declarando nada.

---

## 3. Las reglas del proyecto

No son estilo: cada una nació de un fallo concreto y evita que vuelva.

1. **Todo cambio se conecta o se borra.**
2. **Un test sobre una pieza aislada no prueba que el sistema la use.**
3. **Cada capacidad tiene que poder invocarse desde la interfaz.**
4. **Arrancar encuentra fallos que leer no encuentra.**
5. **«No he podido comprobarlo» no es «está bien».**
6. **El binario publicado no es el mismo programa que el de desarrollo.**
7. **Arreglar algo no es lo mismo que arreglarlo donde importa.**
8. **Lo que abre un navegador no se sondea.**
9. **Los trinquetes bajan, no suben.**
10. **Se escribe con Python, `newline='\n'` y sin BOM.**

Y un corolario que se ganó dos veces en esta sesión:

> **El instrumento de medida es el mejor escondite.** Dos veces un verificador
> mío dio por bueno algo que no lo estaba, y las dos veces el fallo estaba en
> el verificador, no en lo verificado.

### Los trinquetes: números que solo bajan

| Trinquete | Qué vigila | Techo |
|---|---|---|
| `scripts/huerfanos.py` | código público que nadie llama | 83 |
| `tests/test_trinquete_de_lineas.py` | ficheros que crecen sin control | 800 |
| `tests/test_wiring.py` | capacidades sin cable a la interfaz | 0 sueltas |
| `tests/test_interfaz_pilotable.py` | `<div onClick>` que el teclado no ve | 1, declarado |
| `tests/test_contrato_del_bus.py` | sucesos publicados que nadie escucha | 0 |

Si uno sube, el CI se pone rojo. Se conecta, se adelgaza o se borra — **nunca
se sube el número** sin escribir por qué en el commit.

---

## 4. Lo EJECUTADO, con su evidencia

### 4.1 La capa de separación con MAGI System `v3.0.1`

**El fallo:** Venim abría su ventana y dentro aparecía la interfaz de MAGI
System IDE, entera. Marco titulado «Venim», contenido diciendo «MAGI SYSTEM
IDE — Supercomputadora Táctica Autónoma».

**La cadena, medida:**

1. `MAGI-IDE-v5.exe` corría y escuchaba en el puerto **1420**.
2. El servidor de Venim pidió ese mismo puerto y falló.
3. El error se escribió en un registro y `start()` volvió como si nada.
4. `main.py` abrió la ventana en `127.0.0.1:1420`. Contestó MAGI.

**Lo arreglado, y ninguna parte basta sola:**

- Buscar puerto (12 candidatos desde el preferido).
- Identificarse: el servidor responde en `/venim.json` diciendo que es Venim.
- Fallar ruidosamente: si no puede levantar el suyo, **no abre la ventana**.

Además se borraron cuatro restos que viajaban dentro del `.exe`: una maqueta
HTML completa de MAGI en `assets/modelo-interfaz/`, una segunda interfaz en
`venim/gui/`, un segundo `GUIServer`, y `magi_sound.mp3` / `tauri.svg` /
`vite.svg` en lo que se sirve. El `.spec` ya **enumera** lo que empaqueta en
vez de meter `assets/` a bulto — esa comodidad era la causa mecánica.

**Verificado:** con MAGI-IDE-v5 aún ocupando el 1420, Venim se apartó al 1421 y
sirvió su interfaz. Título «Venim», cero rastros del otro.

**Tests:** `test_la_ventana_es_la_nuestra.py` (levanta un impostor que contesta
200 a todo, como hacía MAGI), `test_frontera_con_magi.py`,
`test_el_nombre_no_se_queda_atras.py`.

### 4.2 LILIM y la vaina de mielina

**El problema:** el coste dominante no es pensar, es **esperar**. Los
proveedores gratuitos tardan de 3 a 22 s por llamada y una vuelta del enjambre
son tres. Ninguna optimización de prompt compite con no llamar.

**LILIM** es un índice sobre memoria versionada que contesta lo que ya se sabe
en **0,76 a 10,44 ms** (medido). Aporta 9 herramientas; el catálogo pasó de 71
a 80. **No es un modelo y no razona.** Cuando no sabe algo dice `NO LO SÉ` y
escala al enjambre.

**El atajo** (`venim/modules/swarm/atajo.py`) se consulta justo antes de
`_spawn_loop`, que es el último punto donde ahorra algo. Su freno es una lista
de **verbos de trabajo**: «¿qué controles tiene la Vita?» ataja; «arregla el
mapeo de controles de la Vita» no, aunque lleve las mismas palabras.

**La mielina** envuelve al crítico: antes de que critique, un analizador
estático recorre el AST y le entrega los defectos objetivos en microsegundos y
sin red. Con un KoboldCpp local (`VENIM_KOBOLD=1`) añade crítica neuronal
local; sin él no cuesta nada.

> **Dato importante para quien continúe:** en el proyecto de origen
> (`MAGI-System-IDE`) la mielina tenía tests verdes y **cero llamantes en
> producción**. Aquí está enchufada, y hay un test que comprueba que sigue
> enchufada. No se portaron los «sentidos» (ojos/PDF, oídos/audio,
> brazos/docx) porque allí tampoco tenían un solo llamante: portarlos habría
> sido mudar código muerto y llamarlo actualización.

### 4.3 El banco que baja cuando el sistema se queda ciego

`read_file` falló **8 de 8 veces** —el enjambre buscaba el código en una
carpeta vacía— y el banco de evaluación habría dado la misma nota que el día
anterior: 47 × 23 sigue siendo 1081 aunque el sistema esté ciego.

Hay dos bancos y **sus notas no se promedian**:

| Eje | Qué mide | Corredor |
|---|---|---|
| Lo que sabe | aritmética, código, formato, admitir que no sabe | modelo pelado |
| Si además ve | respuestas leídas del repositorio al construirlo | con `read_file`, `grep`, `glob` |

100 % de saber con 0 % de ver da un 50 % que no describe nada. La auto-mejora
de Naoko sí los funde, y así una lectura rota cuenta como la regresión que es.

**Las respuestas no las escribe quien construye el banco:** se derivan del
repositorio. Si mañana `MUESTREO_FPS` pasa a 8.0, el banco espera 8.0 sin que
nadie lo toque.

### 4.4 La ventana

- **25 de los 50 avisos del bus se tiraban a la basura**, incluidos qué ronda
  va y qué está pensando el nodo. Ahora hay un pulso por conversación y una
  traza de herramientas (quién, qué, con qué argumento, qué salió, cuánto
  tardó). `venim/core/contrato.py` declara los 50 con su destino; los internos
  exigen un motivo escrito.
- **Se pilota sin ratón.** Las 12 pestañas y los botones de parada eran
  `<div onClick>`. Ahora son botones con patrón ARIA. Verificado sobre el DOM:
  12 pestañas, 31 controles enfocables, 0 sin nombre accesible.
- **Una sola decisión de aprobación** (había tres, con textos contradictorios).
- **Cabe en un tercio de pantalla**: funciona a 853 px.

### 4.5 Identidad y publicación

- Renombrado completo: 267 ficheros con `git mv` para conservar la historia.
- Los datos del usuario **se mudan solos** de la carpeta anterior; si no puede
  hacerse, se dice y se dejan intactos.
- Icono nuevo: un diafragma de tres hojas, fondo transparente, legible a 16 px.
- README reescrito con diagramas Mermaid alrededor del fin visual.
- Actions compila, verifica que el Python embebido viajó dentro, comprime y
  publica. Una compuerta comprueba que las notas hablan **solo** de la versión
  que se publica.

---

## 5. Lo NO ejecutado, y qué lo refutaría

Ordenado por lo que más valor daría a continuación.

### 5.1 Cerrar el lazo de auto-mejora — *lo más importante*

**Qué falta:** que Naoko corra el marcador, vea qué eje va peor y **proponga
sola** un cambio, en vez de esperar a que alguien escriba una hipótesis.

La maquinaria está: `run_self_improvement` mide antes y después con los dos
ejes fundidos y revierte si hay regresión. Lo que no existe es el disparador
que elige la hipótesis.

**Criterio de refutación:** *se refuta si el ciclo propone cambios que no mueven
ningún número del banco.* Si eso pasa, se retira y se dice.

### 5.2 El taller de arte de extremo a extremo — *sin comprobar*

El automodelo lo declara **sin comprobar**, y es el corazón de Venim. Hace
falta una corrida completa: encargo → contrato → dos autores → medida → crítico
→ entrega, con las capturas y el veredicto guardados.

**Criterio:** *se refuta si el crítico aprueba una entrega a la que le faltan
promesas del contrato*, o si la medida de la máquina no se guarda junto al
artefacto.

### 5.3 Las 10 afirmaciones refutadas del automodelo

Cada una es una promesa rota que hoy está escrita en vez de escondida. Las de
mayor impacto para el fin visual:

- «El crítico del taller puede juzgar lo que se ve en la imagen» — los modelos
  guest no tienen visión. Depende del cascarón local.
- «El vídeo generativo funciona en modo cloud» — hoy no.
- «El prompt llega entero al proveedor guest» — se corta en 7.000 caracteres.

**Criterio:** una afirmación pasa de refutada a sostenida solo con la prueba
que la tumbó, ejecutada y en verde.

### 5.4 Medir el ahorro real de LILIM en uso

Sé que el atajo tarda menos de 200 ms y que una llamada tarda 3-22 s. **No sé
qué porcentaje de encargos reales ataja.** Si es el 1 %, el mecanismo no
compensa su complejidad.

**Criterio:** *se refuta si en un mes de uso real ataja menos del 5 % de los
encargos.* Hace falta un contador persistente; hoy solo se publica un aviso.

### 5.5 Deuda declarada, pequeña y conocida

- `PreviewPanel.tsx` conserva 1 `<div onClick>`, declarado en el `DEUDA` de
  `test_interfaz_pilotable.py`. Esa lista **solo puede menguar**.
- `sys.terminal.out` es un duplicado histórico de `TERMINAL_OUT`, marcado en el
  contrato para unificar.
- 83 huérfanos bajo el techo. Cada uno es una capacidad sin cable o andamiaje
  que sobra.
- `test_cosecha_cookies.py` falla en el entorno Linux de pruebas y **también
  fallaba antes** de todo este trabajo. No es una regresión, pero está rojo.

### 5.6 Lo que NO se hizo a propósito

- **No se portaron los sentidos de LILIM** (ojos/PDF, oídos/audio,
  brazos/docx): sin llamantes en el origen y sin relación con la velocidad.
- **No se borró ingeniería inversa, emuladores ni datos macro**: se
  reencuadraron como medios para la imagen, por decisión explícita.
- **No se tocó el kernel del enjambre.** Funciona; reescribir un motor que
  funciona sale peor que el que hay.

---

## 6. Errores cometidos en esta sesión, y qué enseñan

Van aquí porque son la parte más útil para quien continúe.

| Error | Qué lo destapó | La lección |
|---|---|---|
| Culpé a UPX de un `.exe` que moría al arrancar, y lo escribí en el `.spec` como si estuviera medido | `Get-Command upx` — no estaba ni instalado. Eran dos instancias bloqueando el binario | **«Suena razonable» no es «está comprobado»** |
| Mi script daba la compilación por buena porque «algo responde en el 1420» | Respondía MAGI | El verificador confirmaba que Venim arrancaba usando como prueba la respuesta del programa que se lo impedía |
| El renombrado dejó el título en «MAGI System IDE» | Arrancar el binario y pedirle la página | Un renombrado se comprueba con **una lista de sitios**, no con una búsqueda: la búsqueda solo encuentra los nombres que ya sabías |
| Puse una sonda a KoboldCpp que se hacía siempre | La suite de tests se arrastró | Un acelerador opcional que cobra peaje al que no lo usa está mal hecho |
| Metí el atajo dentro del orquestador | El trinquete de líneas se puso rojo | Hizo de detector de humo: la pieza necesitaba casa propia |
| Mis propios tests de frontera fallaron contra mis propios comentarios | Ellos mismos | Un comentario **debe** poder nombrar el pasado; filtra comentarios antes de mirar |

---

## 7. Cómo comprobar que algo funciona

```
python scripts/verificar.py            # lo de cada push
python scripts/verificar.py --todo     # + los que compilan un .exe

python -m ruff check venim/ tests/
python scripts/huerfanos.py --conteo
python -m pytest tests/ -q
```

Y para el binario, que es lo que se publica:

```
powershell -ExecutionPolicy Bypass -File scripts\compilar_local.ps1
```

Ese script **no termina cuando termina PyInstaller**: arranca el `.exe`,
pregunta `/venim.json` y solo entonces dice que salió bien.

> **Aviso sobre los tests en paralelo.** `pytest -n` da rojos falsos en este
> repositorio: varios tests comparten ficheros temporales. Antes de perseguir
> un fallo que solo aparece con `-n`, **reprodúcelo en serie**. En serie, hoy,
> la suite está verde de la `a` a la `z` salvo `test_cosecha_cookies.py`
> (§5.5), que ya lo estaba.
