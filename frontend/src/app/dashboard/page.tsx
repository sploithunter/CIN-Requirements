"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/AuthProvider";
import { useSessions } from "@/lib/hooks/useSession";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Plus,
  FileText,
  Loader2,
  LogOut,
  Trash2,
  MoreVertical,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const { sessions, loading, createSession, deleteSession } = useSessions();
  const router = useRouter();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleCreateSession = async () => {
    if (!newSessionTitle.trim()) return;

    setIsCreating(true);
    try {
      const session = await createSession({ title: newSessionTitle.trim() });
      setIsCreateDialogOpen(false);
      setNewSessionTitle("");
      router.push(`/sessions/${session.id}`);
    } catch (err) {
      console.error("Failed to create session:", err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      setDeleteConfirmId(null);
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft":
        return "bg-gray-100 text-gray-700";
      case "in_progress":
        return "bg-blue-100 text-blue-700";
      case "review":
        return "bg-yellow-100 text-yellow-700";
      case "completed":
        return "bg-green-100 text-green-700";
      case "archived":
        return "bg-slate-100 text-slate-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-semibold">Conversational Requirements</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {user?.avatar_url && (
                <img
                  src={user.avatar_url}
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-sm font-medium">{user?.name}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={logout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Your Sessions</h2>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            New Session
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
            <h3 className="text-lg font-medium mb-2">No sessions yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first session to start gathering requirements
            </p>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Session
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="group relative border rounded-lg p-4 hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => router.push(`/sessions/${session.id}`)}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium line-clamp-1">{session.title}</h3>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteConfirmId(session.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-muted rounded transition-opacity"
                  >
                    <Trash2 className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                  </button>
                </div>

                <div className="flex items-center gap-2 text-sm">
                  <span
                    className={cn(
                      "px-2 py-0.5 rounded-full text-xs font-medium",
                      getStatusColor(session.status)
                    )}
                  >
                    {session.status.replace("_", " ")}
                  </span>
                  <span className="text-muted-foreground">
                    {formatRelativeTime(session.updated_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Session Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Session</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Input
              placeholder="Session title..."
              value={newSessionTitle}
              onChange={(e) => setNewSessionTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCreateSession();
                }
              }}
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateSession}
              disabled={!newSessionTitle.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirmId}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Session</DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground">
            Are you sure you want to delete this session? This action cannot be
            undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && handleDeleteSession(deleteConfirmId)}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
