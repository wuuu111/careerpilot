import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { useWorkspaceStore } from "@/app/workspace-store";
import { api, ApplicationRecord, ResumeRecord } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Input, Panel, Select, Textarea } from "@/components/ui";

export function JobAnalysisPage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const setSelectedApplicationId = useWorkspaceStore((state) => state.setSelectedApplicationId);
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [companyContext, setCompanyContext] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listResumes(token), api.listApplications(token)])
      .then(([resumeItems, appItems]) => {
        setResumes(resumeItems);
        setApplications(appItems);
        if (resumeItems[0]) {
          setResumeId((current) => current || resumeItems[0].id);
        }
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Failed to load form."));
  }, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const record = await api.createApplication(token, {
        resume_id: resumeId,
        company_name: companyName,
        job_title: jobTitle,
        job_description: jobDescription,
        company_context: companyContext || undefined,
      });
      setSelectedApplicationId(record.id);
      setApplications((current) => [record, ...current]);
      setCompanyName("");
      setJobTitle("");
      setJobDescription("");
      setCompanyContext("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to create application.");
    }
  }

  const latest = useMemo(() => applications[0], [applications]);

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <Panel title="Create application" eyebrow="jd analysis">
        {resumes.length ? (
          <form className="space-y-4" onSubmit={handleCreate}>
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.2em]">Resume</span>
              <Select
                onChange={(event) => setResumeId(event.target.value)}
                value={resumeId}
              >
                {resumes.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    {resume.file_name}
                  </option>
                ))}
              </Select>
            </label>
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.2em]">Company</span>
              <Input value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
            </label>
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.2em]">Role</span>
              <Input value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} />
            </label>
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.2em]">Job description</span>
              <Textarea value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} />
            </label>
            <label className="block space-y-2">
              <span className="mono-ui text-xs uppercase tracking-[0.2em]">Company context</span>
              <Textarea
                value={companyContext}
                onChange={(event) => setCompanyContext(event.target.value)}
              />
            </label>
            <ErrorNotice message={error} />
            <div className="flex flex-wrap gap-2">
              <Button type="submit">Save target role</Button>
              {latest ? (
                <Button onClick={() => navigate("/matching")} type="button">
                  Continue to matching
                </Button>
              ) : null}
            </div>
          </form>
        ) : (
          <EmptyState
            title="Resume required first"
            body="Application creation depends on a parsed resume. Upload one in the resume workspace, then come back here to structure a JD against it."
            action={
              <Button onClick={() => navigate("/resumes")} type="button">
                Open resumes
              </Button>
            }
          />
        )}
      </Panel>
      <Panel title="Latest analysis" eyebrow="parsed jd">
        {latest ? (
          <div className="space-y-4">
            <div>
              <div className="editorial-serif text-3xl">{latest.company_name}</div>
              <div className="text-sm text-[color:var(--ink-soft)]">{latest.job_title}</div>
            </div>
            {latest.has_company_context ? (
              <div className="border border-[color:var(--line)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
                Company context indexed for RAG-backed retrieval in later workflow runs.
              </div>
            ) : null}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="border border-[color:var(--line)] p-4 text-sm leading-7">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Required skills
                </div>
                <p className="mt-3">{latest.jd_analysis.required_skills.join(", ") || "No skills extracted."}</p>
              </div>
              <div className="border border-[color:var(--line)] p-4 text-sm leading-7">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Preferred skills
                </div>
                <p className="mt-3">{latest.jd_analysis.preferred_skills.join(", ") || "No preferred skills extracted."}</p>
              </div>
              <div className="border border-[color:var(--line)] p-4 text-sm leading-7">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Responsibilities
                </div>
                <p className="mt-3">{latest.jd_analysis.responsibilities.join(" | ") || "No responsibilities extracted."}</p>
              </div>
              <div className="border border-[color:var(--line)] p-4 text-sm leading-7">
                <div className="mono-ui text-xs uppercase tracking-[0.2em] text-[color:var(--ink-blue)]">
                  Business context
                </div>
                <p className="mt-3">
                  {latest.jd_analysis.business_scenario || "No business scenario extracted."}
                </p>
                <p className="mt-3 text-xs uppercase tracking-[0.16em] text-[color:var(--ink-soft)]">
                  {latest.jd_analysis.seniority_level} / {latest.jd_analysis.role_type}
                </p>
                <p className="mt-3">{latest.jd_analysis.keywords.join(", ") || "No keywords extracted."}</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => navigate("/matching")} type="button">
                Run matching
              </Button>
              <Button onClick={() => navigate("/generated")} type="button">
                Open outputs
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-[color:var(--ink-soft)]">No applications yet.</div>
        )}
      </Panel>
    </div>
  );
}
