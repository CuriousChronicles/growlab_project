import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertCircle, ArrowRight, BriefcaseBusiness, CheckCircle2, FileText, Github, Loader2, MapPin, RefreshCw, ShieldCheck, Sparkles, Target, Upload } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { z } from "zod";
import { analyseBridge } from "./lib/api";
import { demoAnalysis } from "./lib/demoAnalysis";
import type { AnalyseRequest, AnalysisResponse, LocationId, PathwayId, SkillAnalysis, SkillStatus } from "./types/analysis";
import "./styles.css";

const requestSchema = z.object({
  resume_text: z.string(),
  target_pathway: z.enum(["ai_automation", "software_fullstack", "embedded_firmware"]),
  location: z.enum(["auckland", "new_zealand", "remote"]),
  github_repo_url: z.string().url().optional().or(z.literal("")),
  use_demo_data: z.boolean()
});

const pathwayOptions: Array<{ id: PathwayId; label: string }> = [
  { id: "ai_automation", label: "AI & Automation" },
  { id: "software_fullstack", label: "Graduate Software / Full-Stack" },
  { id: "embedded_firmware", label: "Embedded / Firmware" }
];

const locationOptions: Array<{ id: LocationId; label: string }> = [
  { id: "auckland", label: "Auckland" },
  { id: "new_zealand", label: "New Zealand" },
  { id: "remote", label: "Remote-friendly" }
];

const statusLabels: Record<SkillStatus, string> = {
  strong_proof: "Strong proof",
  hidden_proof: "Hidden proof",
  adjacent_proof: "Adjacent proof",
  no_proof_yet: "No proof yet"
};

const statusOrder: SkillStatus[] = ["strong_proof", "hidden_proof", "adjacent_proof", "no_proof_yet"];

