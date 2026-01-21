"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { Session, SessionListItem, Message } from "@/types";

export function useSession(sessionId: string | null) {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSession = useCallback(async () => {
    if (!sessionId) {
      setSession(null);
      setMessages([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const [sessionData, messagesData] = await Promise.all([
        api.getSession(sessionId),
        api.getMessages(sessionId),
      ]);

      setSession(sessionData);
      setMessages(messagesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  const updateSession = useCallback(
    async (data: Partial<Session>) => {
      if (!sessionId) return;

      try {
        const updated = await api.updateSession(sessionId, data);
        setSession(updated);
        return updated;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update session");
        throw err;
      }
    },
    [sessionId]
  );

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const refreshMessages = useCallback(async () => {
    if (!sessionId) return;

    try {
      const messagesData = await api.getMessages(sessionId);
      setMessages(messagesData);
    } catch (err) {
      console.error("Failed to refresh messages:", err);
    }
  }, [sessionId]);

  return {
    session,
    messages,
    loading,
    error,
    updateSession,
    addMessage,
    refreshMessages,
    refresh: fetchSession,
  };
}

export function useSessions() {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listSessions();
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const createSession = useCallback(
    async (data: { title?: string; description?: string }) => {
      try {
        const session = await api.createSession(data);
        setSessions((prev) => [
          {
            id: session.id,
            title: session.title,
            status: session.status,
            updated_at: session.updated_at,
          },
          ...prev,
        ]);
        return session;
      } catch (err) {
        throw err;
      }
    },
    []
  );

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await api.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err) {
      throw err;
    }
  }, []);

  return {
    sessions,
    loading,
    error,
    createSession,
    deleteSession,
    refresh: fetchSessions,
  };
}
