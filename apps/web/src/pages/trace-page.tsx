import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { AgentStep } from "@careerpilot/shared";

import { useAuthStore } from "@/app/auth-store";
import { useWorkspaceStore } from "@/app/workspace-store";
import { api, AgentRun, ApplicationRecord } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Panel, Stat, StatusPill } from "@/components/ui";

export function TracePage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const selectedApplicationId = useWorkspaceStore((state) => state.selectedApplicationId);
  const setSelectedApplicationId = useWorkspaceStore((state) => state.setSelectedApplicationId);
  const activeRunId = useWorkspaceStore((state) => state.activeRunId);
  const setActiveRunId = useWorkspaceStore((state) => state.setActiveRunId);

  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listApplications(token)
      .then((items) => {
        setApplications(items);
        if (!selectedApplicationId && items[0]) {
          setSelectedApplicationId(items[0].id);
        }
      })
      .catch((caught) => {
        setError(caught instanceof Error ? caught.message : "Unable to list applications.");
      });
  }, [selectedApplicationId, setSelectedApplicationId, token]);

  useEffect(() => {
    if (!activeRunId) {
      setRun(null);
      setSteps([]);
      return;
    }

    let cancelled = false;

    async function refreshTrace() {
      try {
        const [currentRun, stepsResponse] = await Promise.all([
          api.getRun(token, activeRunId),
          api.getSteps(token, activeRunId),
        ]);
        if (cancelled) {
          return;
        }
        setRun(currentRun);
        setSteps(stepsResponse.steps);
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Trace unavailable.");
        }
      }
    }

    void refreshTrace();
    const interval = window.setInterval(() => {
      void refreshTrace();
    }, 2500);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [activeRunId, token]);

  async function handleRun(applicationId: string) {
    try {
      setError(null);
      setSelectedApplicationId(applicationId);
      const response = await api.createRun(token, applicationId);
      setActiveRunId(response.run_id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to start workflow.");
    }
  }

  const selectedApplication =
    applications.find((item) => item.id === selectedApplicationId) ?? applications[0] ?? null;

  return (
    <div className="grid gap-6 lg:grid-cols-[0.75fr_1.25fr]">
      <Panel title="Workflow runs" eyebrow="agent trace">
        {applications.length ? (
          <div className="space-y-3">
            {applications.map((item) => (
              <div
                key={item.id}
                className={[
                  "border p-4",
                  item.id === selectedApplication?.id
                    ? "border-[color:var(--ink)] bg-[color:var(--paper-deep)]"
                    : "border-[color:var(--line)]",
                ].join(" ")}
              >
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <div className="editorial-serif text-2xl">{item.company_name}</div>
                      <div className="mt-1 text-sm text-[color:var(--ink-soft)]">{item.job_title}</div>
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
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => void handleRun(item.id)} type="button">
                      Start run
                    </Button>
                    <Button onClick={() => setSelectedApplicationId(item.id)} type="button">
                      Focus
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No applications to trace"
            body="The trace ledger is populated by workflow runs. Create an application and launch a run to inspect agent-by-agent outputs."
            action={
              <Button onClick={() => navigate("/job-analysis")} type="button">
                Create application
              </Button>
            }
          />
        )}
      </Panel>
      <Panel
        title="Step ledger"
        eyebrow={activeRunId ? `run ${activeRunId}` : "no active run"}
        actions={
          activeRunId ? (
            <Button onClick={() => navigate("/generated")} type="button">
              Open outputs
            </Button>
          ) : null
        }
      >
        <ErrorNotice message={error} />
        {run ? (
          <div className="mb-4 grid gap-4 md:grid-cols-4">
            <Stat label="Status" value={run.status} />
            <Stat label="Steps" value={steps.length} />
            <Stat
              label="Succeeded"
              value={steps.filter((step) => step.status === "success").length}
            />
            <Stat
              label="Failed"
              value={steps.filter((step) => step.status === "failed").length}
            />
          </div>
        ) : null}
        {steps.length ? (
          <div className="space-y-3">
            {steps.map((step) => (
              <div key={step.step_id} className="border border-[color:var(--line)] p-4">
                <div className="flex flex-col gap-2 md:flex-row md:justify-between">
                  <div>
                    <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                      {step.agent_name}
                    </div>
                    <div className="mt-2 text-sm text-[color:var(--ink-soft)]">
                      latency {step.latency_ms}ms
                    </div>
                  </div>
                  <StatusPill tone={step.status === "failed" ? "danger" : "success"}>
                    {step.status}
                  </StatusPill>
                </div>
                {step.error_message ? (
                  <div className="mt-3 text-sm text-[color:var(--danger)]">{step.error_message}</div>
                ) : null}
                <details className="mt-4 border border-[color:var(--line)] p-3 text-xs">
                  <summary className="mono-ui cursor-pointer uppercase tracking-[0.16em]">
                    Step payload
                  </summary>
                  <pre className="mt-3 overflow-x-auto whitespace-pre-wrap leading-6 text-[color:var(--ink-soft)]">
                    {JSON.stringify(
                      {
                        input: step.input,
                        output: step.output,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </details>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No active trace selected"
            body="Start a workflow run from this page or from matching, then the agent ledger and step payloads will stream into this workspace."
          />
        )}
      </Panel>
    </div>
  );
}
