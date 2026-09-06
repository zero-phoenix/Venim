/**
 * EL PULSO: lo que el sistema está haciendo, mientras lo hace.
 *
 * LOS VEINTE SEGUNDOS EN BLANCO NO ERAN FALTA DE INFORMACIÓN
 * ==========================================================
 * Medido pilotando la aplicación el 2026-09-05: veinte segundos de
 * conversación vacía tras pulsar Ejecutar. Mientras tanto, el núcleo estaba
 * publicando esto por el socket:
 *
 *     swarm.entrada_encolada  {pendientes: 0}
 *     swarm.ronda             {round: 1, count: 3, calls_used: 4, techo: 40}
 *     agent.thought           {text: "voy a leer estilo.py para..."}
 *     agent.timeout           {provider: "gpt"}
 *
 * Una barra de progreso con contador de presupuesto, el razonamiento del nodo
 * y el aviso de que un proveedor se había caído. Todo ello llegaba a la
 * ventana y se descartaba en el `else` final de `useMagiSocket`.
 *
 * Este componente es donde aterriza. No inventa nada: pinta lo que ya venía.
 *
 * POR QUÉ UNA LÍNEA POR SUCESO Y NO UNA BARRA
 * ===========================================
 * Una barra de progreso miente cuando no sabe cuánto falta, y aquí no se
 * sabe: depende de cuántas rondas pida el debate y de qué proveedor conteste.
 * Una lista de lo que ha ido pasando no miente nunca y además deja rastro:
 * cuando algo sale mal, lo que hacía falta era saber por dónde iba.
 */

export interface Latido {
  id: string;
  texto: string;
  tono: string;
}

export default function Pulso({ latidos, activo }:
                              { latidos: Latido[]; activo: boolean }) {
  if (latidos.length === 0) return null;
  // Se ve el último y unos pocos antes. El histórico completo de la tarea
  // vive en el terminal; aquí interesa el «ahora» con algo de contexto.
  const visibles = latidos.slice(-6);
  const ultimo = visibles[visibles.length - 1];

  return (
    <section className="pulso" aria-label="Qué está pasando"
             aria-live="polite" aria-atomic="false">
      {visibles.map((l) => (
        <div key={l.id}
             className={`pulso-linea pulso-${l.tono}`
                        + (l.id === ultimo.id && activo ? " pulso-ahora" : "")}>
          <span className="pulso-punto" aria-hidden="true" />
          <span className="pulso-texto">{l.texto}</span>
        </div>
      ))}
    </section>
  );
}
