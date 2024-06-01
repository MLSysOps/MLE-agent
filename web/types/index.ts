export interface ProjectMessage {
  content: String;
  project: String;
  role: Role;
}

export type Role = "system" | "user";

enum DebugEnv {
    Local = "local",
    Cloud = "cloud"
}

export interface Resource {
    name: string;
    uri?: string;
    description?: string;
    choices?: string[];
}

export interface Function {
    name: string;
    description?: string;
}

export interface Task {
    name: string;
    kind: string;
    description?: string;
    resources?: Resource[];
    functions?: string[];
    debug?: number;
}

export interface Plan {
    current_task: number;
    dataset?: string;
    data_kind?: string;
    ml_task_type?: string;
    ml_model_arch?: string;
    tasks?: Task[];
}

export interface Project {
    name: string;
    path?: string;
    lang: string;
    llm: string;
    plan?: Plan;
    entry_file?: string;
    debug_env?: DebugEnv;
    description?: string;
    requirement?: string;
}
