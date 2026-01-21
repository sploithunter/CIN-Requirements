"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import type { User } from "@/types";
import {
  initializeAuth,
  logout as logoutFn,
  loginWithGoogle,
  loginWithMicrosoft,
} from "@/lib/auth";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (provider: "google" | "microsoft") => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function init() {
      try {
        const user = await initializeAuth();
        setUser(user);
      } catch (error) {
        console.error("Auth initialization failed:", error);
      } finally {
        setLoading(false);
      }
    }

    init();
  }, []);

  const login = useCallback(async (provider: "google" | "microsoft") => {
    if (provider === "google") {
      await loginWithGoogle();
    } else {
      await loginWithMicrosoft();
    }
  }, []);

  const logout = useCallback(() => {
    logoutFn();
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
