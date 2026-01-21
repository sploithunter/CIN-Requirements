"use client";

import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex gap-3", {
        "flex-row-reverse": isUser,
      })}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          {
            "bg-primary text-primary-foreground": isUser,
            "bg-muted": !isUser,
          }
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn("max-w-[80%] rounded-lg px-4 py-2", {
          "bg-primary text-primary-foreground": isUser,
          "bg-muted": !isUser,
        })}
      >
        <div className="whitespace-pre-wrap break-words">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>

        {/* Extra data for questionnaires */}
        {message.message_type === "questionnaire" && message.extra_data && (
          <div className="mt-2 pt-2 border-t border-current/20 text-sm opacity-80">
            Questionnaire: {(message.extra_data as { topic?: string }).topic}
          </div>
        )}

        {/* Token usage (only for assistant messages) */}
        {!isUser && message.output_tokens > 0 && (
          <div className="mt-1 text-xs opacity-50">
            {message.input_tokens + message.output_tokens} tokens
          </div>
        )}
      </div>
    </div>
  );
}
