import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { useWorkspaceStore } from "@/app/workspace-store";
import { api, AgentRun, ApplicationRecord, MatchingReport } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Panel, Stat, StatusPill } from "@/components/ui";

export function MatchingPage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const selectedApplicationId = useWorkspaceStore((state) => state.selectedApplicationId);
  const setSelectedApplicationId = useWorkspaceStore((state) => state.setSelectedApplicationId);
  const activeRunId = useWorkspaceStore((state) => state.activeRunId);
  const setActiveRunId = useWorkspaceStore((state) => state.setActiveRunId);

  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [report, setReport] = useState<MatchingReport | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listApplications(token)
      .then((items) => {
        setApplications(items);
        if (!selectedApplicationId && items[0]) {
          setSelectedApplicationId(items[0].id);
        }
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Unable to load applications.");
      });
  }, [selectedApplicationId, setSelectedApplicationId, token]);

  useEffect(() => {
    if (!selectedApplicationId) {
      setReport(null);
      return;
    }
    void loadReport(selectedApplicationId);
  }, [selectedApplicationId]);

  useEffect(() => {
    if (!activeRunId) {
      setRun(null);
      return;
    }

    let cancelled = false;

    async function refreshRun() {
      try {
        const current = await api.getRun(token, activeRunId);
        if (cancelled) {
          return;
        }
        setRun(current);
        if (current.status === "success" && selectedApplicationId) {
          await loadReport(selectedApplicationId);
        }
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Run status unavailable.");
        }
      }
    }

    void refreshRun();
    const interval = window.setInterval(() => {
      void refreshRun();
    }, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [activeRunId, selectedApplicationId, token]);

  async function loadReport(applicationId: string) {
    try {
      setLoading(true);
      setError(null);
      setReport(await api.getMatchingReport(token, applicationId));
    } catch (caught) {
      setReport(null);
      setError(caught instanceof Error ? caught.message : "Matching report missing.");
    } finally {
      setLoading(false);
    }
  }

  async function runWorkflow(applicationId: string) {
    try {
      setError(null);
      setSelectedApplicationId(applicationId);
      const response = await api.createRun(token, applicationId);
      setActiveRunId(response.run_id);
      setRun(await api.getRun(token, response.run_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Workflow failed to start.");
    }
  }

  const selectedApplication =
    applications.find((item) => item.id === selectedApplicationId) ?? applications[0] ?? null;

  return (
    <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
      <Panel title="Applications" eyebrow="matching sources">
        {applications.length ? (
          <div className="space-y-3">
            {applications.map((item) => (
              <button
                key={item.id}
                className={[
                  "block w-full border p-4 text-left",
                  item.id === selectedApplication?.id
                    ? "border-[color:var(--ink)] bg-[color:var(--paper-deep)]"
                    : "border-[color:var(--line)]",
                ].join(" ")}
                onClick={() => setSelectedApplicationId(item.id)}
                type="button"
              >
                <div className="flex flex-col gap-3">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div className="editorial-serif text-2xl">{item.company_name}</div>
                      <div className="mt-1 text-sm text-[color:var(--ink-soft)]">
                        {item.job_title}
                      </div>
                    </div>
                    <StatusPill
                      tone={
                        item.status === "completed"
                          ? "success"
                          : item.status === "failed"
                            ? "danger"
                            : "warning"
                      }
                    >
                      {item.status}
                    </StatusPill>
                  </div>
                  <div className="text-sm text-[color:var(--ink-soft)]">
                    Keywords:{" "}
                    {item.jd_analysis.keywords.slice(0, 5).join(", ") ||
                      "No keywords extracted."}
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No target applications"
            body="Create an application from a parsed resume and JD before trying to score fit."
            action={
              <Button onClick={() => navigate("/job-analysis")} type="button">
                Create application
              </Button>
            }
          />
        )}
      </Panel>
      <Panel
        title="Matching report"
        eyebrow="scores and gaps"
        actions={
          selectedApplication ? (
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void loadReport(selectedApplication.id)} type="button">
                Refresh report
              </Button>
              <Button onClick={() => void runWorkflow(selectedApplication.id)} type="button">
                Run workflow
              </Button>
              <Button onClick={() => navigate("/generated")} type="button">
                View outputs
              </Button>
            </div>
          ) : null
        }
      >
        <ErrorNotice message={error} />
        {selectedApplication ? (
          <div className="mb-4 flex flex-wrap items-center gap-3 border border-[color:var(--line)] px-4 py-3">
            <div>
              <div className="editorial-serif text-2xl">{selectedApplication.company_name}</div>
              <div className="text-sm text-[color:var(--ink-soft)]">
                {selectedApplication.job_title}
              </div>
            </div>
            {run ? (
              <StatusPill
                tone={
                  run.status === "success"
                    ? "success"
                    : run.status === "failed"
                      ? "danger"
                      : "warning"
                }
              >
                {run.status} / {run.run_id.slice(0, 8)}
              </StatusPill>
            ) : null}
          </div>
        ) : null}
        {report ? (
          <div className="grid gap-4">
            <div className="grid gap-4 md:grid-cols-3">
              <Stat label="Overall" value={report.overall_score} />
              <Stat label="Matched" value={report.matched_keywords.length} />
              <Stat label="Missing" value={report.missing_keywords.length} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="border border-[color:var(--line)] p-4">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Dimension scores
                </div>
                <div className="mt-3 grid gap-2 text-sm">
                  {Object.entries(report.dimension_scores).map(([label, value]) => (
                    <div
                      key={label}
                      className="flex justify-between gap-4 border-b border-[color:var(--line)] pb-2"
                    >
                      <span>{label.replaceAll("_", " ")}</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border border-[color:var(--line)] p-4">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Missing keywords
                </div>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
                  {report.missing_keywords.length ? (
                    report.missing_keywords.map((item) => <li key={item}>{item}</li>)
                  ) : (
                    <li>No major keyword gaps detected.</li>
                  )}
                </ul>
              </div>
            </div>
            <div className="border border-[color:var(--line)] p-4">
              <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                Recommendations
              </div>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
                {report.recommendations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : loading ? (
          <div className="text-sm text-[color:var(--ink-soft)]">Loading report.</div>
        ) : (
          <div className="text-sm text-[color:var(--ink-soft)]">
            Select an application to inspect its score.
          </div>
        )}
      </Panel>
    </div>
  );
}
