import type {
  User,
  Session,
  SessionListItem,
  Message,
  ChatRequest,
  Questionnaire,
  RequirementSuggestion,
  TokenResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

class ApiClient {
  private accessToken: string | null = null;

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.accessToken) {
      (headers as Record<string, string>)["Authorization"] =
        `Bearer ${this.accessToken}`;
    }

    const response = await fetch(`${API_BASE}/api/v1${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Auth
  async getGoogleAuthUrl(): Promise<{ authorization_url: string }> {
    return this.request("/auth/google/authorize");
  }

  async googleCallback(code: string): Promise<TokenResponse> {
    return this.request(`/auth/google/callback?code=${encodeURIComponent(code)}`, {
      method: "POST",
    });
  }

  async getMicrosoftAuthUrl(): Promise<{ authorization_url: string }> {
    return this.request("/auth/microsoft/authorize");
  }

  async microsoftCallback(code: string): Promise<TokenResponse> {
    return this.request(`/auth/microsoft/callback?code=${encodeURIComponent(code)}`, {
      method: "POST",
    });
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.request(`/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, {
      method: "POST",
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request("/auth/me");
  }

  // Sessions
  async createSession(data: { title?: string; description?: string }): Promise<Session> {
    return this.request("/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listSessions(skip = 0, limit = 50): Promise<SessionListItem[]> {
    return this.request(`/sessions?skip=${skip}&limit=${limit}`);
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.request(`/sessions/${sessionId}`);
  }

  async updateSession(
    sessionId: string,
    data: Partial<Session>
  ): Promise<Session> {
    return this.request(`/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteSession(sessionId: string): Promise<void> {
    return this.request(`/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  async getLiveblocksToken(sessionId: string): Promise<{ token: string }> {
    return this.request(`/sessions/${sessionId}/liveblocks-token`, {
      method: "POST",
    });
  }

  // AI Chat
  async sendMessage(sessionId: string, request: ChatRequest): Promise<Message> {
    return this.request(`/ai/${sessionId}/chat`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async streamMessage(
    sessionId: string,
    request: ChatRequest,
    onChunk: (content: string) => void
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/api/v1/ai/${sessionId}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data !== "[DONE]") {
            onChunk(data);
          }
        }
      }
    }
  }

  async getMessages(sessionId: string, skip = 0, limit = 100): Promise<Message[]> {
    return this.request(`/ai/${sessionId}/messages?skip=${skip}&limit=${limit}`);
  }

  async generateQuestionnaire(
    sessionId: string,
    topic: string,
    context?: string
  ): Promise<Questionnaire> {
    return this.request(`/ai/${sessionId}/questionnaire`, {
      method: "POST",
      body: JSON.stringify({ topic, context }),
    });
  }

  async submitQuestionnaireAnswers(
    sessionId: string,
    questionnaireId: string,
    answers: Record<string, string | string[] | boolean>
  ): Promise<{ status: string; message_id: string }> {
    return this.request(`/ai/${sessionId}/questionnaire/answer`, {
      method: "POST",
      body: JSON.stringify({ questionnaire_id: questionnaireId, answers }),
    });
  }

  async suggestRequirements(
    sessionId: string
  ): Promise<{ suggestions: RequirementSuggestion[]; context_used: string }> {
    return this.request(`/ai/${sessionId}/suggest-requirements`, {
      method: "POST",
    });
  }

  // Documents
  async generateRequirementsDocument(
    sessionId: string,
    format: "docx" | "markdown" = "docx"
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE}/api/v1/documents/${sessionId}/generate/requirements?format=${format}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.accessToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Document generation failed: ${response.status}`);
    }

    return response.blob();
  }

  async getSessionSummary(sessionId: string): Promise<{ summary: string }> {
    return this.request(`/documents/${sessionId}/generate/summary`, {
      method: "POST",
    });
  }

  async exportSession(
    sessionId: string,
    includeMessages = true,
    includeMedia = false
  ): Promise<Record<string, unknown>> {
    return this.request(
      `/documents/${sessionId}/export?include_messages=${includeMessages}&include_media=${includeMedia}`,
      { method: "POST" }
    );
  }

  // Media
  async uploadFile(sessionId: string, file: File): Promise<{
    id: string;
    filename: string;
    content_type: string;
    size_bytes: number;
    url: string;
  }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE}/api/v1/media/${sessionId}/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    return response.json();
  }

  async listFiles(sessionId: string): Promise<
    Array<{
      id: string;
      filename: string;
      content_type: string;
      media_type: string;
      size_bytes: number;
      url: string;
      created_at: string;
    }>
  > {
    return this.request(`/media/${sessionId}/files`);
  }

  async deleteFile(sessionId: string, mediaId: string): Promise<void> {
    return this.request(`/media/${sessionId}/files/${mediaId}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiClient();
