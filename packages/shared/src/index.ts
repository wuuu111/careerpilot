export type ErrorEnvelope = {
  error_code: string;
  message: string;
  details: Record<string, unknown>;
};

export type AuthToken = {
  access_token: string;
  token_type: "bearer";
};

export type ResumeParsedResult = {
  basic_info: {
    name: string;
    email: string;
    phone: string;
    location: string;
  };
  education: string[];
  skills: string[];
  projects: string[];
  experience: string[];
  awards: string[];
};

export type JobDescriptionAnalysis = {
  role_type: string;
  responsibilities: string[];
  required_skills: string[];
  preferred_skills: string[];
  keywords: string[];
  business_scenario: string;
  seniority_level: string;
};

export type GeneratedOutputType =
  | "matching_report"
  | "rewritten_resume"
  | "cover_letter"
  | "interview_prep"
  | "evaluation";

export type GeneratedOutput = {
  output_type: GeneratedOutputType;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  version: string;
};

export type GeneratedOutputHistoryItem = GeneratedOutput & {
  output_id: string;
};

export type GeneratedOutputHistory = {
  output_type: GeneratedOutputType;
  items: GeneratedOutputHistoryItem[];
};

export type GeneratedOutputCompare = {
  output_type: GeneratedOutputType;
  current: GeneratedOutputHistoryItem;
  previous: GeneratedOutputHistoryItem | null;
  diff: {
    changed_fields?: string[];
    current_created_at?: string;
    previous_created_at?: string;
  };
};

export type CompanyProfile = {
  id: string;
  application_id: string;
  company_name: string;
  content: string;
  created_at: string;
};

export type AgentRunStatus = "queued" | "running" | "success" | "failed";

export type AgentStep = {
  step_id: string;
  agent_name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  status: string;
  latency_ms: number;
  error_message: string | null;
  created_at: string;
};
