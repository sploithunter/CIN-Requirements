"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { handleOAuthCallback } from "@/lib/auth";
import { Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError(searchParams.get("error_description") || "Authentication failed");
      return;
    }

    if (!code) {
      setError("No authorization code received");
      return;
    }

    // Determine provider from state or URL
    const provider = state?.includes("microsoft") ? "microsoft" : "google";

    handleOAuthCallback(provider, code)
      .then(() => {
        router.push("/dashboard");
      })
      .catch((err) => {
        console.error("OAuth callback error:", err);
        setError(err.message || "Authentication failed");
      });
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="max-w-md w-full mx-4 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 mb-4">
            <AlertCircle className="w-8 h-8 text-destructive" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Authentication Failed</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button onClick={() => router.push("/login")}>
            Back to Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
        <p className="text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
