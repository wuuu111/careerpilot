import type { PropsWithChildren, ReactNode } from "react";

const fieldClassName =
  "w-full border border-[color:var(--ink)] bg-transparent px-3 py-3 text-sm outline-none";
const buttonClassName =
  "mono-ui border border-[color:var(--ink)] px-4 py-3 text-xs uppercase tracking-[0.22em] disabled:opacity-50";

export function Panel({
  title,
  eyebrow,
  actions,
  children,
}: PropsWithChildren<{ title: string; eyebrow?: string; actions?: ReactNode }>) {
  return (
    <section className="paper-panel p-5">
      <div className="flex flex-col gap-3 border-b border-[color:var(--line)] pb-4 md:flex-row md:items-end md:justify-between">
        <div>
          {eyebrow ? (
            <p className="mono-ui text-xs uppercase tracking-[0.22em] text-[color:var(--ink-blue)]">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="editorial-serif mt-2 text-3xl">{title}</h2>
        </div>
        {actions}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="border border-[color:var(--line)] p-4">
      <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-soft)]">
        {label}
      </div>
      <div className="editorial-serif mt-3 text-4xl">{value}</div>
    </div>
  );
}

export function ErrorNotice({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }

  return (
    <div className="border border-[color:var(--danger)] bg-[color:var(--paper)] px-4 py-3 text-sm text-[color:var(--danger)]">
      {message}
    </div>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={[fieldClassName, props.className].filter(Boolean).join(" ")} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={["min-h-40", fieldClassName, props.className].filter(Boolean).join(" ")}
    />
  );
}

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={[buttonClassName, props.className].filter(Boolean).join(" ")} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={[fieldClassName, props.className].filter(Boolean).join(" ")} />;
}

export function StatusPill({
  children,
  tone = "neutral",
}: PropsWithChildren<{ tone?: "neutral" | "success" | "warning" | "danger" }>) {
  const toneClassName = {
    neutral: "border-[color:var(--line)] text-[color:var(--ink-blue)]",
    success: "border-[color:var(--ink)] text-[color:var(--ink)]",
    warning: "border-[color:var(--ink-blue)] text-[color:var(--ink-blue)]",
    danger: "border-[color:var(--danger)] text-[color:var(--danger)]",
  }[tone];

  return (
    <div
      className={[
        "mono-ui inline-flex items-center border px-3 py-2 text-[11px] uppercase tracking-[0.18em]",
        toneClassName,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="border border-dashed border-[color:var(--line)] px-5 py-8">
      <div className="editorial-serif text-2xl">{title}</div>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-[color:var(--ink-soft)]">{body}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
