import { create } from 'zustand';
import type { ApprovalRequest } from './lib/approval';
import { appendBounded } from './lib/history';

export interface AgentMessage {
  id: string;
  agent: string;
  role: string;
  provider: string;
  content: string;
  changes: number;
  stats: string;
}

export interface Project {
  name: string;
  desc: string;
}

export interface Metrics {
  prov_a: string;
  prov_b: string;
  prov_c: string;
  status: string;
}

interface MagiState {
  connected: boolean;
  setConnected: (status: boolean) => void;
  
  activeConversationId: string;
  setActiveConversationId: (id: string) => void;
  conversations: Record<string, AgentMessage[]>;
  
  // Getter derivado para compatibilidad
  messages: AgentMessage[]; 
  
  addMessage: (msg: AgentMessage & { task_id?: string }) => void;
  // MAGI 9.0 §1.2 — streaming token a token
  streaming: Record<string, { agent: string; text: string; provider: string; family: string }>;
  appendDelta: (d: { task_id: string; agent: string; text: string; provider?: string; family?: string }) => void;
  endDelta: (d: { task_id: string; agent: string }) => void;
  // §2.2 — traza de herramientas: convierte una caja negra en un colaborador
  // EL PULSO: lo que el sistema dice que está haciendo, ahora mismo.
  //
  // POR QUÉ ESTO NO EXISTÍA, CONTADO SOBRE EL CÓDIGO
  // ================================================
  // El núcleo publica 50 clases de suceso. La ventana atendía 25. Entre las
  // 25 tiradas estaban `swarm.ronda` —que lleva `{round, count, calls_used,
  // techo}`, o sea una barra de progreso con contador de presupuesto ya
  // calculada— y `swarm.entrada_encolada`, que lleva cuántos mensajes hay
  // por delante del tuyo. Y `agent.thought`, que es el razonamiento del nodo
  // mientras piensa.
  //
  // Los veinte segundos de pantalla en blanco que se midieron pilotando la
  // aplicación no eran falta de información: eran esta información, tirada al
  // llegar. El pulso es donde aterriza.
  pulso: Record<string, Array<{ id: string; texto: string; tono: string }>>;
  anota: (task_id: string, texto: string, tono?: string) => void;
  toolTrace: Array<{ id: string; task_id: string; agent: string; tool: string;
                     ok?: boolean; error?: string | null;
                     args?: any; resumen?: string;
                     inicio?: number; ms?: number }>;
  addToolUse: (d: { task_id: string; agent: string; calls: any[] }) => void;
  addToolResult: (d: { task_id: string; agent: string; results: any[] }) => void;
  // §7.4 — aprobación CON CONTEXTO. Antes el estado de aprobación se deducía
  // buscando una frase dentro del terminal, y el diff se quedaba sin original
  // que enseñar. Ahora llega un evento con los ficheros y su contenido previo.
  approval: ApprovalRequest | null;
  setApproval: (a: ApprovalRequest | null) => void;
  // §7.3 — panel de coste. El backend contaba los tokens y los tiraba: la
  // tabla `token_ledger` llevaba vacía desde que se creó porque nadie
  // llamaba a record_usage(). Ahora llegan por `task.usage`.
  // Ciclo de mejora en curso, si hay alguno. Naoko publica cada transición.
  improvement: any | null;
  setImprovement: (m: any) => void;
  usage: Array<{ id: string; task_id: string; agent: string; family: string;
                 tokens_in: number; tokens_out: number; elapsed_s: number;
                 iterations: number; tool_calls: number }>;
  addUsage: (u: any) => void;
  // §2.3 — por qué ruta fue la petición
  route: { route: string; reason: string; max_rounds: number } | null;
  setRoute: (r: any) => void;
  // §3.4 — la observabilidad es inútil si el usuario no la ve
  alerts: Array<{ id: string; kind: string; subject: string; detail: string; severity: string }>;
  addAlert: (a: any) => void;
  dismissAlert: (id: string) => void;
  startNewConversation: (id?: string) => void;
  // v5.3.0 — títulos de tareas (generados por IA en el backend) y gestión de
  // la lista de conversaciones: archivar / borrar.
  taskTitles: Record<string, string>;
  setTaskTitle: (taskId: string, titulo: string) => void;
  removeConversation: (taskId: string) => void;
  setConversations: (convs: Record<string, AgentMessage[]>, titulos?: Record<string, string>) => void;
  
  terminalOutput: string;
  appendTerminal: (text: string) => void;
  // §7.3 — se ponía escaneando `terminalOutput` entero en busca de una frase,
  // dos veces por repintado. Medido: 2,7 ms por repintado sobre una cadena de
  // 4,9 MB, y con un useEffect que se dispara en cada línea nueva.
  awaitingApproval: boolean;
  setAwaitingApproval: (v: boolean) => void;
  
  sysCommand: (cmd: string) => void;

