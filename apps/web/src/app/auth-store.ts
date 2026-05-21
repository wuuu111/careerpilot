import { create } from "zustand";

import { useWorkspaceStore } from "@/app/workspace-store";
import { api, type User } from "@/lib/api";

type AuthState = {
  token: string | null;
  user: User | null;
  hydrated: boolean;
  setSession: (token: string | null, user: User | null) => void;
  restoreSession: () => Promise<void>;
  clearSession: () => void;
};

const SESSION_KEY = "careerpilot-session";
const COOKIE_SESSION_TOKEN = "cookie-session";

function clearLegacyToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(SESSION_KEY);
  }
}

let restorePromise: Promise<void> | null = null;

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  hydrated: false,
  setSession: (_token, user) => {
    clearLegacyToken();
    set({ token: user ? COOKIE_SESSION_TOKEN : null, user, hydrated: true });
  },
  restoreSession: async () => {
    if (get().hydrated) {
      return;
    }
    if (restorePromise) {
      return restorePromise;
    }

    clearLegacyToken();
    restorePromise = (async () => {
      try {
        const user = await api.me();
        set({ token: COOKIE_SESSION_TOKEN, user, hydrated: true });
      } catch {
        useWorkspaceStore.getState().reset();
        set({ token: null, user: null, hydrated: true });
      } finally {
        restorePromise = null;
      }
    })();

    return restorePromise;
  },
  clearSession: () => {
    clearLegacyToken();
    useWorkspaceStore.getState().reset();
    set({ token: null, user: null, hydrated: true });
  },
}));
