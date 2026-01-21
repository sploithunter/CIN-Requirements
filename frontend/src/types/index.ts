export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  title: string;
  description?: string;
  status: SessionStatus;
  owner_id: string;
  liveblocks_room_id?: string;
  system_prompt?: string;
  context_summary?: string;
  document_content?: Record<string, unknown>;
  token_usage: number;
  created_at: string;
  updated_at: string;
}

export type SessionStatus =
  | "draft"
  | "in_progress"
  | "review"
  | "completed"
  | "archived";

export interface SessionListItem {
  id: string;
  title: string;
  status: SessionStatus;
  updated_at: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  message_type: MessageType;
  extra_data?: Record<string, unknown>;
  input_tokens: number;
  output_tokens: number;
  created_at: string;
}

export type MessageRole = "user" | "assistant" | "system";
export type MessageType = "text" | "questionnaire" | "requirement" | "voice_transcript";

export interface ChatRequest {
  message: string;
  include_history?: boolean;
  max_history_messages?: number;
}

export interface QuestionnaireQuestion {
  id: string;
  question: string;
  type: "text" | "select" | "multiselect" | "boolean";
  options?: string[];
  required: boolean;
}

export interface Questionnaire {
  id: string;
  questions: QuestionnaireQuestion[];
  topic: string;
  created_at: string;
}

export interface RequirementSuggestion {
  id: string;
  text: string;
  category: string;
  priority?: string;
  rationale?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}