function App() {
  const [request, setRequest] = useState<AnalyseRequest>({
    resume_text: "",
    target_pathway: "ai_automation",
    location: "auckland",
    github_repo_url: "",
    use_demo_data: false
  });
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function runAnalysis(useDemo: boolean) {
    setIsLoading(true);
    setError("");
    const payload = { ...request, use_demo_data: useDemo };
    const parsed = requestSchema.safeParse(payload);
    if (!parsed.success) {
      setError("Add a valid public GitHub repository URL or leave it blank.");
      setIsLoading(false);
      return;
    }

    try {
      const result = await analyseBridge(parsed.data as AnalyseRequest);
      setAnalysis(result);
    } catch {
      if (useDemo) {
        setAnalysis(demoAnalysis);
      } else {
        setError("The API is not reachable. Try the demo profile, which works offline.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <div className="brand">
          <span className="logo"><ShieldCheck size={22} /></span>
          <div>
            <strong>GradBridge</strong>
            <span>Evidence-led graduate role readiness</span>
          </div>
        </div>
        <button className="ghost-button" onClick={() => runAnalysis(true)} disabled={isLoading}>
          <Sparkles size={16} /> Try demo profile
        </button>
      </header>

      <section className="container">
        <Intake request={request} setRequest={setRequest} onAnalyse={() => runAnalysis(false)} onDemo={() => runAnalysis(true)} isLoading={isLoading} error={error} />
        {analysis ? <Dashboard analysis={analysis} /> : <EmptyState />}
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
  return (
    <section className="intake">
      <div className="intro">
        <p className="eyebrow"><Target size={16} /> Final-year and entry-level technical graduates</p>
        <h1>Find the roles you are closest to now, then close the smallest honest gaps.</h1>
        <p>Paste resume text, choose a pathway and location, then GradBridge maps market signals to evidence you can actually stand behind.</p>
      </div>

      <div className="panel">
        <label>
          <span><FileText size={16} /> Resume text</span>
          <textarea value={request.resume_text} onChange={(event) => setRequest((current) => ({ ...current, resume_text: event.target.value }))} placeholder="Paste resume text here. PDF upload is represented for the MVP; pasted text keeps the local demo dependable." />
        </label>
        <div className="upload-note"><Upload size={16} /> PDF upload placeholder: backend includes pypdf dependency for the next implementation pass.</div>

        <div className="form-grid">
          <label>
            <span><BriefcaseBusiness size={16} /> Target pathway</span>
            <select value={request.target_pathway} onChange={(event) => setRequest((current) => ({ ...current, target_pathway: event.target.value as PathwayId }))}>
              {pathwayOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
          <label>
            <span><MapPin size={16} /> Location</span>
            <select value={request.location} onChange={(event) => setRequest((current) => ({ ...current, location: event.target.value as LocationId }))}>
              {locationOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
          </label>
        </div>

        <label>
          <span><Github size={16} /> Optional public GitHub repository URL</span>
          <input value={request.github_repo_url} onChange={(event) => setRequest((current) => ({ ...current, github_repo_url: event.target.value }))} placeholder="https://github.com/you/project" />
        </label>

        {error ? <div className="error"><AlertCircle size={16} /> {error}</div> : null}

        <div className="actions">
          <button className="primary-button" onClick={onAnalyse} disabled={isLoading}>
            {isLoading ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />} Analyse my bridge
          </button>
          <button className="secondary-button" onClick={onDemo} disabled={isLoading}>
            <Sparkles size={18} /> Try demo profile
          </button>
        </div>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="empty">
      <h2>Demo-ready evidence, not career astrology.</h2>
      <p>Run the demo profile to see Python, APIs, databases, embedded work, and project ownership translated into a practical Bridge Plan.</p>
    </section>
  );
}

function Dashboard({ analysis }: { analysis: AnalysisResponse }) {
  const chartData = analysis.skills.slice(0, 8).map((skill) => ({ name: skill.name, listings: skill.listing_count, required: skill.required_count }));
  const grouped = useMemo(() => {
    return statusOrder.map((status) => ({
      status,
      skills: analysis.skills.filter((skill) => skill.status === status)
    }));
  }, [analysis.skills]);

  return (
    <section className="dashboard">
      <div className="snapshot">
        <div>
          <p className="eyebrow"><RefreshCw size={16} /> Market snapshot</p>
          <h2>{analysis.headline}</h2>
          <p>{analysis.market_snapshot.listing_count} relevant roles analysed in {analysis.market_snapshot.location}; {analysis.market_snapshot.distinct_employers} distinct employers. Captured {new Date(analysis.market_snapshot.captured_at).toLocaleDateString()} from {analysis.market_snapshot.sources.join(", ")}.</p>
        </div>
      </div>

      <div className="role-grid">
        {analysis.role_pathways.map((role) => (
          <article className="card role-card" key={role.id}>
            <span className="demand">{role.market_demand} market demand</span>
            <h3>{role.label}</h3>
            <strong>{role.evidence_coverage}% evidence coverage</strong>
            <p>{role.summary}</p>
          </article>
        ))}
      </div>

      <div className="two-column">
        <section className="card">
          <h3>Top In-Demand Skills</h3>
          <div className="chart">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid stroke="#E2E8F0" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={92} />
                <Tooltip />
                <Bar dataKey="listings" name="Listings" fill="#2563EB" radius={[0, 6, 6, 0]} />
                <Bar dataKey="required" name="Required" fill="#059669" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card">
          <h3>Skill Evidence Map</h3>
          <div className="status-list">
            {grouped.map((group) => (
              <div key={group.status} className={`status-block ${group.status}`}>
                <div className="status-heading">
                  <span>{statusLabels[group.status]}</span>
                  <strong>{group.skills.length}</strong>
                </div>
                <div className="chips">
                  {group.skills.length ? group.skills.map((skill) => <span key={skill.name}>{skill.name}</span>) : <em>No top skills in this group.</em>}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="card skill-table">
        <h3>Market Signals And Evidence</h3>
        {analysis.skills.slice(0, 10).map((skill) => <SkillRow key={skill.name} skill={skill} />)}
      </section>

      <section className="bridge-plan">
        <div className="section-heading">
          <p className="eyebrow"><CheckCircle2 size={16} /> Bridge Plan</p>
          <h2>Three highest-value next actions</h2>
        </div>
        <div className="plan-grid">
          {analysis.bridge_plan.map((item) => (
            <article className={`card plan-card ${item.action_type}`} key={`${item.priority}-${item.skill_name}`}>
              <span className="priority">{item.priority}</span>
              <p className="eyebrow">{item.action_type} · {item.time_estimate}</p>
              <h3>{item.title}</h3>
              <p><strong>Market signal:</strong> {item.market_signal}</p>
              <p><strong>Evidence found:</strong> {item.candidate_evidence_found}</p>
              <p><strong>Confidence:</strong> {item.confidence}</p>
              <p>{item.recommended_action}</p>
              <ul>
                {item.steps.map((step) => <li key={step}>{step}</li>)}
              </ul>
              {item.resume_draft ? <div className="resume-draft">{item.resume_draft}</div> : null}
              <p className="why">{item.why}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="methodology">
        <h3>Transparent Methodology</h3>
        {analysis.methodology.map((line) => <p key={line}>{line}</p>)}
      </section>
    </section>
  );
}

function SkillRow({ skill }: { skill: SkillAnalysis }) {
  return (
    <article className="skill-row">
      <div>
        <h4>{skill.name}</h4>
        <span className={`badge ${skill.status}`}>{statusLabels[skill.status]}</span>
      </div>
      <p>{skill.market_evidence}</p>
      <p>{skill.candidate_evidence[0]?.excerpt ?? "No direct candidate evidence found yet."}</p>
      <p>{skill.recommended_action}</p>
    </article>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
