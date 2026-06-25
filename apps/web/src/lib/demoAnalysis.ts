import type { AnalysisResponse } from "../types/analysis";

export const demoAnalysis: AnalysisResponse = {
  market_snapshot: {
    listing_count: 8,
    distinct_employers: 8,
    location: "Auckland",
    captured_at: "2026-06-25T10:00:00Z",
    sources: ["Cached curated snapshot"]
  },
  role_pathways: [
    {
      id: "ai_automation",
      label: "AI & Automation",
      evidence_coverage: 79,
      market_demand: "high",
      summary: "79% evidence coverage across the top skills in 8 cached roles."
    },
    {
      id: "software_fullstack",
      label: "Graduate Software / Full-Stack",
      evidence_coverage: 68,
      market_demand: "high",
      summary: "68% evidence coverage across the top skills in 6 cached roles."
    },
    {
      id: "embedded_firmware",
      label: "Embedded / Firmware",
      evidence_coverage: 62,
      market_demand: "medium",
      summary: "62% evidence coverage across the top skills in 6 cached roles."
    }
  ],
  skills: [
    {
      name: "Python",
      market_label: "Core demand",
      demand_score: 100,
      listing_count: 8,
      total_listings: 8,
      employer_count: 8,
      required_count: 7,
      status: "strong_proof",
      confidence: "high",
      market_evidence: "Python appeared in 8 of 8 relevant roles (7 listed it as required).",
      candidate_evidence: [{ source: "resume", excerpt: "Built a Python automation tool that cleaned telemetry CSV files with Pandas and produced weekly data visualisation summaries for a capstone team." }],
      recommended_action: "Surface this skill in a role-targeted project bullet with the concrete contribution intact."
    },
    {
      name: "REST APIs",
      market_label: "Growing signal",
      demand_score: 50,
      listing_count: 4,
      total_listings: 8,
      employer_count: 4,
      required_count: 3,
      status: "strong_proof",
      confidence: "high",
      market_evidence: "REST APIs appeared in 4 of 8 relevant roles (3 listed it as required).",
      candidate_evidence: [{ source: "resume", excerpt: "Created a React and TypeScript web app for project tracking, integrating REST APIs and SQLite-backed task storage." }],
      recommended_action: "Surface the integration evidence in a role-targeted project bullet."
    },
    {
      name: "Docker",
      market_label: "Growing signal",
      demand_score: 50,
      listing_count: 4,
      total_listings: 8,
      employer_count: 4,
      required_count: 2,
      status: "hidden_proof",
      confidence: "medium",
      market_evidence: "Docker appeared in 4 of 8 relevant roles (2 listed it as required).",
      candidate_evidence: [{ source: "repository:Dockerfile", excerpt: "Dockerfile found for the Python automation service, but Docker is not mentioned in the resume." }],
      recommended_action: "Make this proof visible in the resume or project README, and confirm you personally created or maintained it."
    },
    {
      name: "CI/CD",
      market_label: "Differentiator",
      demand_score: 25,
      listing_count: 2,
      total_listings: 8,
      employer_count: 2,
      required_count: 1,
      status: "hidden_proof",
      confidence: "medium",
      market_evidence: "CI/CD appeared in 2 of 8 relevant roles (1 listed it as required).",
      candidate_evidence: [{ source: "repository:.github/workflows/test.yml", excerpt: "GitHub Actions CI/CD workflow runs Python tests on pull requests." }],
      recommended_action: "Make this proof visible only if you created or maintained the workflow."
    },
    {
      name: "RAG",
      market_label: "Differentiator",
      demand_score: 25,
      listing_count: 2,
      total_listings: 8,
      employer_count: 2,
      required_count: 0,
      status: "adjacent_proof",
      confidence: "medium",
      market_evidence: "RAG appeared in 2 of 8 relevant roles (0 listed it as required).",
      candidate_evidence: [{ source: "resume", excerpt: "Built a Python automation tool that cleaned telemetry CSV files with Pandas and produced weekly data visualisation summaries for a capstone team." }],
      recommended_action: "Extend an existing project so the adjacent Python evidence proves RAG directly."
    },
    {
      name: "AWS",
      market_label: "Differentiator",
      demand_score: 25,
      listing_count: 2,
      total_listings: 8,
      employer_count: 2,
      required_count: 0,
      status: "no_proof_yet",
      confidence: "low",
      market_evidence: "AWS appeared in 2 of 8 relevant roles (0 listed it as required).",
      candidate_evidence: [],
      recommended_action: "Build a small, reviewable proof artifact before adding this skill to a resume."
    }
  ],
  bridge_plan: [
    {
      priority: 1,
      action_type: "surface",
      title: "Surface Docker",
      time_estimate: "20 minutes",
      why: "Docker is a growing signal in this selected snapshot, based on raw listing and employer counts.",
      steps: ["Add one project bullet that names the containerised setup.", "Add a short README setup note so a reviewer can verify it quickly."],
      resume_draft: "Containerised a full-stack telemetry app (Node.js backend + PostgreSQL) with Docker for reproducible team demos."
    },
    {
      priority: 2,
      action_type: "surface",
      title: "Surface CI/CD",
      time_estimate: "20 minutes",
      why: "CI/CD is a differentiator in this selected snapshot.",
      steps: ["Add a README badge or workflow note.", "Only add a resume bullet after confirming your contribution."],
      resume_draft: "Added a GitHub Actions workflow to run project tests automatically on pull requests."
    },
    {
      priority: 3,
      action_type: "strengthen",
      title: "Strengthen RAG",
      time_estimate: "1-3 hours",
      why: "This is a focused gap, not a reason to start over.",
      steps: ["Index three local project notes.", "Add a small retrieval endpoint and document its limits."],
      resume_draft: null
    }
  ]
};
