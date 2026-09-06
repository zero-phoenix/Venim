# v2.3.0 — la ventana deja de esconder el trabajo, y una capa local que no llama

**Qué cambia:** la interfaz se ha rehecho pieza a pieza comprobando cada una
sobre la aplicación en marcha, no leyendo el código. Y el sistema estrena una
forma de puntuarse que **baja cuando se queda ciego** — la anterior no.

**Descarga:** en Assets, `VeniceMAGI-v2.3.0.zip`. Dentro hay **un solo
fichero**, `VeniceMAGI.exe`: onefile, con su propio Python 3.10 dentro.

---

## 25 de los 50 avisos del sistema se tiraban a la basura

El motor publicaba 50 sucesos distintos y la ventana solo atendía 25. Entre los
descartados estaban los dos que más falta hacen mientras esperas:

- `swarm.ronda` — qué ronda va, cuántas variantes hay, cuántas llamadas quedan
- `agent.thought` — qué está pensando el nodo ahora mismo

El resultado medido era **veinte segundos de pantalla en blanco** mientras el
registro tenía todo el detalle. Ahora hay un **pulso** por conversación que
escribe una línea por suceso, y una **traza de herramientas** que dice quién
llamó a qué, con qué argumento, qué salió y cuánto tardó.

Para que no vuelva a pasar hay un `contrato.py` que declara los 50 sucesos con
su destino; los internos **exigen un motivo escrito** de por qué nadie los ve.
Un test compara las dos listas y se pone rojo si se separan.

> Mi propio recuento de esto estaba mal: dije 20 de 43 porque mi búsqueda no
> veía la forma `emit("...")` del bucle de agente. Lo encontré revisando mi
> propio trabajo y la cifra real era peor.

## La ventana se puede pilotar sin ratón

Las doce pestañas del panel derecho eran `<div onClick>`. Los dos controles más
consecuentes de toda la aplicación —**PARAR ESTA** y **PARAR TODO**— eran
`<span onClick>`. Cambiar de conversación, lo que más se hace, otro `<div>`.

Nada de eso existía para `Tab`, ni para un lector de pantalla, ni para
automatizar la ventana. Ahora son botones de verdad, con el patrón ARIA de
pestañas: flechas para moverse, `Home`/`End`, y **una sola parada en el
recorrido de Tab** en vez de doce.

Verificado sobre el DOM de la aplicación en marcha: 12 pestañas, 31 controles
enfocables, **0 sin nombre accesible**.

> Y el error que cometí haciéndolo: le puse a cada botón su propio
> `outline: 2px solid`, pisando el anillo de foco que el tema ya definía con
> `box-shadow`. Funcionaba, y era un segundo sistema de foco montado encima del
> que había. Lo encontré leyendo `getComputedStyle` en la ventana real.

## Una sola decisión, y sin saltos de pestaña

Había **tres controles de aprobación** compitiendo, con textos que se
contradecían: uno decía «aplicar cambios» sobre una tarea que no tocaba ningún
fichero. Ahora hay **una barra** que dice los hechos —cuántos ficheros, si los
tests pasaron— y cambia el verbo cuando no hay nada que aplicar.

Y la ventana ya no salta sola de pestaña mientras lees.

## Cabe en un tercio de pantalla

Las columnas llevaban `minWidth` en línea que sumaban 1060 px: por debajo de
eso, la interfaz se rompía. Ahora se apilan y **funciona a 853 px de ancho**,
que es un tercio de un monitor de 2560.

## El banco que baja cuando el sistema se queda ciego

Pilotando la aplicación, `read_file` falló **8 de 8 veces**: el enjambre
buscaba el código en una carpeta vacía. El banco de evaluación habría dado
exactamente la misma nota que el día anterior, porque 47 × 23 sigue siendo 1081
aunque el sistema no encuentre un solo fichero.

Hay un segundo banco cuyas **respuestas se leen del repositorio** al construirlo
—si mañana una constante cambia, el banco espera el valor nuevo sin que nadie lo
toque— y que se corre con un corredor **con herramientas de lectura**, porque
con un modelo pelado su cero significaría «le tapamos los ojos» en vez de «está
ciego».

