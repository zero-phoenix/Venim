# v3.0.1 — Venim deja de poder mostrar la interfaz de otro programa

**Qué cambia:** una corrección de raíz sobre la versión anterior. Venim abría
su ventana y dentro aparecía **la interfaz de MAGI System IDE**, entera. No era
un texto olvidado en el código: era otro programa.

**Descarga:** en Assets, `Venim-v3.0.1.zip`. Dentro hay **un solo fichero**,
`Venim.exe`: onefile, con su propio Python 3.10 dentro.

---

## Lo que pasaba, medido

El marco de la ventana decía «Venim». El contenido decía «MAGI SYSTEM IDE —
Supercomputadora Táctica Autónoma (independiente de Venim)». La cadena entera:

1. `MAGI-IDE-v5.exe` estaba corriendo y escuchaba en el puerto **1420**.
2. Venim arrancó y su servidor pidió ese mismo puerto.
3. Falló, con «address already in use».
4. **El error se escribió en un registro y la función volvió como si nada.**
5. `main.py`, sin forma de enterarse, abrió la ventana en `127.0.0.1:1420`.
6. Ahí contestó MAGI.

Dos programas que comparten antepasado comparten también los números que
alguien eligió una vez. El puerto fijo no era una decisión: era una herencia.

## Las tres cosas que lo arreglan, y ninguna basta sola

- **Buscar puerto.** Si el preferido está ocupado se prueban los siguientes.
  Un programa que solo sabe vivir en un número deja de funcionar en cuanto
  alguien más lo quiere.
- **Identificarse.** El servidor responde en `/venim.json` diciendo que es
  Venim. Sin esto, «hay algo escuchando» se confunde con «está el mío».
- **Fallar ruidosamente.** Si no puede levantar el suyo, Venim **no abre la
  ventana**. Abrirla sobre un servidor ajeno es peor que no abrirla: el
  usuario cree que está usando Venim.

Verificado con MAGI-IDE-v5 aún ocupando el 1420: Venim se apartó solo al 1421
y sirvió su interfaz, con su título y sin un solo rastro del otro.

## La capa de separación, y lo que había debajo

El fallo del puerto era el síntoma. Debajo había **cuatro restos** del proyecto
del que salió este, y todos viajaban dentro del `.exe`:

- `assets/modelo-interfaz/magi-interfaz-v6.html` — una maqueta COMPLETA de la
  interfaz de MAGI. Nadie la importaba; no hacía falta.
- `venim/gui/` — una SEGUNDA interfaz, con su `magi.proto` y su `src-tauri`.
- Dos clases `GUIServer` en el árbol. Dos servidores para una ventana es uno
  que sirve lo que no toca.
- `magi_sound.mp3`, `tauri.svg` y `vite.svg` servidos junto a la interfaz.

Borrados. Y el `.spec` ya no empaqueta `assets/` a bulto: **enumera** lo que
viaja dentro. Esa comodidad era la causa mecánica de que una maqueta de otro
programa se publicara en cada release.

## Y un fallo en mi propio verificador

El script de compilación daba la compilación por buena comprobando que «algo
responde en el 1420». Respondía MAGI. **El verificador confirmaba que Venim
arrancaba usando como prueba la respuesta del programa que le impedía
arrancar.** Ahora pregunta `/venim.json`: no vale que haya algo, tiene que
contestar que es Venim.

Es el corolario que este repositorio se repite: el instrumento de medida es el
mejor escondite.

## Lo que impide que vuelva

Tres ficheros de tests nuevos, con el fallo reproducido dentro:

- `test_la_ventana_es_la_nuestra.py` levanta un impostor que contesta 200 a
  todo —como hacía MAGI— y comprueba que Venim no lo confunde con el suyo.
- `test_frontera_con_magi.py` vigila que no vuelva ninguna maqueta, ninguna
  segunda interfaz, ningún segundo servidor y ningún fichero ajeno en lo que
  se sirve.
- `test_el_nombre_no_se_queda_atras.py` comprueba el título de la ventana, que
  se había quedado en «MAGI System IDE» tras el renombrado porque esa cadena
  no contenía ninguno de los nombres que mi búsqueda sustituía.

---

**Venim y MAGI System son dos proyectos distintos.** A partir de aquí, el
código lo comprueba en cada push.
