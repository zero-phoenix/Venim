import { useState } from "react";

/**
 * LA TRAZA DE HERRAMIENTAS, QUE ES DONDE SE VE SI EL SISTEMA TRABAJA.
 *
 * LO QUE HABÍA, MEDIDO PILOTANDO LA VENTANA EL 2026-09-05
 * ======================================================
 * Veinte segundos de conversación vacía mientras el registro contaba
 * iteraciones, proveedores y latencias. Y después, esto:
 *
 *     MELCHIOR  glob  ok
 *     MELCHIOR  glob  ok
 *     MELCHIOR  glob  ok
 *     MELCHIOR  glob  ok
 *
 * Gris oscuro sobre gris oscuro, siete píxeles, sin argumentos, sin resultado
 * y sin tiempo. Y solo las últimas seis: la vista hacía `slice(-6)`, así que
 * de una tarea de treinta llamadas veías cinco.
 *
 * El resto de la historia estaba en el registro, donde el usuario no mira.
 *
 * LAS TRES DECISIONES DE ESTE COMPONENTE
 * ======================================
 * 1. Se ven TODAS. Una tarea larga se resume arriba («18 llamadas, 2 fallos»)
 *    y se despliega entera de un clic. Recortar por defecto está bien;
 *    recortar sin decir cuánto se recorta, no.
 *
 * 2. Cada fila lleva el argumento. «read_file» no dice nada; «read_file
 *    venim/modules/studio/estilo.py» dice si el enjambre está mirando donde
 *    debe. Ese detalle exacto es el que habría delatado en dos segundos que
 *    el workspace apuntaba a una carpeta vacía.
 *
 * 3. Un fallo se ve como un fallo. Rojo, con el motivo al lado y desplegado
 *    por defecto: es lo que hay que leer, no lo que hay que buscar.
 */

export interface Llamada {
  id: string;
  agent: string;
  tool: string;
  ok?: boolean;
  error?: string | null;
  args?: any;
  resumen?: string;
  ms?: number;
}

/** El argumento que identifica la llamada, en una línea. */
function argumentoCorto(args: any): string {
  if (args == null) return "";
  if (typeof args === "string") return args;
  if (typeof args !== "object") return String(args);
  // Se prefieren los nombres que dicen SOBRE QUÉ actuó la herramienta. Un
  // `{"path": "x.py", "encoding": "utf-8"}` se lee mejor como «x.py» que como
  // el objeto entero, y es lo que distingue una llamada de la siguiente.
  for (const clave of ["path", "ruta", "file", "pattern", "patron", "query",
                       "cmd", "command", "orden", "url", "out_path"]) {
    const v = (args as any)[clave];
    if (typeof v === "string" && v) return v;
  }
  try {
    return JSON.stringify(args);
  } catch {
    return "";
  }
}

function Fila({ ll }: { ll: Llamada }) {
  const fallo = ll.ok === false;
  // Un fallo se abre solo. Lo que salió mal no se esconde detrás de un clic.
  const [abierta, setAbierta] = useState(fallo);
  const arg = argumentoCorto(ll.args);
  const hayDetalle = Boolean(ll.resumen || ll.error);
  const estado = ll.ok === undefined ? "corriendo" : fallo ? "falla" : "ok";

  return (
    <li className={`traza-fila traza-${estado}`}>
      <button
        type="button"
        className="traza-cabeza"
        aria-expanded={abierta}
        disabled={!hayDetalle}
        onClick={() => setAbierta((v) => !v)}
      >
        <span className="traza-punto" aria-hidden="true" />
        <span className="traza-agente">{ll.agent}</span>
        <span className="traza-util">{ll.tool}</span>
        <span className="traza-arg" title={arg}>{arg}</span>
        <span className="traza-estado">
          {ll.ok === undefined ? "ejecutando…" : fallo ? "falló" : "ok"}
        </span>
        <span className="traza-ms">
          {ll.ms !== undefined ? `${(ll.ms / 1000).toFixed(1)} s` : ""}
        </span>
      </button>
      {abierta && hayDetalle && (
        <pre className="traza-detalle">{ll.error || ll.resumen}</pre>
      )}
    </li>
  );
}

export default function TrazaHerramientas({ llamadas }: { llamadas: Llamada[] }) {
  const [todas, setTodas] = useState(false);
  if (llamadas.length === 0) return null;

  const fallos = llamadas.filter((l) => l.ok === false).length;
  const corriendo = llamadas.some((l) => l.ok === undefined);
  const TOPE = 8;
  const ocultas = Math.max(0, llamadas.length - TOPE);
  const visibles = todas ? llamadas : llamadas.slice(-TOPE);

  return (
    <section className="traza" aria-label="Herramientas usadas">
      <header className="traza-resumen">
        <span className="traza-cuenta">
          {llamadas.length} llamada{llamadas.length === 1 ? "" : "s"}
        </span>
        {fallos > 0 && (
          <span className="traza-fallos">
            {fallos} fallo{fallos === 1 ? "" : "s"}
          </span>
        )}
        {corriendo && <span className="traza-vivo">trabajando…</span>}
        {ocultas > 0 && (
          <button
            type="button"
            className="traza-mas"
            onClick={() => setTodas((v) => !v)}
          >
            {todas ? "ver solo las últimas" : `ver las ${ocultas} anteriores`}
          </button>
        )}
      </header>
      <ul className="traza-lista">
        {visibles.map((ll) => <Fila key={ll.id} ll={ll} />)}
      </ul>
    </section>
  );
}
