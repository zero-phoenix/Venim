import type { ApprovalRequest } from "../lib/approval";

/**
 * UNA DECISIÓN, UN SITIO, CON LOS HECHOS AL LADO.
 *
 * LO QUE HABÍA, MEDIDO PILOTANDO LA APLICACIÓN EL 2026-09-05
 * ==========================================================
 * Cuando una propuesta quedaba lista aparecían TRES controles distintos para
 * lo mismo, en tres sitios distintos:
 *
 *   · «✅ Apruebo (Ejecutar)» en la barra inferior — que no ejecutaba nada:
 *     escribía «sí» en el chat.
 *   · «▶ Ejecutar en PC» encima del bloque de código.
 *   · «Apruebo» / «Rechazo» en la pestaña de diff.
 *
 * Pulsé dos de los tres y el sistema ejecutó la resolución final DOS VECES.
 *
 * Y el panel de diff decía, una línea debajo de la otra:
 *
 *     Aprobación requerida
 *     ⚠ No toca ningún fichero ni ejecuta nada: no hay cambio que aprobar.
 *
 * Pedir una aprobación y decir en la línea siguiente que no hay nada que
 * aprobar es la manera más rápida de enseñar a pulsar sin leer. Y una puerta
 * que se abre sola no es una puerta.
 *
 * LAS TRES DECISIONES DE ESTE COMPONENTE
 * ======================================
 * 1. **Los hechos van pegados al botón.** Cuántos ficheros toca, si los tests
 *    pasaron, si es reversible. Decidir sin ver qué se decide es lo que la
 *    barra vieja invitaba a hacer, y por eso el diff estaba en otra pestaña.
 *
 * 2. **Si no hay nada que aprobar, no se pide aprobación.** Se ofrece
 *    continuar, que es lo que de verdad va a pasar.
 *
 * 3. **Los tests en rojo se dicen en rojo.** Era un aviso más entre otros, con
 *    el mismo peso que «reversible». No es un aviso más: es el motivo por el
 *    que uno diría que no.
 */

interface Props {
  approval: ApprovalRequest | null;
  onApprove: () => void;
  onModify: () => void;
  onCancel: () => void;
}

export default function Decision({ approval, onApprove, onModify, onCancel }: Props) {
  const ficheros = approval?.files_touched ?? 0;
  // «Nada que aprobar» es un ESTADO, no un aviso a pie de página. Sin
  // contexto del backend no se puede afirmar: se pregunta en vez de suponer.
  const sinCambios = approval != null && ficheros === 0;
  const testsRojos = approval?.tests_ran === true && approval?.tests_passed === false;

  const hechos: string[] = [];
  if (approval) {
    hechos.push(ficheros === 0 ? "no toca ningún fichero"
                : `${ficheros} fichero${ficheros === 1 ? "" : "s"}`);
    hechos.push(approval.tests_ran
                ? (approval.tests_passed ? "tests en verde" : "TESTS EN ROJO")
                : "sin tests");
    if (approval.reversible === false) hechos.push("NO reversible");
  } else {
    // Sin contexto no se inventa: se dice que falta. Es lo que separa «no lo
    // sé» de «no hay nada», y son cosas distintas.
    hechos.push("el backend no envió el detalle del cambio");
  }

  return (
    <section className={`decision${testsRojos ? " decision-rojo" : ""}`}
             aria-label="Decisión pendiente">
      <div className="decision-que">
        <strong className="decision-titulo">
          {sinCambios ? "Listo para entregar" : "Esperando tu decisión"}
        </strong>
        <span className="decision-hechos">
          {hechos.map((h, i) => (
            <span key={i}
                  className={h === "TESTS EN ROJO" || h === "NO reversible"
                             ? "decision-grave" : ""}>
              {h}{i < hechos.length - 1 ? " · " : ""}
            </span>
          ))}
        </span>
      </div>
      <div className="decision-botones">
        <button type="button" className="decision-si" onClick={onApprove}>
          {sinCambios ? "Continuar" : "Aprobar y ejecutar"}
        </button>
        <button type="button" className="decision-no" onClick={onModify}>
          Cambiar algo
        </button>
        <button type="button" className="decision-alto" onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </section>
  );
}
