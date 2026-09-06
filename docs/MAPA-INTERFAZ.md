# Mapa de la interfaz de MAGI

Generado por `venim.modules.gui.mapa`. No arranca la aplicación:
mapea el cableado por topics entre `venim-gui/src` y `venim/`.

| | |
|---|---:|
| Comandos conectados (UI → handler) | 19 |
| Eventos conectados (backend → UI) | 45 |
| Sin nadie al otro lado | 0 |
| Capacidades invisibles | 3 |

## Comandos conectados

_la UI los manda y hay `register_handler` que los atiende_

- `artifacts.list`
- `artifacts.read`
- `eval.run`
- `git.clone`
- `naoko.chat`
- `naoko.improve.decide`
- `naoko.improve.list`
- `naoko.improve.propose`
- `naoko.self_improve`
- `obs.metrics`
- `ritsuko.chat`
- `ritsuko.informes`
- `rpc.state.sync`
- `sys.config`
- `task.archive`
- `task.cancel`
- `task.delete`
- `task.list`
- `task.running`

## Eventos conectados

_el backend los emite y la UI los nombra_

- `agent.delta`
- `agent.delta_end`
- `agent.done`
- `agent.slow_iteration`
- `agent.thought`
- `agent.timeout`
- `agent.tool_result`
- `agent.tool_use`
- `agent.turn_done`
- `error.critical`
- `eval.result`
- `knowledge.recorded`
- `memgraph.status`
- `naoko.diagnostico`
- `naoko.improvement`
- `naoko.log`
- `naoko.status`
- `naoko.trace`
- `naoko.user_message`
- `obs.alert`
- `provider.model_drift`
- `ritsuko.informe`
- `ritsuko.log`
- `ritsuko.status`
- `ritsuko.user_message`
- `ritsuko.veto_de_deriva`
- `sonda.actualizada`
- `swarm.approval_required`
- `swarm.artefacto_listo`
- `swarm.budget_exhausted`
- `swarm.entrada_encolada`
- `swarm.entrega_incompleta`
- `swarm.ronda`
- `swarm.routed`
- `swarm.style`
- `swarm.task_completed`
- `swarm.verificacion_agotada`
- `swarm.verification_failed`
- `system.project_created`
- `system.started`
- `task.archived`
- `task.cancelled`
- `task.deleted`
- `task.titled`
- `task.usage`

## Sin nadie al otro lado

_la UI los nombra y el backend ni los emite ni los atiende_

- (ninguno)

## Capacidades invisibles

_trabajo que se hace y ningún panel muestra_

- `rpc.hello`
- `rpc.policy.check`
- `sys.terminal.out`

