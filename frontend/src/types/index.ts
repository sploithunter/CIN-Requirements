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

// ============================================================================
// Projects
// ============================================================================

export type ProjectRole = "owner" | "gatherer" | "client" | "viewer";

export interface Project {
  id: string;
  name: string;
  description?: string;
  client_name?: string;
  target_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectRole;
  invited_at: string;
  accepted_at?: string;
  user_name?: string;
  user_email?: string;
}

export interface ProjectWithMembers extends Project {
  members: ProjectMember[];
}

export interface ProjectListItem {
  id: string;
  name: string;
  client_name?: string;
  updated_at: string;
}

// ============================================================================
// Documents
// ============================================================================

export type DocumentType =
  | "requirements"
  | "functional"
  | "specification"
  | "rom"
  | "custom";

export type DocumentStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "superseded";

export interface Document {
  id: string;
  project_id: string;
  document_type: DocumentType;
  title: string;
  description?: string;
  current_version: number;
  status: DocumentStatus;
  derived_from_id?: string;
  liveblocks_room_id?: string;
  created_by_id: string;
  last_edited_by_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithContent extends Document {
  content?: Record<string, unknown>;
}

export interface DocumentListItem {
  id: string;
  title: string;
  document_type: DocumentType;
  status: DocumentStatus;
  current_version: number;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: number;
  change_summary?: string;
  created_by_id: string;
  created_at: string;
}

export interface DocumentVersionWithContent extends DocumentVersion {
  content: Record<string, unknown>;
  diff_from_previous?: Record<string, unknown>;
}

// ============================================================================
// Sections
// ============================================================================

export type SectionStatus =
  | "empty"
  | "draft"
  | "needs_review"
  | "approved"
  | "disputed";

export type BindingType =
  | "discussion"
  | "editing"
  | "reference"
  | "question"
  | "approval";

export interface Section {
  id: string;
  document_id: string;
  section_number: string;
  title: string;
  parent_id?: string;
  order: number;
  status: SectionStatus;
  prosemirror_node_id?: string;
  content_preview?: string;
  ai_generated: boolean;
  ai_confidence?: number;
  open_questions?: string[];
  created_at: string;
  updated_at: string;
}

export interface SectionTree extends Section {
  children: SectionTree[];
}

export interface SectionBinding {
  id: string;
  section_id: string;
  message_id?: string;
  binding_type: BindingType;
  created_by_id?: string;
  is_ai_generated: boolean;
  is_active: boolean;
  note?: string;
  created_at: string;
  deactivated_at?: string;
}

export interface SectionWithBindings extends Section {
  bindings: SectionBinding[];
}
