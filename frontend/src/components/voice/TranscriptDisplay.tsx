"use client";

import { Mic, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface TranscriptDisplayProps {
  transcript: string;
  isListening?: boolean;
  isFinal?: boolean;
  className?: string;
}

export function TranscriptDisplay({
  transcript,
  isListening = false,
  isFinal = false,
  className,
}: TranscriptDisplayProps) {
  if (!transcript) {
    return null;
  }

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg bg-muted/50 border",
        {
          "border-primary/50": isListening,
          "border-green-500/50": isFinal,
        },
        className
      )}
    >
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          {
            "bg-primary text-primary-foreground animate-pulse": isListening,
            "bg-green-500 text-white": isFinal,
            "bg-muted": !isListening && !isFinal,
          }
        )}
      >
        {isListening ? (
          <Mic className="w-4 h-4" />
        ) : (
          <Volume2 className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1">
        <div className="text-xs font-medium text-muted-foreground mb-1">
          {isListening ? "Listening..." : isFinal ? "Transcribed" : "Transcript"}
        </div>
        <p className="text-sm">{transcript}</p>
      </div>
    </div>
  );
}