  projects: Project[];
  setProjects: (projects: Project[]) => void;

  metrics: Metrics;
  setMetrics: (metrics: Metrics) => void;

  telemetry: any[];
  setTelemetry: (data: any[]) => void;

  fileTree: any[];
  setFileTree: (tree: any[]) => void;

  activeFilePath: string | null;
  activeFileContent: string;
  setActiveFile: (path: string, content: string) => void;

  naokoMessages: AgentMessage[];
  addNaokoMessage: (msg: AgentMessage) => void;
  naokoStatus: string;
  setNaokoStatus: (status: string) => void;

  // Ritsuko va en su propio cajón, no en el de Naoko: es quien la audita, y
  // mezclar los dos hilos hace imposible saber quién dijo qué.
  ritsukoMessages: AgentMessage[];
  addRitsukoMessage: (msg: AgentMessage) => void;
  ritsukoStatus: string;
  setRitsukoStatus: (status: string) => void;
  ritsukoInformes: Array<{ nombre: string; ruta: string; bytes: number }>;
  setRitsukoInformes: (v: Array<{ nombre: string; ruta: string; bytes: number }>) => void;
}

export const useMagiStore = create<MagiState>((set) => ({
  connected: false,
  setConnected: (status) => set({ connected: status }),
  
  activeConversationId: "default",
  conversations: { "default": [] },
  messages: [],
  
  setActiveConversationId: (id) => set((state) => ({ 
    activeConversationId: id,
    messages: state.conversations[id] || []
  })),
  
  startNewConversation: (id) => set((state) => {
    const newId = id || `task_${Math.random().toString(36).substring(2, 10)}`;
    return {
      activeConversationId: newId,
      conversations: { ...state.conversations, [newId]: [] },
      messages: []
    };
  }),

  // v5.3.0 — títulos y gestión de la lista de conversaciones.
  taskTitles: {},
  setTaskTitle: (taskId, titulo) => set((state) => ({
    taskTitles: { ...state.taskTitles, [taskId]: titulo },
  })),
  removeConversation: (taskId) => set((state) => {
    const conversations = { ...state.conversations };
    delete conversations[taskId];
    const taskTitles = { ...state.taskTitles };
    delete taskTitles[taskId];
    const stillActive = taskId !== state.activeConversationId;
    return {
      conversations,
      taskTitles,
      // Si borramos la activa, volvemos a "default" para no quedar en blanco.
      activeConversationId: stillActive ? state.activeConversationId : "default",
      messages: stillActive ? state.messages : (conversations["default"] || []),
    };
  }),
  setConversations: (convs, titulos) => set(() => ({
    conversations: convs,
    taskTitles: titulos || {},
  })),

  addMessage: (msg) => set((state) => {
    const targetId = msg.task_id || state.activeConversationId;
    const currentList = state.conversations[targetId] || [];
    const newConversations = { ...state.conversations, [targetId]: [...currentList, msg] };

    // El AGENT_POST definitivo reemplaza al buffer de streaming del mismo agente.
    const streaming = { ...state.streaming };
    delete streaming[`${targetId}:${msg.agent}`];

    return {
      conversations: newConversations,
      messages: newConversations[state.activeConversationId] || [],
      streaming,
    };
  }),
  
  // Buffers de streaming, indexados por task_id+agente. Se vacían cuando
  // llega el AGENT_POST definitivo con el texto completo.
  streaming: {},
  appendDelta: (d) => set((state) => {
    const key = `${d.task_id}:${d.agent}`;
    const prev = state.streaming[key];
    return {
      streaming: {
        ...state.streaming,
        [key]: {
          agent: d.agent,
          text: (prev?.text || "") + d.text,
          provider: d.provider || prev?.provider || "",
          family: d.family || prev?.family || "",
        },
      },
    };
  }),
  endDelta: (d) => set((state) => {
    const next = { ...state.streaming };
    delete next[`${d.task_id}:${d.agent}`];
    return { streaming: next };
  }),

  toolTrace: [],
  // LO QUE ESTA TRAZA TIRABA, Y POR QUÉ IMPORTA
  // ===========================================
  // Pilotando la ventana el 2026-09-05: durante veinte segundos la
  // conversación estuvo vacía mientras el registro contaba iteraciones,
  // herramientas y latencias. Cuando por fin apareció algo, era esto:
  //
  //     MELCHIOR  glob  ok
  //     MELCHIOR  glob  ok
  //
  // Cuatro líneas grises de siete píxeles. Sin argumentos, sin resultado, sin
  // tiempo — y sin las anteriores, porque la vista solo pintaba las últimas
  // seis. El evento del bus SÍ traía los argumentos y el contenido devuelto:
  // se descartaban aquí, en `c.tool`, antes de llegar a la pantalla.
  //
  // Un enjambre que trabaja tres minutos y solo te enseña la palabra «ok» es
  // una caja negra por decisión de la interfaz, no por naturaleza.
  pulso: {},
  anota: (task_id, texto, tono = "info") => set((state) => {
    const previo = state.pulso[task_id] || [];
    // Se descarta el repetido consecutivo: «ronda 2» tres veces seguidas es
    // ruido, y el ruido en el sitio donde se mira el progreso es peor que el
    // silencio — enseña a no mirar.
    if (previo.length && previo[previo.length - 1].texto === texto) return {};
    return {
      pulso: {
        ...state.pulso,
        // Techo de 60: esto se pinta entero y crece durante toda la tarea.
        [task_id]: [...previo.slice(-59),
                    { id: Math.random().toString(36), texto, tono }],
      },
    };
  }),

  addToolUse: (d) => set((state) => ({
    toolTrace: [
      ...state.toolTrace.slice(-200),
      ...d.calls.map((c: any) => ({
        id: Math.random().toString(36),
        task_id: d.task_id, agent: d.agent, tool: c.tool,
        args: c.args ?? c.arguments ?? null,
        inicio: Date.now(),
      })),
    ],
  })),
  addToolResult: (d) => set((state) => {
    // Marca los últimos usos pendientes de este agente con su resultado.
    const trace = [...state.toolTrace];
    for (const r of d.results) {
      for (let i = trace.length - 1; i >= 0; i--) {
        if (trace[i].agent === d.agent && trace[i].tool === r.tool
            && trace[i].ok === undefined) {
          const bruto = r.content ?? r.result ?? r.output ?? "";
          trace[i] = {
            ...trace[i], ok: r.ok, error: r.error,
            // Se recorta AQUÍ y no al pintar: una salida de cien mil
            // caracteres en el estado repinta toda la lista cada vez que
            // llega otra. Lo que se guarda es lo que se enseña plegado; lo
            // largo vive en el terminal, que es su sitio.
            resumen: typeof bruto === "string" ? bruto.slice(0, 600)
                     : JSON.stringify(bruto ?? "").slice(0, 600),
            ms: trace[i].inicio ? Date.now() - (trace[i].inicio as number) : undefined,
          };
          break;
        }
      }
    }
    return { toolTrace: trace };
  }),

  approval: null,
  setApproval: (approval) => set({ approval }),

  improvement: null,
  setImprovement: (improvement) => set({ improvement }),

  usage: [],
  addUsage: (u) => set((state) => ({
    usage: [...state.usage.slice(-199),
            { id: Math.random().toString(36), ...u }],
  })),

  route: null,
  setRoute: (r) => set({ route: r }),

  alerts: [],
  addAlert: (a) => set((state) => ({
    alerts: [...state.alerts.filter(
      (x) => !(x.kind === a.kind && x.subject === a.subject)).slice(-9),
      { id: Math.random().toString(36), ...a }],
  })),
  dismissAlert: (id) => set((state) => ({
    alerts: state.alerts.filter((a) => a.id !== id),
  })),

  terminalOutput: "",
  // El historial se acotaba: `state.terminalOutput + text` crecía sin fin
  // (4,9 MB tras 4000 anexiones) y se recorría entero en cada repintado.
  appendTerminal: (text) => set((state) => ({
    terminalOutput: appendBounded(state.terminalOutput, text),
    awaitingApproval: state.awaitingApproval
      || text.includes("Esperando aprobación interactiva del usuario"),
  })),

  awaitingApproval: false,
  setAwaitingApproval: (awaitingApproval) => set({ awaitingApproval }),
  
  sysCommand: (cmd) => {
    set((state) => ({ terminalOutput: state.terminalOutput + `\nroot@system:~# ${cmd}` }));
  },

  projects: [],
  setProjects: (projects) => set({ projects }),

  metrics: { prov_a: "0/0", prov_b: "0/0", prov_c: "0/0", status: "offline" },
  setMetrics: (metrics) => set({ metrics }),

  telemetry: [],
  setTelemetry: (telemetry) => set({ telemetry }),

  fileTree: [],
  setFileTree: (fileTree) => set({ fileTree }),

  activeFilePath: null,
  activeFileContent: "",
  setActiveFile: (path, content) => set({ activeFilePath: path, activeFileContent: content }),

  naokoMessages: [],
  naokoStatus: "Inactiva",
  addNaokoMessage: (msg) => set((state) => ({ naokoMessages: [...state.naokoMessages, msg] })),
  setNaokoStatus: (status) => set({ naokoStatus: status }),

  ritsukoMessages: [],
  ritsukoStatus: "Inactiva",
  ritsukoInformes: [],
  addRitsukoMessage: (msg) => set((state) => ({ ritsukoMessages: [...state.ritsukoMessages, msg] })),
  setRitsukoStatus: (status) => set({ ritsukoStatus: status }),
  setRitsukoInformes: (v) => set({ ritsukoInformes: v })
}));
