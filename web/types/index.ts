export enum OpenAIModel {
  DAVINCI_TURBO = "gpt-3.5-turbo"
}

export interface Message {
  role: Role;
  content: string;
}

export interface ChatMessage {
  message: String;
  project: String;
}

export type Role = "assistant" | "user";
