export function SourceCitations({
  citations,
}: {
  citations: Array<Record<string, unknown>>;
}) {
  if (!citations.length) {
    return null;
  }

  return (
    <div className="border border-[color:var(--line)] p-4">
      <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
        Retrieval citations
      </div>
      <div className="mt-3 space-y-3">
        {citations.map((citation, index) => (
          <div key={`${citation.source_type}-${citation.source_subtype}-${index}`} className="border border-[color:var(--line)] p-3">
            <div className="mono-ui text-[11px] uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
              {String(citation.source_type ?? "unknown")} / {String(citation.source_subtype ?? "unknown")} / {String(citation.version ?? "v1")}
            </div>
            <p className="mt-2 text-sm leading-6 text-[color:var(--ink-soft)]">
              {String(citation.excerpt ?? "No excerpt available.")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
