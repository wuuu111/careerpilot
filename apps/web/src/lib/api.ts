import type {
  AgentStep,
  AuthToken,
  CompanyProfile,
  ErrorEnvelope,
  GeneratedOutputCompare,
  GeneratedOutput,
  GeneratedOutputHistory,
  GeneratedOutputType,
  JobDescriptionAnalysis,
  ResumeParsedResult,
} from "@careerpilot/shared";

import { API_BASE_URL, CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from "@/lib/config";

export type User = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type ResumeRecord = {
  id: string;
  file_name: string;
  parsed_result: ResumeParsedResult;
  created_at: string;
};

export type ApplicationRecord = {
  id: string;
  resume_id: string;
  jd_id: string;
  company_name: string;
  job_title: string;
  status: string;
  created_at: string;
  jd_analysis: JobDescriptionAnalysis;
  has_company_context: boolean;
};

export type AgentRun = {
  run_id: string;
  application_id: string;
  status: string;
  workflow_type: string;
  started_at: string;
  finished_at: string | null;
};

export type MatchingReport = {
  overall_score: number;
  dimension_scores: Record<string, number>;
  matched_keywords: string[];
  missing_keywords: string[];
  recommendations: string[];
};

export class ApiError extends Error {
  errorCode: string;
  details: Record<string, unknown>;

  constructor(payload: ErrorEnvelope) {
    super(payload.message);
    this.name = "ApiError";
    this.errorCode = payload.error_code;
    this.details = payload.details;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  _token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const method = (options.method ?? "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrfToken = readCookie(CSRF_COOKIE_NAME);
    if (csrfToken) {
      headers.set(CSRF_HEADER_NAME, csrfToken);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    const payload = (await response.json()) as ErrorEnvelope;
    throw new ApiError(payload);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookie = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${name}=`));
  if (!cookie) {
    return null;
  }
  return decodeURIComponent(cookie.slice(name.length + 1));
}

export const api = {
  register: (payload: { name: string; email: string; password: string }) =>
    request<User>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) =>
    request<AuthToken>("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: (_token?: string | null) => request<User>("/api/auth/me"),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  uploadResume: (token: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<ResumeRecord>("/api/resumes/upload", { method: "POST", body: formData }, token);
  },
  listResumes: (token: string) => request<ResumeRecord[]>("/api/resumes", {}, token),
  createApplication: (
    token: string,
    payload: {
      resume_id: string;
      company_name: string;
      job_title: string;
      job_description: string;
      company_context?: string;
    },
  ) =>
    request<ApplicationRecord>(
      "/api/applications",
      { method: "POST", body: JSON.stringify(payload) },
      token,
    ),
  listApplications: (token: string) =>
    request<ApplicationRecord[]>("/api/applications", {}, token),
  getApplication: (token: string, applicationId: string) =>
    request<ApplicationRecord>(`/api/applications/${applicationId}`, {}, token),
  getCompanyProfile: (token: string, applicationId: string) =>
    request<CompanyProfile>(`/api/applications/${applicationId}/company-profile`, {}, token),
  createRun: (token: string, applicationId: string) =>
    request<{ run_id: string; status: string }>(
      "/api/agent-runs",
      {
        method: "POST",
        body: JSON.stringify({ application_id: applicationId, workflow_type: "full_application" }),
      },
      token,
    ),
  getRun: (token: string, runId: string) => request<AgentRun>(`/api/agent-runs/${runId}`, {}, token),
  getSteps: (token: string, runId: string) =>
    request<{ run_id: string; steps: AgentStep[] }>(`/api/agent-runs/${runId}/steps`, {}, token),
  getMatchingReport: (token: string, applicationId: string) =>
    request<MatchingReport>(`/api/applications/${applicationId}/matching-report`, {}, token),
  generateCoverLetter: (
    token: string,
    applicationId: string,
    payload: { style: string; language: string },
  ) =>
    request<GeneratedOutput>(
      `/api/applications/${applicationId}/cover-letter`,
      { method: "POST", body: JSON.stringify(payload) },
      token,
    ),
  getGeneratedOutput: (token: string, applicationId: string, type: GeneratedOutputType) =>
    request<GeneratedOutput>(
      `/api/applications/${applicationId}/generated-outputs?type=${type}`,
      {},
      token,
    ),
  getGeneratedOutputHistory: (token: string, applicationId: string, type: GeneratedOutputType) =>
    request<GeneratedOutputHistory>(
      `/api/applications/${applicationId}/generated-outputs/history?type=${type}`,
      {},
      token,
    ),
  compareGeneratedOutputs: (token: string, applicationId: string, type: GeneratedOutputType) =>
    request<GeneratedOutputCompare>(
      `/api/applications/${applicationId}/generated-outputs/compare?type=${type}`,
      {},
      token,
    ),
};
