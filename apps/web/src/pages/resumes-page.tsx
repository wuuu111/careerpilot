import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "@/app/auth-store";
import { api, ResumeRecord } from "@/lib/api";
import { Button, EmptyState, ErrorNotice, Panel } from "@/components/ui";

export function ResumesPage() {
  const navigate = useNavigate();
  const token = useAuthStore((state) => state.token)!;
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadedName, setUploadedName] = useState<string | null>(null);

  async function refresh() {
    const items = await api.listResumes(token);
    setResumes(items);
  }

  useEffect(() => {
    refresh().catch((caught) => setError(caught instanceof Error ? caught.message : "Load failed."));
  }, [token]);

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      return;
    }
    setError(null);
    try {
      await api.uploadResume(token, selectedFile);
      setUploadedName(selectedFile.name);
      setSelectedFile(null);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Panel title="Upload resume" eyebrow="ingestion">
        <form className="space-y-4" onSubmit={handleUpload}>
          <input
            accept=".pdf,.docx"
            className="w-full border border-[color:var(--ink)] px-3 py-4"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            type="file"
          />
          <p className="text-sm text-[color:var(--ink-soft)]">
            Supported formats: PDF and DOCX, up to 10MB. Files are parsed immediately and stored as structured text.
          </p>
          {uploadedName ? (
            <div className="border border-[color:var(--line)] px-4 py-3 text-sm text-[color:var(--ink-soft)]">
              Uploaded <span className="font-medium text-[color:var(--ink)]">{uploadedName}</span>. Continue into job analysis to create a target role.
            </div>
          ) : null}
          <ErrorNotice message={error} />
          <div className="flex flex-wrap gap-2">
            <Button type="submit">Upload</Button>
            <Button onClick={() => navigate("/job-analysis")} type="button">
              Create application
            </Button>
          </div>
        </form>
      </Panel>
      <Panel title="Structured resumes" eyebrow="stored artifacts">
        {resumes.length ? (
          <div className="space-y-3">
            {resumes.map((resume) => (
              <div key={resume.id} className="border border-[color:var(--line)] p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:justify-between">
                  <div className="space-y-3">
                    <div className="mono-ui text-xs uppercase tracking-[0.18em] text-[color:var(--ink-soft)]">
                      {resume.file_name}
                    </div>
                    <div className="editorial-serif text-2xl">
                      {resume.parsed_result.basic_info.name || "Unnamed candidate"}
                    </div>
                    <div className="grid gap-2 text-sm text-[color:var(--ink-soft)]">
                      <div>Skills: {resume.parsed_result.skills.join(", ") || "No skills extracted yet."}</div>
                      <div>Projects: {resume.parsed_result.projects.slice(0, 2).join(" | ") || "No projects extracted."}</div>
                      <div>Experience: {resume.parsed_result.experience.slice(0, 2).join(" | ") || "No experience extracted."}</div>
                    </div>
                  </div>
                  <div className="max-w-md text-sm leading-6 text-[color:var(--ink-soft)]">
                    {resume.parsed_result.education.slice(0, 2).join(" | ") || "Education details were not extracted from this file."}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No resumes ingested"
            body="Upload a source resume first. The parser will extract candidate basics, skills, projects, experience, and a RAG-ready text payload for later retrieval work."
          />
        )}
      </Panel>
    </div>
  );
}
