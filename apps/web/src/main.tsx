import React, { useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  FileText,
  Github,
  Loader2,
  MapPin,
  Sparkles,
  Target,
  Upload
} from "lucide-react";
import { analyseBridge } from "./lib/api";
import type { AnalyseRequest, AnalysisResponse, BridgePlanItem, LocationId, PathwayId, SkillAnalysis, SkillStatus } from "./types/analysis";
import "./styles.css";

type Screen = "intake" | "dashboard" | "bridge";

const pathwayOptions: Array<{ id: PathwayId; label: string }> = [
  { id: "ai_automation", label: "AI & Automation" },
  { id: "software_fullstack", label: "Graduate Software" },
  { id: "embedded_firmware", label: "Embedded" }
];

const locationOptions: Array<{ id: LocationId; label: string }> = [
  { id: "auckland", label: "Auckland" },
  { id: "new_zealand", label: "New Zealand" },
  { id: "remote", label: "Remote" }
];

const statusLabels: Record<SkillStatus, string> = {
  strong_proof: "Strong proof",
  hidden_proof: "Hidden proof",
  adjacent_proof: "Adjacent proof",
  no_proof_yet: "No proof yet"
};

const statusDescriptions: Record<SkillStatus, string> = {
  strong_proof: "Clear, resume-ready evidence.",
  hidden_proof: "Evidence exists but needs to be surfaced.",
  adjacent_proof: "Nearby evidence that can be strengthened.",
  no_proof_yet: "Worth building only if the market signal justifies it."
};

const statusOrder: SkillStatus[] = ["strong_proof", "hidden_proof", "adjacent_proof", "no_proof_yet"];
const MAX_RENDERED_EVIDENCE_CHARS = 200;

