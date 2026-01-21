import { api } from "./api";
import type { User, TokenResponse } from "@/types";

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const USER_KEY = "user";

export function getStoredTokens(): {
  accessToken: string | null;
  refreshToken: string | null;
} {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null };
  }

  return {
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }

  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;

  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

export function storeAuthData(data: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  api.setAccessToken(data.access_token);
}

export function clearAuthData(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  api.setAccessToken(null);
}

export async function initializeAuth(): Promise<User | null> {
  const { accessToken, refreshToken } = getStoredTokens();

  if (!accessToken) {
    return null;
  }

  api.setAccessToken(accessToken);

  try {
    const user = await api.getCurrentUser();
    return user;
  } catch {
    // Token might be expired, try refresh
    if (refreshToken) {
      try {
        const newTokens = await api.refreshToken(refreshToken);
        storeAuthData(newTokens);
        return newTokens.user;
      } catch {
        clearAuthData();
        return null;
      }
    }

    clearAuthData();
    return null;
  }
}

export async function loginWithGoogle(): Promise<void> {
  const { authorization_url } = await api.getGoogleAuthUrl();
  window.location.href = authorization_url;
}

export async function loginWithMicrosoft(): Promise<void> {
  const { authorization_url } = await api.getMicrosoftAuthUrl();
  window.location.href = authorization_url;
}

export async function handleOAuthCallback(
  provider: "google" | "microsoft",
  code: string
): Promise<User> {
  const tokenResponse =
    provider === "google"
      ? await api.googleCallback(code)
      : await api.microsoftCallback(code);

  storeAuthData(tokenResponse);
  return tokenResponse.user;
}

export function logout(): void {
  clearAuthData();
  window.location.href = "/login";
}
