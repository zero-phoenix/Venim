# Prompt de continuidad — para pegar en Google Antigravity

> Copia todo lo que hay debajo de la línea y pégalo como primer mensaje.

---

Vas a continuar el desarrollo de **Venim**, un proyecto Python + React que ya
está en marcha. Lee esto entero antes de tocar nada: describe cómo trabaja este
repositorio, y trabajar de otra forma aquí produce daño que cuesta más que el
avance.

## 1. Lo primero que tienes que hacer

Lee `docs/PLAN-VENIM.md`. Es el estado real del proyecto: lo hecho con su
evidencia, lo que falta con su criterio de refutación, y los errores ya
cometidos para que no los repitas. **No empieces a programar sin leerlo.**

Después, y antes de escribir código, ejecuta esto para ver por ti mismo dónde
está todo:

```
python -m pytest tests/ -q
python scripts/huerfanos.py --conteo
python -m ruff check venim/ tests/
```

## 2. Qué es Venim, y el criterio que decide

**Venim crea imagen, vídeo y cine de alta calidad, y mide la calidad en vez de
suponerla.** Todo lo demás que lleva dentro —ingeniería inversa, emuladores,
datos macroeconómicos— existe para servir a esa imagen: son las formas de
conseguir material real cuando lo que se pide tiene que parecer real.

Usa esa frase para decidir. Una capacidad nueva se justifica diciendo **qué
imagen ayuda a hacer**. Si no puedes decirlo, no entra.

**Venim NO es MAGI System IDE.** Son dos proyectos distintos que comparten
antepasado. Esa herencia ya causó un fallo grave: la ventana de Venim llegó a
mostrar la interfaz de MAGI entera, porque ambos usaban el puerto 1420 y el
servidor de Venim se tragaba el error al no poder tomarlo. No mezcles nada de
MAGI aquí; hay tests que lo comprueban en cada push
(`tests/test_frontera_con_magi.py`).

## 3. Cómo se trabaja en este repositorio

Estas diez reglas no son estilo. Cada una nació de un fallo concreto:

1. **Todo cambio se conecta o se borra.** Nunca añadas código sin un llamante
   real. Si escribes una función que nadie invoca, bórrala o conéctala en el
   mismo commit.
2. **Un test sobre una pieza aislada no prueba que el sistema la use.** Añade
   siempre un test que compruebe que el sistema *llama* a lo que escribiste.
3. **Cada capacidad tiene que poder invocarse desde la interfaz.**
4. **Arrancar encuentra fallos que leer no encuentra.** Ejecuta el programa;
   no te fíes de haber leído el código.
5. **«No he podido comprobarlo» no es «está bien».** Declara lo no verificado
   en vez de aprobarlo por omisión.
6. **El binario publicado no es el mismo programa que el de desarrollo.**
7. **Arreglar algo no es lo mismo que arreglarlo donde importa.**
8. **Lo que abre un navegador no se sondea.**
9. **Los trinquetes bajan, no suben.**
10. **Escribe ficheros con Python, `newline='\n'` y sin BOM.** PowerShell mete
    BOM y ya rompió un módulo con un `SyntaxError` que no señalaba a ninguna
    línea.

Y el corolario que más caro sale olvidar:

> **El instrumento de medida es el mejor escondite.** Cuando algo «pasa»,
> comprueba que el verificador mide lo que crees. En este proyecto, dos veces
> un verificador dio por bueno algo que no lo estaba.

### Los trinquetes

Son números que **solo pueden bajar**. Si tu cambio los sube, el CI se pone
rojo, y la salida correcta es conectar, adelgazar o borrar — **no subir el
número**. Si de verdad hay que subirlo, explica por qué en el mismo commit.

| Trinquete | Techo |
|---|---|
| `scripts/huerfanos.py` (código público sin llamantes) | 83 |
| `tests/test_trinquete_de_lineas.py` | 800 líneas por fichero |
| `tests/test_wiring.py` | 0 capacidades sueltas |
| `tests/test_interfaz_pilotable.py` | 1 `<div onClick>`, declarado |
| `tests/test_contrato_del_bus.py` | 0 sucesos sin escuchar |

