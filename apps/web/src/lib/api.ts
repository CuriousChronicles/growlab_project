import type { AnalyseRequest, AnalysisResponse } from "../types/analysis";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function analyseBridge(request: AnalyseRequest): Promise<AnalysisResponse> {
  const endpoint = request.use_demo_data ? "/demo-analysis" : "/analyse";
  const githubUrl = request.github_repo_url?.trim() || null;
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, github_repo_url: githubUrl })
  });

  if (!response.ok) {
    throw new Error("GradBridge could not complete the analysis.");
  }

  return response.json();
}
