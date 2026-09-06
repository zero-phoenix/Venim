# v3.0.0 — Venim: el sistema deja de ser un IDE que además dibuja

**Qué cambia:** VeniceMAGI pasa a llamarse **Venim**, y no es solo un nombre.
El fin del sistema es **crear imagen, vídeo y cine de alta calidad**. Todo lo
demás que lleva dentro —desensamblar binarios, pilotar emuladores, consultar
datos macroeconómicos— deja de ser una lista de funciones y pasa a ser lo que
siempre debió ser: **las formas de conseguir material real cuando lo que pides
tiene que parecer real**.

**Descarga:** en Assets, `Venim-v3.0.0.zip`. Dentro hay **un solo fichero**,
`Venim.exe`: onefile, con su propio Python 3.10 dentro.

> **Tus datos se mudan solos.** El historial de conversaciones, la carpeta de
> trabajo elegida y los artefactos generados viven en una carpeta que ahora se
> llama distinto. La primera vez que abras Venim se renombra sola, con todo
> dentro. Si no puede hacerse —la carpeta abierta en otro proceso, permisos— se
> te dice y tus datos siguen intactos donde estaban: perderlos por intentar
> moverlos habría sido peor que el problema que se venía a resolver.

---

## Por qué el nombre cambia lo que hace

Un generador de imágenes te da lo que salga. Venim convierte tu encargo en un
**contrato de promesas separables**, se lo da a **dos autores que no se ven**, y
pone a un **crítico más estricto** —en otro modelo— a contar cuáles se
cumplieron. Lo que una máquina puede medir lo mide una máquina; lo que no, se
declara **sin verificar** en vez de aprobarse por omisión.

«Salió una imagen» y «salió LA imagen» dejan de ser lo mismo. Y cuando la
máquina y el modelo discrepan, **manda la máquina**.

## Ingeniería inversa y emuladores, reencuadrados

No se ha borrado nada. Se ha dicho para qué está:

- **Ingeniería inversa** — sacar material de donde está: formatos de textura,
  tablas de paleta, assets dentro de un binario. Una referencia real vale más
  que una descrita.
- **Emuladores** — capturar movimiento auténtico. Un plano grabado de una
  consola real es material medible; la descripción de ese plano, no.
- **Datos del mundo real** — cuando la pieza tiene que ser realista, los datos
  que aparecen en ella también. Cada uno con su fuente y su fecha.

## Identidad propia

Icono nuevo: un **diafragma de tres hojas** —lo que decide cuánta luz entra, la
primera decisión de cualquier imagen— con los colores del tema. Tres hojas
porque el sistema tiene tres nodos, y ninguna más porque a 16 px una cuarta no
se distingue. Fondo transparente, legible sobre claro y sobre oscuro.

El anterior era un triángulo, que es la forma del sistema del que salió este.
Un programa que se presenta con la cara de su antecesor no se distingue de él en
la barra de tareas.

## LILIM: no llamar es más rápido que llamar rápido

El coste dominante no es pensar: es **esperar**. Los proveedores gratuitos
tardan de 3 a 22 segundos por llamada y una vuelta del enjambre son tres.

Ahora hay un índice local que contesta lo que ya se sabe **en 0,76 a 10,44 ms**,
medido. Trae 9 herramientas nuevas; el catálogo pasa de 71 a 80. No es un modelo
y no razona: cuando no sabe algo dice `NO LO SÉ` y escala al enjambre — un
índice que inventa sería más rápido y peor que no tenerlo.

El freno que lo hace seguro es una lista de verbos de trabajo: una pregunta
ataja, un encargo no, aunque lleven las mismas palabras.

## La vaina de mielina, envolviendo al crítico

Antes de que critique, un analizador estático recorre el AST de la propuesta y
le entrega los defectos objetivos —un `SyntaxError` con su línea, una función
que solo tiene `pass`, un `except:` desnudo— en microsegundos y sin red. El
prompt los da por ciertos y le pide lo que un AST no puede ver.

Quien levante un **KoboldCpp** local (Qwen 2.5 1.5B, gratis, va en CPU sin
AVX2) obtiene además crítica neuronal local con `VENIM_KOBOLD=1`. Quien no, no
paga nada: la sonda no se hace.

## La ventana deja de esconder el trabajo

- **25 de los 50 avisos del sistema se tiraban a la basura**, incluidos los dos
  que más falta hacen mientras esperas: qué ronda va y qué está pensando el
  nodo. Ahora hay un pulso por conversación y una traza de herramientas que dice
  quién llamó a qué, con qué argumento, qué salió y cuánto tardó.
- **Se puede pilotar sin ratón.** Las doce pestañas y los dos botones de parada
  eran `<div onClick>`: no existían para `Tab` ni para un lector de pantalla.
- **Una sola decisión.** Había tres controles de aprobación con textos que se
  contradecían.
- **Cabe en un tercio de pantalla**: funciona a 853 px de ancho.

## El banco que baja cuando el sistema se queda ciego

`read_file` falló **8 de 8 veces** y el banco de evaluación habría dado la misma
nota que el día anterior: 47 × 23 sigue siendo 1081 aunque el sistema esté
ciego. Ahora hay un segundo banco cuyas respuestas se leen del repositorio al
construirlo, corrido con herramientas de lectura. Las dos notas **no se
promedian**: 100 % de saber con 0 % de ver da un 50 % que no describe nada.

## Errores míos, escritos

- Culpé a UPX de un `.exe` que moría al arrancar. UPX no estaba ni instalado:
  eran dos instancias abiertas que impedían sobrescribir el binario.
- La sonda de KoboldCpp se hacía siempre. Donde el puerto está filtrado en vez
  de cerrado, el plazo se agota entero y la suite de tests se arrastró. Un
  acelerador opcional que cobra peaje al que no lo usa está mal hecho.
- Metí el atajo local dentro del orquestador y el trinquete de líneas se puso
  rojo. Hizo de detector de humo: la pieza tenía que tener casa propia.

## Otros arreglos

- Una conversación reanudada se tragaba en silencio todos los mensajes
  siguientes.
- El árbitro podía entregar `tud.` —cuatro caracteres— como respuesta final.
- Los borradores de auto-ejecución se escribían en la raíz del repositorio.
- La ventana abre con su fondo oscuro definitivo en vez de un fogonazo blanco.

---

**1.920 tests en verde.** Sin eso, este `.zip` no existe.
