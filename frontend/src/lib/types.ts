export interface PipelineStep {
  step: string;
  status: "running" | "done" | "error";
  detail?: string;
  ms?: number | null;
}

export interface Deadline {
  label: string;
  date: string | null;
  raw: string;
  source_page: number | null;
}

export interface Criterion {
  name: string;
  weight_pct: number | null;
  description: string;
}

export interface QAItem {
  question: string;
  section: string;
  source_page: number | null;
}

export interface RFPProfile {
  title: string;
  issuer: string;
  sector: string;
  summary: string;
  budget_raw: string;
  budget_pkr_m: number | null;
  submission_deadline: string | null;
  deadlines: Deadline[];
  criteria: Criterion[];
  qa_items: QAItem[];
  submission_instructions: string;
}

export interface Evidence {
  cap_id: string;
  domain: string;
  summary: string;
  certification: string;
  year_completed: number;
  contract_value: string;
  duration_months: number;
  client_type: string;
  score: number;
  cosine: number;
  keyword: number;
}

export interface Requirement {
  id: string;
  idx: number;
  text: string;
  category: string;
  mandatory: boolean;
  source_page: number | null;
  status: "PASS" | "PARTIAL" | "GAP" | null;
  confidence: number | null;
  rationale: string | null;
  evidence: Evidence[];
  used_cap_ids: string[];
  overridden: number;
}

export interface DraftSection {
  id: string;
  idx: number;
  title: string;
  content: string;
  citations: string[];
  status: "draft" | "approved";
}

export interface ShapItem {
  feature: string;
  label: string;
  value: number;
  impact: number;
}

export interface EstimatorComponent {
  name: string;
  points: number;
  detail: string;
}

export interface WinProb {
  probability: number;
  model: string;
  model_cv_auc: number | null;
  estimator: { estimated_score: number; components: EstimatorComponent[] };
  shap: ShapItem[];
  decision: { decision: "GO" | "CONDITIONAL_GO" | "NO_GO"; label: string };
  memo: string;
  comparables: {
    bid_id: string; client: string; sector: string; budget: string;
    outcome: string; score: number; compliance: number; gaps: number;
  }[];
  compliance_summary: ComplianceSummary;
}

export interface ComplianceSummary {
  total: number;
  counts: { PASS: number; PARTIAL: number; GAP: number };
  compliance_pct: number;
  mandatory_gaps: string[];
}

export interface Effort {
  pipeline_seconds: number;
  manual_baseline_hours: number;
  baseline_basis: string;
  reduction_pct: number;
}

export interface Workspace {
  id: string;
  name: string;
  filename: string;
  filetype: string;
  created_at: string;
  status: string;
  pipeline: PipelineStep[] | null;
  profile: RFPProfile | null;
  winprob: WinProb | null;
  effort: Effort | null;
  error?: string | null;
  requirements?: Requirement[];
  sections?: DraftSection[];
}

export const RUNNING_STATUSES = ["extracting", "matching", "scoring", "drafting"];
