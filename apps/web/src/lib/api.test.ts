import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError } from "@/lib/api";

describe("ApiError", () => {
  it("preserves the standard error envelope fields", () => {
    const error = new ApiError({
      error_code: "AGENT_STEP_FAILED",
      message: "The workflow failed during ResumeRewriteAgent.",
      details: { agent_name: "ResumeRewriteAgent" },
    });

    expect(error.errorCode).toBe("AGENT_STEP_FAILED");
    expect(error.message).toContain("ResumeRewriteAgent");
  });
});

describe("api session requests", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    document.cookie = "careerpilot_csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
  });

  it("sends cookie-backed auth requests with credentials and no bearer header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "user-1", email: "ada@example.com" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    vi.stubGlobal("fetch", fetchMock);

    await api.me("bearer-token");

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(options.headers);

    expect(options.credentials).toBe("include");
    expect(headers.get("Authorization")).toBeNull();
  });

  it("supports logout endpoints that return no response body", async () => {
    document.cookie = "careerpilot_csrf_token=csrf-token-123";
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));

    vi.stubGlobal("fetch", fetchMock);

    await expect(api.logout()).resolves.toBeUndefined();
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
    const headers = new Headers(options.headers);

    expect(headers.get("X-CSRF-Token")).toBe("csrf-token-123");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/auth/logout"),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
  });
});
