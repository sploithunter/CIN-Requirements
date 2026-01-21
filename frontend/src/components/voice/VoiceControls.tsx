"use client";

import { Mic, MicOff, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useVoice } from "@/lib/hooks/useVoice";
import { cn } from "@/lib/utils";

interface VoiceControlsProps {
  onTranscript?: (transcript: string) => void;
  className?: string;
}

export function VoiceControls({ onTranscript, className }: VoiceControlsProps) {
  const { isListening, isSupported, transcript, toggleListening, stopListening } =
    useVoice({
      onTranscript: (text, isFinal) => {
        if (isFinal && onTranscript) {
          onTranscript(text);
        }
      },
    });

  if (!isSupported) {
    return (
      <Button
        variant="outline"
        size="icon"
        disabled
        title="Speech recognition not supported"
        className={className}
      >
        <MicOff className="h-4 w-4 text-muted-foreground" />
      </Button>
    );
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Button
        variant={isListening ? "destructive" : "outline"}
        size="icon"
        onClick={toggleListening}
        title={isListening ? "Stop recording" : "Start recording"}
        className={cn({
          "animate-pulse": isListening,
        })}
      >
        {isListening ? (
          <Square className="h-4 w-4" />
        ) : (
          <Mic className="h-4 w-4" />
        )}
      </Button>

      {isListening && transcript && (
        <div className="flex-1 p-2 bg-muted rounded-md text-sm animate-pulse">
          {transcript}
        </div>
      )}
    </div>
  );
}
