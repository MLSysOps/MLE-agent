export interface ProjectMessage {
  content: String;
  project: String;
  role: Role;
}

export type Role = "assistant" | "user";
