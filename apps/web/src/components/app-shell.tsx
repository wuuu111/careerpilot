import { Outlet } from "react-router-dom";

import { CommandBar } from "@/components/command-bar";

export function AppShell() {
  return (
    <div className="min-h-screen">
      <CommandBar />
      <main className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8">
        <section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="space-y-4">
            <p className="mono-ui text-xs uppercase tracking-[0.28em] text-[color:var(--ink-blue)]">
              resume-to-application workflow
            </p>
            <h1 className="editorial-serif text-5xl leading-none text-[color:var(--ink)] md:text-7xl">
              Move from raw materials to a traced application run.
            </h1>
          </div>
          <div className="paper-panel p-5">
            <p className="mono-ui text-xs uppercase tracking-[0.24em] text-[color:var(--ink-soft)]">
              Operating posture
            </p>
            <p className="mt-4 text-sm leading-7 text-[color:var(--ink-soft)]">
              Upload a resume, structure a JD, run the agent chain, and inspect each output
              and step record without leaving the same workspace.
            </p>
          </div>
        </section>
        <Outlet />
      </main>
    </div>
  );
}
