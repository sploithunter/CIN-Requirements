"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageBubble } from "./MessageBubble";
import { useAI } from "@/lib/hooks/useAI";
import type { Message } from "@/types";

interface ChatPanelProps {
  sessionId: string;
  messages: Message[];
  onNewMessage: (message: Message) => void;
}

export function ChatPanel({
  sessionId,
  messages,
  onNewMessage,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendMessage, streaming, streamingContent, error } = useAI(sessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setIsLoading(true);

    // Optimistically add user message
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userMessage,
      message_type: "text",
      input_tokens: 0,
      output_tokens: 0,
      created_at: new Date().toISOString(),
    };
    onNewMessage(tempUserMessage);

    try {
      const response = await sendMessage(userMessage);
      if (response) {
        onNewMessage(response);
      }
    } catch (err) {
      console.error("Failed to send message:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          <h2 className="font-semibold">AI Assistant</h2>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Start a conversation to gather requirements</p>
            <p className="text-sm mt-2">
              Ask questions, describe your project, or request a questionnaire
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}

        {streaming && streamingContent && (
          <MessageBubble
            message={{
              id: "streaming",
              role: "assistant",
              content: streamingContent,
              message_type: "text",
              input_tokens: 0,
              output_tokens: 0,
              created_at: new Date().toISOString(),
            }}
            isStreaming
          />
        )}

        {error && (
          <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your requirements..."
            disabled={isLoading || streaming}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || streaming}
            size="icon"
          >
            {isLoading || streaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
