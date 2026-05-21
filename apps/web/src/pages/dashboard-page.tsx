import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useWorkspaceStore } from "@/app/workspace-store";
import { useAuthStore } from "@/app/auth-store";
import { api, ApplicationRecord } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Panel, Stat, StatusPill } from "@/components/ui";

export function DashboardPage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const selectedApplicationId = useWorkspaceStore((state) => state.selectedApplicationId);
  const setSelectedApplicationId = useWorkspaceStore((state) => state.setSelectedApplicationId);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listApplications(token).then((items) => {
      setApplications(items);
      if (!selectedApplicationId && items[0]) {
        setSelectedApplicationId(items[0].id);
      }
    }).catch((caught) => {
      setError(caught instanceof Error ? caught.message : "Unable to load dashboard.");
    });
  }, [selectedApplicationId, setSelectedApplicationId, token]);

  function openWorkspace(path: string, applicationId: string) {
    setSelectedApplicationId(applicationId);
    navigate(path);
  }

  const runningCount = applications.filter((item) => item.status === "running").length;
  const failedCount = applications.filter((item) => item.status === "failed").length;

  return (
    <div className="grid gap-6">
      <Panel title="Overview" eyebrow="system summary">
        <ErrorNotice message={error} />
        <div className="grid gap-4 md:grid-cols-4">
          <Stat label="Applications" value={applications.length} />
          <Stat
            label="Completed"
            value={applications.filter((item) => item.status === "completed").length}
          />
          <Stat label="Running" value={runningCount} />
          <Stat label="Failed" value={failedCount} />
        </div>
      </Panel>
      <Panel title="Recent applications" eyebrow="activity ledger">
        {applications.length ? (
          <div className="space-y-3">
            {applications.map((item) => (
              <div
                key={item.id}
                className={[
                  "border p-4",
                  item.id === selectedApplicationId
                    ? "border-[color:var(--ink)] bg-[color:var(--paper-deep)]"
                    : "border-[color:var(--line)]",
                ].join(" ")}
              >
                <div className="flex flex-col gap-4 md:flex-row md:justify-between">
                  <div className="space-y-3">
                    <div>
                      <div className="editorial-serif text-2xl">{item.company_name}</div>
                      <div className="text-sm text-[color:var(--ink-soft)]">{item.job_title}</div>
                    </div>
                    <div className="flex flex-wrap gap-2 text-sm text-[color:var(--ink-soft)]">
                      {item.jd_analysis.keywords.slice(0, 4).map((keyword) => (
                        <span key={keyword} className="border border-[color:var(--line)] px-2 py-1">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-col items-start gap-3 md:items-end">
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
                    <div className="flex flex-wrap gap-2">
                      <Button onClick={() => openWorkspace("/matching", item.id)} type="button">
                        Continue
                      </Button>
                      <Button onClick={() => openWorkspace("/generated", item.id)} type="button">
                        Outputs
                      </Button>
                      <Button onClick={() => openWorkspace("/trace", item.id)} type="button">
                        Trace
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No applications yet"
            body="Start with a resume upload, then create a job target so the workflow has something to execute."
            action={
              <Button onClick={() => navigate("/resumes")} type="button">
                Upload resume
              </Button>
            }
          />
        )}
      </Panel>
    </div>
  );
}
