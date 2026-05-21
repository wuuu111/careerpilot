import { Link, NavLink } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { useWorkspaceStore } from "@/app/workspace-store";
import { api } from "@/lib/api";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/resumes", label: "Resumes" },
  { to: "/job-analysis", label: "Job Analysis" },
  { to: "/matching", label: "Matching" },
  { to: "/generated", label: "Generated" },
  { to: "/trace", label: "Trace" },
];

export function CommandBar() {
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);
  const selectedApplicationId = useWorkspaceStore((state) => state.selectedApplicationId);
  const activeRunId = useWorkspaceStore((state) => state.activeRunId);

  async function handleLogout() {
    try {
      await api.logout();
    } finally {
      clearSession();
    }
  }

  return (
    <header className="border-b border-[color:var(--line)] bg-[color:var(--paper)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <Link to="/" className="editorial-serif text-3xl tracking-tight text-[color:var(--ink)]">
            CareerPilot
          </Link>
          <div className="mono-ui text-xs uppercase tracking-[0.3em] text-[color:var(--ink-blue)]">
            multi-agent application studio
          </div>
        </div>
        <nav className="flex flex-wrap gap-2 text-sm">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "mono-ui border px-3 py-2 uppercase tracking-[0.2em]",
                  isActive
                    ? "border-[color:var(--ink)] bg-[color:var(--paper-deep)]"
                    : "border-[color:var(--line)] hover:border-[color:var(--ink)]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <div className="mono-ui text-[11px] uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
            {selectedApplicationId ? `app ${selectedApplicationId.slice(0, 8)}` : "no app focus"}
            {activeRunId ? ` / run ${activeRunId.slice(0, 8)}` : ""}
          </div>
          <div className="mono-ui text-xs text-[color:var(--ink-soft)]">
            {user ? user.email : "guest"}
          </div>
          <button
            className="mono-ui border border-[color:var(--ink)] px-3 py-2 text-xs uppercase tracking-[0.2em]"
            onClick={() => void handleLogout()}
            type="button"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