### Cómo se escriben los comentarios aquí

Los comentarios de este repositorio explican **por qué existe algo y qué fallo
lo forzó**, con la medición al lado. No describen lo que el código ya dice.
Sigue ese estilo: quien venga a simplificar algo tiene que leer primero por qué
está ahí. Todo en **español**.

## 4. Restricciones que no se negocian

- **Cero claves de API, cero cuentas, cero logins** en el camino principal.
  Solo proveedores de nube gratuitos en modo invitado.
- **Cero dinero adicional.** Nada de servicios de pago.
- Electricidad local ilimitada: puedes usar la GPU local (una GTX 1050) y
  procesos locales sin límite.
- El `.exe` abre **su propia ventana pywebview**, nunca un navegador.
- La interfaz es **permanentemente oscura**, legible, sin reducir funciones.
- No sortees CAPTCHAs ni autenticaciones.

## 5. Por dónde continuar, en orden

Está detallado en `docs/PLAN-VENIM.md` §5. En resumen:

1. **Cerrar el lazo de auto-mejora.** La maquinaria existe: `run_self_improvement`
   mide con dos ejes y revierte si hay regresión. Falta el disparador que
   **elige la hipótesis solo**, mirando qué eje del marcador va peor.
   *Se refuta si el ciclo propone cambios que no mueven ningún número del banco.*
2. **El taller de arte de extremo a extremo.** El automodelo lo declara **sin
   comprobar** y es el corazón del proyecto. Hace falta una corrida completa
   con las capturas y el veredicto guardados.
   *Se refuta si el crítico aprueba una entrega a la que le faltan promesas.*
3. **Las 10 afirmaciones refutadas** de `docs/AUTOMODELO.json`. Cada una es una
   promesa rota, hoy escrita en vez de escondida.
4. **Medir el ahorro real de LILIM.** Sé que ataja en menos de 200 ms; **no sé
   qué porcentaje de encargos reales ataja**. *Se refuta si en un mes de uso
   real ataja menos del 5 %.*

## 6. Trampas concretas de este repositorio

- **`pytest -n` da rojos falsos.** Varios tests comparten ficheros temporales.
  Antes de perseguir un fallo que solo aparece en paralelo, **reprodúcelo en
  serie**. Hoy, en serie, la suite está verde salvo `test_cosecha_cookies.py`,
  que ya lo estaba antes.
- **No compiles con instancias abiertas.** PyInstaller no puede sobrescribir
  `dist\Venim.exe` si el programa está corriendo, no da error claro, y lo que
  pruebas es un binario viejo a medio escribir.
- **Verifica el binario arrancándolo**, con `scripts\compilar_local.ps1`. Ese
  script pregunta `/venim.json` para asegurarse de que quien responde es Venim
  y no otro programa en el mismo puerto.
- **Un renombrado se comprueba con una lista de sitios, no con una búsqueda.**
  La búsqueda solo encuentra los nombres que ya sabías que existían.
- Los datos del usuario viven en `%LOCALAPPDATA%\Venim`. Si tocas esa ruta,
  **migra**, no abandones: ahí está el historial y los artefactos.

## 7. Qué se espera de ti

- Trabaja **en español**, incluidos comentarios, mensajes de commit y
  documentación.
- **Mide antes de afirmar.** Si dices que algo tarda 5 ms, enseña la medición.
- **Escribe tus errores.** Este repositorio conserva los fallos cometidos
  porque son la parte más útil de su documentación. Si te equivocas y lo
  descubres, corrígelo *y deja escrito qué creías y qué era*.
- **No inventes.** Si no puedes comprobar algo, dilo. «Sin comprobar» es un
  resultado válido; un veredicto inventado, no.
- Antes de dar por terminado cualquier trabajo: ruff limpio, trinquetes verdes,
  suite en serie verde, y el binario arrancando.
