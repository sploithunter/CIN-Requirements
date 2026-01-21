"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { Message, Questionnaire, RequirementSuggestion } from "@/types";

export function useAI(sessionId: string | null) {
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (
      message: string,
      onMessage?: (message: Message) => void
    ): Promise<Message | null> => {
      if (!sessionId) return null;

      try {
        setError(null);
        const response = await api.sendMessage(sessionId, { message });
        onMessage?.(response);
        return response;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
        return null;
      }
    },
    [sessionId]
  );

  const sendMessageStream = useCallback(
    async (
      message: string,
      onChunk?: (content: string) => void,
      onComplete?: () => void
    ): Promise<void> => {
      if (!sessionId) return;

      try {
        setError(null);
        setStreaming(true);
        setStreamingContent("");

        await api.streamMessage(sessionId, { message }, (chunk) => {
          setStreamingContent((prev) => prev + chunk);
          onChunk?.(chunk);
        });

        onComplete?.();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
      } finally {
        setStreaming(false);
        setStreamingContent("");
      }
    },
    [sessionId]
  );

  const generateQuestionnaire = useCallback(
    async (topic: string, context?: string): Promise<Questionnaire | null> => {
      if (!sessionId) return null;

      try {
        setError(null);
        return await api.generateQuestionnaire(sessionId, topic, context);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to generate questionnaire"
        );
        return null;
      }
    },
    [sessionId]
  );

  const submitAnswers = useCallback(
    async (
      questionnaireId: string,
      answers: Record<string, string | string[] | boolean>
    ): Promise<boolean> => {
      if (!sessionId) return false;

      try {
        setError(null);
        await api.submitQuestionnaireAnswers(sessionId, questionnaireId, answers);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to submit answers");
        return false;
      }
    },
    [sessionId]
  );

  const suggestRequirements = useCallback(async (): Promise<{
    suggestions: RequirementSuggestion[];
    context_used: string;
  } | null> => {
    if (!sessionId) return null;

    try {
      setError(null);
      return await api.suggestRequirements(sessionId);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to suggest requirements"
      );
      return null;
    }
  }, [sessionId]);

  return {
    sendMessage,
    sendMessageStream,
    generateQuestionnaire,
    submitAnswers,
    suggestRequirements,
    streaming,
    streamingContent,
    error,
    clearError: () => setError(null),
  };
}
