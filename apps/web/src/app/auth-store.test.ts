import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({
  api: {
    me: vi.fn(),
  },
}));

import { useAuthStore } from "@/app/auth-store";
import { api } from "@/lib/api";

const user = {
  id: "user-1",
  name: "Ada",
  email: "ada@example.com",
  created_at: new Date().toISOString(),
};

describe("auth-store", () => {
  beforeEach(() => {
    window.localStorage.clear();
    useAuthStore.setState({ token: null, user: null, hydrated: false });
    vi.clearAllMocks();
  });

  it("does not persist access tokens into localStorage", () => {
    useAuthStore.getState().setSession("bearer-token", user);

    expect(window.localStorage.getItem("careerpilot-session")).toBeNull();
    expect(useAuthStore.getState().token).toBeTruthy();
    expect(useAuthStore.getState().token).not.toBe("bearer-token");
  });

  it("restores the authenticated user from the cookie-backed session", async () => {
    vi.mocked(api.me).mockResolvedValue(user);

    await useAuthStore.getState().restoreSession();

    expect(api.me).toHaveBeenCalledWith();
    expect(useAuthStore.getState()).toMatchObject({
      token: expect.any(String),
      user,
      hydrated: true,
    });
  });
});
