import type { GeneratedOutputCompare } from "@careerpilot/shared";

export function VersionCompare({ compare }: { compare: GeneratedOutputCompare | null }) {
  if (!compare || !compare.previous) {
    return null;
  }

  return (
    <div className="border border-[color:var(--line)] p-4">
      <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
        Version compare
      </div>
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        <div>
          <div className="mono-ui text-[11px] uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
            Current {compare.current.version}
          </div>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-3 text-xs leading-6">
            {compare.current.content}
          </pre>
        </div>
        <div>
          <div className="mono-ui text-[11px] uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
            Previous {compare.previous.version}
          </div>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-3 text-xs leading-6">
            {compare.previous.content}
          </pre>
        </div>
      </div>
      <div className="mt-3 text-sm text-[color:var(--ink-soft)]">
        Changed fields: {((compare.diff.changed_fields ?? []) as string[]).join(", ") || "None"}
      </div>
    </div>
  );
}
