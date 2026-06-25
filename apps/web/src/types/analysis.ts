export type PathwayId = "ai_automation" | "software_fullstack" | "embedded_firmware";
export type LocationId = "auckland" | "new_zealand" | "remote";
export type SkillStatus = "strong_proof" | "hidden_proof" | "adjacent_proof" | "no_proof_yet";
export type Confidence = "high" | "medium" | "low";

export interface AnalyseRequest {
  resume_text: string;
  target_pathway: PathwayId;
  location: LocationId;
  github_repo_url?: string;
  use_demo_data: boolean;
}

export interface CandidateEvidence {
  source: string;
  excerpt: string;
}

export interface SkillAnalysis {
  name: string;
  market_label: string;
  listing_count: number;
  total_listings: number;
  employer_count: number;
  required_count: number;
  status: SkillStatus;
  confidence: Confidence;
  market_evidence: string;
  candidate_evidence: CandidateEvidence[];
  recommended_action: string;
}

export interface BridgePlanItem {
  priority: number;
  action_type: "surface" | "strengthen" | "build";
  skill_name: string;
  title: string;
  time_estimate: string;
  market_signal: string;
  candidate_evidence_found: string;
  confidence: Confidence;
  recommended_action: string;
  why: string;
  steps: string[];
  resume_draft?: string | null;
}

export interface AnalysisResponse {
  market_snapshot: {
    listing_count: number;
    distinct_employers: number;
    location: string;
    role_pathway: string;
    captured_at: string;
    sources: string[];
  };
  headline: string;
  role_pathways: Array<{
    id: PathwayId;
    label: string;
    evidence_coverage: number;
    market_demand: "high" | "medium" | "focused";
    summary: string;
  }>;
  skills: SkillAnalysis[];
  bridge_plan: BridgePlanItem[];
  methodology: string[];
}
