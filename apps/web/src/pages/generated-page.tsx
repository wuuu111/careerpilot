import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import type {
  CompanyProfile,
  GeneratedOutput,
  GeneratedOutputCompare,
  GeneratedOutputHistory,
  GeneratedOutputType,
} from "@careerpilot/shared";

import { useAuthStore } from "@/app/auth-store";
import { useWorkspaceStore } from "@/app/workspace-store";
import { api, ApplicationRecord } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Panel, Select, Stat, StatusPill } from "@/components/ui";
import { SourceCitations } from "@/components/source-citations";
import { VersionCompare } from "@/components/version-compare";

const outputTypes: GeneratedOutputType[] = [
  "matching_report",
  "rewritten_resume",
  "cover_letter",
  "interview_prep",
  "evaluation",
];

function parseOutput(output: GeneratedOutput | null): Record<string, unknown> | null {
  if (!output) {
    return null;
  }
  try {
    return JSON.parse(output.content) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function GeneratedPage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const selectedApplicationId = useWorkspaceStore((state) => state.selectedApplicationId);
  const setSelectedApplicationId = useWorkspaceStore((state) => state.setSelectedApplicationId);
  const setActiveRunId = useWorkspaceStore((state) => state.setActiveRunId);

  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [selectedType, setSelectedType] = useState<GeneratedOutputType>("matching_report");
  const [output, setOutput] = useState<GeneratedOutput | null>(null);
  const [history, setHistory] = useState<GeneratedOutputHistory | null>(null);
  const [comparison, setComparison] = useState<GeneratedOutputCompare | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
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
      setOutput(null);
      return;
    }

    void refreshOutputState(selectedApplicationId, selectedType);
  }, [selectedApplicationId, selectedType, token]);

  async function refreshOutputState(applicationId: string, outputType: GeneratedOutputType) {
    setLoading(true);
    setError(null);
    try {
      const [nextOutput, nextHistory, nextComparison, nextCompanyProfile] = await Promise.all([
        api.getGeneratedOutput(token, applicationId, outputType),
        api.getGeneratedOutputHistory(token, applicationId, outputType).catch(() => null),
        api.compareGeneratedOutputs(token, applicationId, outputType).catch(() => null),
        api.getCompanyProfile(token, applicationId).catch(() => null),
      ]);
      setOutput(nextOutput);
      setHistory(nextHistory);
      setComparison(nextComparison);
      setCompanyProfile(nextCompanyProfile);
    } catch (caught) {
      setOutput(null);
      setHistory(null);
      setComparison(null);
      setError(caught instanceof Error ? caught.message : "Output unavailable.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCoverLetterGenerate() {
    if (!selectedApplicationId) {
      return;
    }
    try {
      const generated = await api.generateCoverLetter(token, selectedApplicationId, {
        style: "technical",
        language: "en",
      });
      setSelectedType("cover_letter");
      setOutput(generated);
      await refreshOutputState(selectedApplicationId, "cover_letter");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Cover letter generation failed.");
    }
  }

  async function handleRunWorkflow() {
    if (!selectedApplicationId) {
      return;
    }
    try {
      setError(null);
      const run = await api.createRun(token, selectedApplicationId);
      setActiveRunId(run.run_id);
      navigate("/trace");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Workflow failed to start.");
    }
  }

  const selectedApplication =
    applications.find((item) => item.id === selectedApplicationId) ?? applications[0] ?? null;
  const parsedOutput = useMemo(() => parseOutput(output), [output]);
  const citations = ((output?.metadata.citations as Array<Record<string, unknown>> | undefined) ?? []);

  function renderOutput() {
    if (!output) {
      return null;
    }

    if (selectedType === "matching_report" && parsedOutput) {
      return (
        <div className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Overall" value={String(parsedOutput.overall_score ?? "-")} />
            <Stat
              label="Matched"
              value={String(((parsedOutput.matched_keywords as unknown[]) ?? []).length)}
            />
            <Stat
              label="Missing"
              value={String(((parsedOutput.missing_keywords as unknown[]) ?? []).length)}
            />
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-4 text-sm leading-7">
            {output.content}
          </pre>
        </div>
      );
    }

    if (selectedType === "rewritten_resume" && parsedOutput) {
      const items = (parsedOutput.items as Array<Record<string, string>> | undefined) ?? [];
      return (
        <div className="space-y-3">
          {items.map((item, index) => (
            <div key={`${item.original_bullet}-${index}`} className="border border-[color:var(--line)] p-4">
              <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
                {item.risk_level} risk
              </div>
              <p className="mt-3 text-sm text-[color:var(--ink-soft)]">{item.original_bullet}</p>
              <p className="mt-3 text-sm leading-7">{item.rewritten_bullet}</p>
              <p className="mt-3 text-xs leading-6 text-[color:var(--ink-soft)]">{item.reason}</p>
            </div>
          ))}
        </div>
      );
    }

    if (selectedType === "cover_letter" && parsedOutput) {
      return (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Stat label="Style" value={String(parsedOutput.style ?? "-")} />
            <Stat label="Words" value={String(parsedOutput.word_count ?? "-")} />
            <Stat
              label="Evidence"
              value={String(((parsedOutput.used_evidence as unknown[]) ?? []).length)}
            />
          </div>
          <pre className="overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-4 text-sm leading-7">
            {String(parsedOutput.cover_letter ?? output.content)}
          </pre>
        </div>
      );
    }

    if (selectedType === "interview_prep" && parsedOutput) {
      const sections = [
        ["HR questions", parsedOutput.hr_questions],
        ["Technical questions", parsedOutput.technical_questions],
        ["Project deep dive", parsedOutput.project_deep_dive_questions],
        ["Review plan", parsedOutput.review_plan],
      ] as const;
      return (
        <div className="grid gap-4 md:grid-cols-2">
          {sections.map(([label, value]) => (
            <div key={label} className="border border-[color:var(--line)] p-4">
              <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
                {label}
              </div>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
                {((value as string[] | undefined) ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      );
    }

    if (selectedType === "evaluation" && parsedOutput) {
      return (
        <div className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-4">
            <Stat label="Faithfulness" value={String(parsedOutput.faithfulness ?? "-")} />
            <Stat label="JD coverage" value={String(parsedOutput.jd_coverage ?? "-")} />
            <Stat label="Specificity" value={String(parsedOutput.specificity ?? "-")} />
            <Stat label="Readability" value={String(parsedOutput.readability ?? "-")} />
          </div>
          <div className="border border-[color:var(--line)] p-4">
            <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
              Suggestions
            </div>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
              {(((parsedOutput.suggestions as string[] | undefined) ?? [])).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="mt-3 text-sm text-[color:var(--ink-soft)]">
              Hallucination risk: {String(parsedOutput.hallucination_risk ?? "-")}
            </p>
          </div>
        </div>
      );
    }

    return (
      <pre className="overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-4 text-sm leading-7">
        {output.content}
      </pre>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <Panel title="Output selector" eyebrow="versioned artifacts">
        {applications.length ? (
          <div className="space-y-4">
            <Select
              onChange={(event) => setSelectedApplicationId(event.target.value)}
              value={selectedApplicationId}
            >
              {applications.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.company_name} / {item.job_title}
                </option>
              ))}
            </Select>
            <div className="flex flex-wrap gap-2">
              {outputTypes.map((type) => (
                <Button
                  key={type}
                  className={selectedType === type ? "bg-[color:var(--paper-deep)]" : ""}
                  onClick={() => setSelectedType(type)}
                  type="button"
                >
                  {type}
                </Button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleRunWorkflow} type="button">
                Run workflow
              </Button>
              <Button onClick={handleCoverLetterGenerate} type="button">
                Generate cover letter
              </Button>
              <Button onClick={() => navigate("/trace")} type="button">
                Open trace
              </Button>
            </div>
          </div>
        ) : (
          <EmptyState
            title="No applications available"
            body="Generated artifacts belong to an application run. Create a target role first, then come back to inspect matching, rewritten bullets, letters, interview prep, and evaluation."
            action={
              <Button onClick={() => navigate("/job-analysis")} type="button">
                Create application
              </Button>
            }
          />
        )}
      </Panel>
      <Panel title="Generated content" eyebrow={selectedType}>
        <ErrorNotice message={error} />
        {selectedApplication ? (
          <div className="mb-4 flex flex-wrap items-center gap-3 border border-[color:var(--line)] px-4 py-3">
            <div>
              <div className="editorial-serif text-2xl">{selectedApplication.company_name}</div>
              <div className="text-sm text-[color:var(--ink-soft)]">
                {selectedApplication.job_title}
              </div>
            </div>
            {output ? <StatusPill tone="success">{output.version}</StatusPill> : null}
            {output ? <StatusPill tone="success">{output.created_at}</StatusPill> : null}
          </div>
        ) : null}
        {output ? (
          <div className="space-y-4">
            {companyProfile ? (
              <div className="border border-[color:var(--line)] p-4">
                <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
                  Company knowledge
                </div>
                <p className="mt-3 text-sm leading-7 text-[color:var(--ink-soft)]">
                  {companyProfile.content}
                </p>
              </div>
            ) : null}
            {renderOutput()}
            <SourceCitations citations={citations} />
            <VersionCompare compare={comparison} />
            {history?.items.length ? (
              <div className="border border-[color:var(--line)] p-4">
                <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-blue)]">
                  Version history
                </div>
                <div className="mt-3 space-y-2">
                  {history.items.map((item) => (
                    <div key={item.output_id} className="flex flex-wrap items-center justify-between gap-3 border border-[color:var(--line)] px-3 py-2 text-sm">
                      <span>{item.version}</span>
                      <span className="text-[color:var(--ink-soft)]">{item.created_at}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
            <pre className="overflow-x-auto whitespace-pre-wrap border border-[color:var(--line)] p-4 text-xs leading-6 text-[color:var(--ink-soft)]">
              {JSON.stringify(output.metadata, null, 2)}
            </pre>
          </div>
        ) : loading ? (
          <div className="text-sm text-[color:var(--ink-soft)]">Loading output.</div>
        ) : (
          <EmptyState
            title="Artifact not generated yet"
            body="This output type has no current version for the selected application. Run the workflow to generate the full artifact set, or generate a cover letter directly from this page."
          />
        )}
      </Panel>
    </div>
  );
}
