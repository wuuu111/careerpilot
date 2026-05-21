import { create } from "zustand";

type WorkspaceState = {
  selectedApplicationId: string;
  activeRunId: string;
  setSelectedApplicationId: (applicationId: string) => void;
  setActiveRunId: (runId: string) => void;
  reset: () => void;
};

const STORAGE_KEY = "careerpilot-workspace";

function loadWorkspace() {
  if (typeof window === "undefined") {
    return { selectedApplicationId: "", activeRunId: "" };
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { selectedApplicationId: "", activeRunId: "" };
  }

  try {
    const parsed = JSON.parse(raw) as Partial<WorkspaceState>;
    return {
      selectedApplicationId: parsed.selectedApplicationId ?? "",
      activeRunId: parsed.activeRunId ?? "",
    };
  } catch {
    return { selectedApplicationId: "", activeRunId: "" };
  }
}

function persistWorkspace(state: Pick<WorkspaceState, "selectedApplicationId" | "activeRunId">) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function clearWorkspaceStorage() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
}

const initialState = loadWorkspace();

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  ...initialState,
  setSelectedApplicationId: (selectedApplicationId) =>
    set((current) => {
      const next = { ...current, selectedApplicationId };
      persistWorkspace(next);
      return next;
    }),
  setActiveRunId: (activeRunId) =>
    set((current) => {
      const next = { ...current, activeRunId };
      persistWorkspace(next);
      return next;
    }),
  reset: () => {
    clearWorkspaceStorage();
    set({ selectedApplicationId: "", activeRunId: "" });
  },
}));
