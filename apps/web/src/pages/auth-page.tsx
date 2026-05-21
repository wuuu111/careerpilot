import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { api, ApiError } from "@/lib/api";
import { Button, ErrorNotice, Input, Panel } from "@/components/ui";

type Mode = "login" | "register";

export function AuthPage({ mode }: { mode: Mode }) {
  const navigate = useNavigate();
  const setSession = useAuthStore((state) => state.setSession);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register({ name, email, password });
      }
      await api.login({ email, password });
      const user = await api.me();
      setSession(null, user);
      navigate("/");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unexpected request failure.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-20 max-w-xl">
      <Panel title={mode === "login" ? "Sign in" : "Create account"} eyebrow="auth">
        <form className="space-y-4" onSubmit={handleSubmit}>
          {mode === "register" ? (
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.18em]">Name</span>
              <Input value={name} onChange={(event) => setName(event.target.value)} />
            </label>
          ) : null}
          <label className="block space-y-2">
            <span className="mono-ui text-xs uppercase tracking-[0.18em]">Email</span>
            <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="block space-y-2">
            <span className="mono-ui text-xs uppercase tracking-[0.18em]">Password</span>
            <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <ErrorNotice message={error} />
          <Button disabled={busy} type="submit">
            {busy ? "Working" : mode === "login" ? "Login" : "Register"}
          </Button>
        </form>
      </Panel>
    </div>
  );
}
