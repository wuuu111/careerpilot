import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProtectedOutlet } from "./router";
import { useAuthStore } from "@/app/auth-store";
import { AppShell } from "@/components/app-shell";

const user = {
  id: "user-1",
  name: "Ada",
  email: "ada@example.com",
  created_at: new Date().toISOString(),
};

describe("AppShell", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null, hydrated: true });
  });

  it("renders the top navigation for authenticated sessions", () => {
    useAuthStore.setState({
      token: "session",
      user,
      hydrated: true,
    });

    render(
      <MemoryRouter>
        <AppShell />
      </MemoryRouter>,
    );

    expect(screen.getByText("CareerPilot")).toBeInTheDocument();
    expect(screen.getByText("Trace")).toBeInTheDocument();
  });

  it("redirects unauthenticated visitors to login after hydration", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/login" element={<div>Sign in</div>} />
          <Route path="/" element={<ProtectedOutlet />}>
            <Route index element={<div>Private page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(screen.getByText("Sign in")).toBeInTheDocument());
  });

  it("restores the cookie-backed session before rendering protected routes", async () => {
    const restoreSession = vi.fn(async () => {
      useAuthStore.setState({ token: "session", user, hydrated: true });
    });

    useAuthStore.setState({ token: null, user: null, hydrated: false, restoreSession });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/login" element={<div>Sign in</div>} />
          <Route path="/" element={<ProtectedOutlet />}>
            <Route index element={<div>Private page</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(restoreSession).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("CareerPilot")).toBeInTheDocument();
    expect(screen.getByText("Private page")).toBeInTheDocument();
  });
});