function App() {
  const [request, setRequest] = useState<AnalyseRequest>({
    resume_text: "",
    target_pathway: "ai_automation",
    location: "auckland",
    github_repo_url: "",
    use_demo_data: false
  });
  const [screen, setScreen] = useState<Screen>("intake");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function runAnalysis(useDemo: boolean) {
    setIsLoading(true);
    setError("");

    try {
      const result = await analyseBridge({ ...request, use_demo_data: useDemo });
      setAnalysis(result);
      if (useDemo && result.resume_text) {
        setRequest((current) => ({ ...current, resume_text: result.resume_text ?? "" }));
      }
      setScreen("dashboard");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "GradBridge could not complete the analysis.";
      setError(useDemo ? `Demo analysis failed: ${message}` : `Analysis failed: ${message}`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <button className="brand" type="button" onClick={() => setScreen("intake")}>
          <span className="logo"><Target size={22} /></span>
          <span>
            <strong>GradBridge</strong>
            <small>Evidence-led graduate role readiness</small>
          </span>
        </button>
        <nav aria-label="Primary">
          <button className={screen === "intake" ? "nav-active" : ""} type="button" onClick={() => setScreen("intake")}>Intake</button>
          <button className={screen === "dashboard" ? "nav-active" : ""} type="button" onClick={() => analysis && setScreen("dashboard")} disabled={!analysis}>Readiness</button>
          <button className={screen === "bridge" ? "nav-active" : ""} type="button" onClick={() => analysis && setScreen("bridge")} disabled={!analysis}>Bridge Plan</button>
        </nav>
      </header>

      <section className="container">
        {screen === "intake" ? (
          <Intake request={request} setRequest={setRequest} onAnalyse={() => runAnalysis(false)} onDemo={() => runAnalysis(true)} isLoading={isLoading} error={error} />
        ) : null}
        {screen === "dashboard" && analysis ? <Dashboard analysis={analysis} onBack={() => setScreen("intake")} onBridge={() => setScreen("bridge")} /> : null}
        {screen === "bridge" && analysis ? <BridgePlan analysis={analysis} onBack={() => setScreen("dashboard")} /> : null}
      </section>
    </main>
  );
}

function Intake({ request, setRequest, onAnalyse, onDemo, isLoading, error }: {
  request: AnalyseRequest;
  setRequest: React.Dispatch<React.SetStateAction<AnalyseRequest>>;
  onAnalyse: () => void;
  onDemo: () => void;
  isLoading: boolean;
  error: string;
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [fileName, setFileName] = useState("");

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);

    if (file.type.startsWith("text/") || file.name.endsWith(".txt") || file.name.endsWith(".md")) {
      const text = await file.text();
      setRequest((current) => ({ ...current, resume_text: text }));
    }
  }

  return (
    <section className="screen-grid">
      <div className="intro">
        <p className="eyebrow"><Target size={16} /> Fast, practical intake</p>
        <h1>Find the bridge between your proof and the roles hiring now.</h1>
        <p>Paste a resume, upload a text copy, or run the demo profile. GradBridge compares visible candidate evidence with real market signals and keeps the advice plain.</p>
      </div>

      <div className="panel">
        <label>
          <span><FileText size={16} /> Resume paste area</span>
          <textarea value={request.resume_text} onChange={(event) => setRequest((current) => ({ ...current, resume_text: event.target.value }))} placeholder="Paste resume text here." />
        </label>

        <div className="upload-area" role="button" tabIndex={0} onClick={() => fileInputRef.current?.click()} onKeyDown={(event) => event.key === "Enter" && fileInputRef.current?.click()}>
          <Upload size={20} />
          <div>
            <strong>{fileName || "Upload resume file"}</strong>
            <span>Text files are read into the paste area. PDF upload is accepted for the intake flow.</span>
          </div>
          <input ref={fileInputRef} type="file" accept=".pdf,.txt,.md,text/plain,application/pdf" onChange={handleFileUpload} />
        </div>

        <div className="form-grid">
          <ChoiceGroup label="Target pathway" icon={<BriefcaseBusiness size={16} />} value={request.target_pathway} options={pathwayOptions} onChange={(value) => setRequest((current) => ({ ...current, target_pathway: value as PathwayId }))} />
          <ChoiceGroup label="Location" icon={<MapPin size={16} />} value={request.location} options={locationOptions} onChange={(value) => setRequest((current) => ({ ...current, location: value as LocationId }))} />
        </div>

        <label>
          <span><Github size={16} /> Optional public GitHub repository URL</span>
          <input value={request.github_repo_url ?? ""} onChange={(event) => setRequest((current) => ({ ...current, github_repo_url: event.target.value }))} placeholder="https://github.com/you/project" />
        </label>

        {error ? <div className="error"><AlertCircle size={16} /> {error}</div> : null}

        <div className="actions">
          <button className="primary-button" type="button" onClick={onAnalyse} disabled={isLoading}>
            {isLoading ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />} Analyse my bridge
          </button>
          <button className="secondary-button" type="button" onClick={onDemo} disabled={isLoading}>
            {isLoading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />} Try demo profile
          </button>
        </div>
      </div>
    </section>
  );
}

function ChoiceGroup({ label, icon, value, options, onChange }: {
  label: string;
  icon: React.ReactNode;
  value: string;
  options: Array<{ id: string; label: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <fieldset>
      <legend>{icon}{label}</legend>
      <div className="segmented">
        {options.map((option) => (
          <button key={option.id} className={value === option.id ? "selected" : ""} type="button" onClick={() => onChange(option.id)}>
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

function Dashboard({ analysis, onBack, onBridge }: { analysis: AnalysisResponse; onBack: () => void; onBridge: () => void }) {
  const headline = useMemo(() => makeHeadline(analysis), [analysis]);
  const grouped = useMemo(() => statusOrder.map((status) => ({
    status,
    skills: analysis.skills.filter((skill) => skill.status === status)
  })), [analysis.skills]);

  return (
    <section className="dashboard">
      <div className="screen-actions">
        <button className="secondary-button" type="button" onClick={onBack}><ArrowLeft size={18} /> Back to intake</button>
        <button className="primary-button" type="button" onClick={onBridge}><ClipboardList size={18} /> View bridge plan</button>
      </div>

      <section className="snapshot">
        <div>
          <p className="eyebrow"><BarChart3 size={16} /> Market snapshot</p>
          <h2>{headline}</h2>
          <p>{formatDate(analysis.market_snapshot.captured_at)} from {analysis.market_snapshot.sources.join(", ")}</p>
        </div>
        <div className="metadata-grid">
          <Metric label="Relevant roles" value={analysis.market_snapshot.listing_count} />
          <Metric label="Employers" value={analysis.market_snapshot.distinct_employers} />
          <Metric label="Location" value={analysis.market_snapshot.location} />
          <Metric label="Sources" value={analysis.market_snapshot.sources.length} />
        </div>
      </section>

      {analysis.resume_text ? <ResumeUsed resumeText={analysis.resume_text} /> : null}

      <section className="role-grid" aria-label="Role readiness">
        {analysis.role_pathways.map((role) => (
          <article className="card role-card" key={role.id}>
            <span className={`demand demand-${role.market_demand}`}>{role.market_demand} demand</span>
            <h3>{role.label}</h3>
            <strong>{role.evidence_coverage}%</strong>
            <p>{role.summary}</p>
          </article>
        ))}
      </section>

      <section className="card">
        <div className="section-heading">
          <h3>Top In-Demand Skills</h3>
          <p>Raw counts from the selected market snapshot.</p>
        </div>
        <div className="skill-bars">
          {analysis.skills.slice(0, 8).map((skill) => <SkillDemandBar key={skill.name} skill={skill} />)}
        </div>
      </section>

      <section className="status-grid" aria-label="Skill status groups">
        {grouped.map((group) => (
          <article className={`card status-card ${group.status}`} key={group.status}>
            <div className="status-heading">
              <div>
                <h3>{statusLabels[group.status]}</h3>
                <p>{statusDescriptions[group.status]}</p>
              </div>
              <strong>{group.skills.length}</strong>
            </div>
            <div className="evidence-list">
              {group.skills.length ? group.skills.map((skill) => <SkillEvidence key={skill.name} skill={skill} />) : <p className="muted">No top skills in this group.</p>}
            </div>
          </article>
        ))}
      </section>
    </section>
  );
}

function ResumeUsed({ resumeText }: { resumeText: string }) {
  return (
    <details className="card resume-used" open>
      <summary>
        <span><FileText size={18} /> Resume used</span>
        <span className="resume-note">Docker is absent here; hidden proof comes from project evidence.</span>
      </summary>
      <pre>{resumeText}</pre>
    </details>
  );
}

function BridgePlan({ analysis, onBack }: { analysis: AnalysisResponse; onBack: () => void }) {
  return (
    <section className="dashboard">
      <div className="screen-actions">
        <button className="secondary-button" type="button" onClick={onBack}><ArrowLeft size={18} /> Back to readiness</button>
      </div>
      <div className="section-heading bridge-heading">
        <p className="eyebrow"><CheckCircle2 size={16} /> Bridge Plan</p>
        <h2>Three highest-value actions</h2>
        <p>Surface what already exists, strengthen nearby proof, or build a focused artifact only where the evidence is missing.</p>
      </div>
      <div className="plan-grid">
        {analysis.bridge_plan.map((item) => <PlanCard key={`${item.priority}-${item.title}`} item={item} skills={analysis.skills} />)}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SkillDemandBar({ skill }: { skill: SkillAnalysis }) {
  const percent = skill.total_listings ? Math.round((skill.listing_count / skill.total_listings) * 100) : skill.demand_score;
  return (
    <article className="skill-demand">
      <div>
        <strong>{skill.name}</strong>
        <span>{skill.listing_count} listings - {skill.required_count} required - {skill.employer_count} employers</span>
      </div>
      <div className="bar-track" aria-hidden="true">
        <span style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
    </article>
  );
}

function SkillEvidence({ skill }: { skill: SkillAnalysis }) {
  return (
    <article className="evidence-item">
      <div>
        <h4>{skill.name}</h4>
        <span>{skill.market_label} - {skill.confidence} confidence</span>
      </div>
      <p><strong>Market evidence:</strong> {skill.market_evidence}</p>
      <p><strong>Candidate evidence:</strong> {formatCandidateEvidence(skill)}</p>
    </article>
  );
}

function PlanCard({ item, skills }: { item: BridgePlanItem; skills: SkillAnalysis[] }) {
  const matchingSkill = skills.find((skill) => item.title.toLowerCase().includes(skill.name.toLowerCase()));
  const actionLabel = item.action_type[0].toUpperCase() + item.action_type.slice(1);
  const refinedModel = item.resume_draft_refined_by;
  const showAiRefined = item.resume_draft_source === "llm" || item.resume_draft_ai_refined;
  const showTemplateFallback = item.resume_draft_source === "template_llm_fallback";

  return (
    <article className={`card plan-card ${item.action_type}`}>
      <span className="priority">{item.priority}</span>
      <p className="eyebrow">{actionLabel} - {item.time_estimate}</p>
      <h3>{item.title}</h3>
      <p><strong>Skill:</strong> {matchingSkill?.name ?? item.title.replace(/^(Surface|Strengthen|Build proof for)\s+/, "")}</p>
      <p><strong>Market signal:</strong> {matchingSkill?.market_evidence ?? item.why}</p>
      <p><strong>Candidate evidence found:</strong> {matchingSkill ? formatCandidateEvidence(matchingSkill) : "No linked skill evidence was returned for this action."}</p>
      <p><strong>Confidence level:</strong> {matchingSkill?.confidence ?? "medium"}</p>
      <p><strong>Recommended action:</strong> {matchingSkill?.recommended_action ?? item.steps[0]}</p>
      {item.resume_draft ? (
        <div className="resume-draft">
          {showAiRefined ? <span className="ai-refined">AI-refined{refinedModel ? ` (${refinedModel})` : ""}</span> : null}
          {showTemplateFallback ? <span className="template-fallback">(template)</span> : null}
          {item.resume_draft}
        </div>
      ) : <div className="resume-draft empty-draft">No resume draft yet. Build proof first, then write the claim.</div>}
      <p className="why"><strong>Why this matters:</strong> {item.why}</p>
    </article>
  );
}

function makeHeadline(analysis: AnalysisResponse) {
  const topRole = [...analysis.role_pathways].sort((a, b) => b.evidence_coverage - a.evidence_coverage)[0];
  const hiddenCount = analysis.skills.filter((skill) => skill.status === "hidden_proof").length;
  if (!topRole) return "Your evidence has been mapped against the selected market snapshot.";
  if (hiddenCount > 0) return `You are closest to ${topRole.label}, with ${hiddenCount} proof point${hiddenCount === 1 ? "" : "s"} to make more visible.`;
  return `You are closest to ${topRole.label} roles.`;
}

function formatCandidateEvidence(skill: SkillAnalysis) {
  if (!skill.candidate_evidence.length) return "No direct candidate evidence found yet.";
  return truncateEvidence(skill.candidate_evidence.map((evidence) => `${evidence.source}: ${evidence.excerpt}`).join(" "));
}

function truncateEvidence(value: string) {
  const clean = value.replace(/\s+/g, " ").trim();
  if (clean.length <= MAX_RENDERED_EVIDENCE_CHARS) return clean;
  return `${clean.slice(0, MAX_RENDERED_EVIDENCE_CHARS - 3).trim()}...`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

createRoot(document.getElementById("root")!).render(<App />);
