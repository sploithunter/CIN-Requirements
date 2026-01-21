"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "@/lib/hooks/useSession";
import { useAI } from "@/lib/hooks/useAI";
import { useAuth } from "@/providers/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatPanel } from "@/components/ai/ChatPanel";
import { Editor } from "@/components/editor/Editor";
import { VoiceControls } from "@/components/voice/VoiceControls";
import { api } from "@/lib/api";
import {
  ArrowLeft,
  Download,
  FileText,
  Loader2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Save,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Message } from "@/types";

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const { session, messages, loading, error, updateSession, addMessage } =
    useSession(sessionId);
  const { suggestRequirements } = useAI(sessionId);
  const { user } = useAuth();

  const [showChat, setShowChat] = useState(true);
  const [editorContent, setEditorContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const handleSave = async () => {
    if (!session) return;

    setIsSaving(true);
    try {
      await updateSession({ document_content: { html: editorContent } });
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async (format: "docx" | "markdown") => {
    if (!session) return;

    setIsExporting(true);
    try {
      const blob = await api.generateRequirementsDocument(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${session.title.replace(/\s+/g, "_")}_requirements.${format === "docx" ? "docx" : "md"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export:", err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleSuggestRequirements = async () => {
    setIsSuggesting(true);
    try {
      const result = await suggestRequirements();
      if (result && result.suggestions.length > 0) {
        // Format suggestions as text for the editor
        const suggestionsText = result.suggestions
          .map(
            (s, i) =>
              `<h3>REQ-${String(i + 1).padStart(3, "0")}: ${s.text}</h3>
<p><strong>Category:</strong> ${s.category}</p>
${s.priority ? `<p><strong>Priority:</strong> ${s.priority}</p>` : ""}
${s.rationale ? `<p><strong>Rationale:</strong> ${s.rationale}</p>` : ""}
<hr/>`
          )
          .join("\n");

        setEditorContent((prev) => prev + suggestionsText);
      }
    } catch (err) {
      console.error("Failed to suggest requirements:", err);
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    // Add transcript to editor
    setEditorContent((prev) => prev + `<p>${transcript}</p>`);
  };

  const handleNewMessage = (message: Message) => {
    addMessage(message);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error || "Session not found"}</p>
          <Button onClick={() => router.push("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>

            <div>
              <Input
                value={session.title}
                onChange={(e) => updateSession({ title: e.target.value })}
                className="text-lg font-semibold border-none p-0 h-auto focus-visible:ring-0"
              />
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-xs",
                    session.status === "draft" && "bg-gray-100",
                    session.status === "in_progress" && "bg-blue-100 text-blue-700",
                    session.status === "completed" && "bg-green-100 text-green-700"
                  )}
                >
                  {session.status.replace("_", " ")}
                </span>
                <span>{session.token_usage.toLocaleString()} tokens used</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <VoiceControls onTranscript={handleVoiceTranscript} />

            <Button
              variant="outline"
              size="sm"
              onClick={handleSuggestRequirements}
              disabled={isSuggesting}
            >
              {isSuggesting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4 mr-2" />
              )}
              Suggest
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Save
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("docx")}
              disabled={isExporting}
            >
              {isExporting ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Export
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowChat(!showChat)}
            >
              {showChat ? (
                <PanelLeftClose className="w-4 h-4" />
              ) : (
                <PanelLeftOpen className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel */}
        {showChat && (
          <div className="w-96 border-r flex-shrink-0">
            <ChatPanel
              sessionId={sessionId}
              messages={messages}
              onNewMessage={handleNewMessage}
            />
          </div>
        )}

        {/* Editor */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-4xl mx-auto">
            <Editor
              content={editorContent}
              onChange={setEditorContent}
              placeholder="Start documenting requirements here..."
            />
          </div>
        </div>
      </div>
    </div>
  );
}