Las dos notas **no se promedian**: 100 % de saber y 0 % de ver da un 50 % que no
describe nada. La auto-mejora de Naoko sí las funde, y así una lectura rota
cuenta como la regresión que es y revierte el cambio.

> Este banco corrige un fallo mío: en mi propio plan había propuesto medir el
> sistema con un examen **escrito por mí**, que es el mismo jurado circular que
> este repositorio ya había cazado y anotado como refutado.

## La capa local: no llamar es más rápido que llamar rápido

El coste dominante de este sistema no es pensar: es **esperar**. Los
proveedores gratuitos tardan de 3 a 22 segundos por llamada y una vuelta del
enjambre son tres como mínimo. Ninguna optimización de prompt compite con no
hacer la llamada.

Ahora hay un índice local —**LILIM**, traído del proyecto de origen— que
contesta lo que ya se sabe **en 0,76 a 10,44 ms**, medido en esta máquina.
Entre 300 y 25.000 veces más rápido que la vuelta que sustituye. Trae 9
herramientas nuevas para el enjambre; el catálogo pasa de 71 a 80.

No es un modelo y no razona: es un índice sobre memoria versionada. Cuando no
sabe algo dice `NO LO SÉ` y escala al enjambre en vez de rellenar el hueco —
un índice que inventa sería más rápido y peor que no tenerlo.

El freno que lo hace seguro es una lista de verbos de trabajo: «¿qué controles
tiene la Vita?» ataja, «arregla el mapeo de controles de la Vita» no, aunque
lleve las mismas palabras. Seis encargos de trabajo cargados de términos
indexados van en la suite intentando colarse.

## La vaina de mielina, envolviendo a Balthasar

Antes de que Balthasar critique, un analizador estático recorre el AST de la
propuesta y le entrega los defectos objetivos —un `SyntaxError` con su línea,
una función que solo tiene `pass`, un `except:` desnudo— en microsegundos y sin
red. El prompt los da por ciertos y le pide lo que un AST no puede ver.

Sin esto, la mitad de las críticas de la primera ronda eran «esto no compila»,
cuatro veces en paralelo, a 3-22 s la llamada.

Quien levante un **KoboldCpp** local (Qwen 2.5 1.5B, gratis, va en CPU sin
AVX2) obtiene además una crítica neuronal local, activándola con
`VENICEMAGI_KOBOLD=1`. Quien no, no paga nada: la sonda no se hace.

> Esa activación explícita salió de un error mío. La primera versión sondeaba
> siempre y memoizaba un minuto, que parecía barato; donde el puerto está
> filtrado en vez de cerrado, el plazo se agota entero y la suite de tests se
> arrastró. Un acelerador opcional que cobra peaje al que no lo usa está mal
> hecho, por pequeño que sea el peaje.

> **Lo que no se ha traído, y por qué.** El paquete original incluía sentidos
> —ojos (PDF), oídos (audio), brazos (`.docx`)— y cuatro funciones de
> lubricación neuronal. Al medirlo, ninguna tenía un solo llamante en
> producción: tests verdes y cero uso. Traerlas habría sido mudar código muerto
> de un repositorio a otro y llamarlo actualización.

## Elegir la carpeta de trabajo

El sistema apuntaba a una caja de arena vacía y no había forma de cambiarlo
desde la ventana. Ahora se elige en ⚙, y el panel dice cuántos ficheros `.py`
ve realmente donde apunta.

## Otros arreglos

- Una conversación reanudada se tragaba en silencio todos los mensajes
  siguientes.
- Casper podía entregar `tud.` —cuatro caracteres— como respuesta final, con la
  capa de proveedores ya avisando de que no servía. Ahora la respuesta final
  pasa por el mismo filtro antes de publicarse.
- Los borradores de auto-ejecución se escribían en la raíz del repositorio y uno
  llegó a colarse en un commit.
- Icono nuevo: tres trazos que no se tocan y un punto en el centro, con los
  colores del tema. Fondo transparente, legible a 16 px.
- La ventana abre con su fondo oscuro definitivo en vez de un fogonazo blanco.

---

**1.920 tests en verde.** Sin eso, este `.zip` no existe.
