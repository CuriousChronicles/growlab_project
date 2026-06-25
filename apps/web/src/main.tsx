import React, { useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import {
  CartesianGrid,
  Label,
  ReferenceArea,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  ArrowDown,
  ArrowUp,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Copy,
  FileText,
  Github,
  Loader2,
  MapPin,
  Sparkles,
  Target,
  Upload
} from "lucide-react";
import { analyseBridge } from "./lib/api";
import type { AnalyseRequest, AnalysisResponse, BridgePlanItem, CandidateEvidence, LocationId, PathwayId, SkillAnalysis, SkillStatus } from "./types/analysis";
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
const MAX_CARD_EVIDENCE_CHARS = 120;
const statusBandPositions: Record<SkillStatus, number> = {
  no_proof_yet: 0,
  adjacent_proof: 1,
  hidden_proof: 2,
  strong_proof: 3
};
const statusColours: Record<SkillStatus, string> = {
  no_proof_yet: "#dc2626",
  adjacent_proof: "#d97706",
  hidden_proof: "#2563eb",
  strong_proof: "#059669"
};
const strengthBandLabels = ["No proof", "Adjacent", "Hidden", "Strong"];
const defaultXDomain: [number, number] = [-0.5, 3.5];
const chartHeight = 420;
const chartMargin = { top: 18, right: 24, bottom: 20, left: 18 };

type SkillScatterPoint = SkillAnalysis & {
  x: number;
  y: number;
  radius: number;
};

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
        {screen === "dashboard" && analysis ? <Dashboard analysis={analysis} targetPathwayId={request.target_pathway} onBack={() => setScreen("intake")} onBridge={() => setScreen("bridge")} /> : null}
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

function Dashboard({ analysis, targetPathwayId, onBack, onBridge }: { analysis: AnalysisResponse; targetPathwayId: PathwayId; onBack: () => void; onBridge: () => void }) {
  const headline = useMemo(() => makeHeadline(analysis, targetPathwayId), [analysis, targetPathwayId]);
  const grouped = useMemo(() => statusOrder.map((status) => ({
    status,
    skills: analysis.skills.filter((skill) => skill.status === status)
  })), [analysis.skills]);
  const topSkills = analysis.skills.slice(0, 8);
  const maxSkillListingCount = Math.max(...topSkills.map((skill) => skill.listing_count), 1);

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

      {analysis.resume_text ? <ResumeUsed resumeText={analysis.resume_text} skills={analysis.skills} /> : null}

      <div className="skills-insight-grid">
        <section className="card">
          <div className="section-heading">
            <h3>Top In-Demand Skills</h3>
            <p>Raw counts from the selected market snapshot.</p>
          </div>
          <div className="skill-bars">
            {topSkills.map((skill) => <SkillDemandBar key={skill.name} skill={skill} maxCount={maxSkillListingCount} />)}
          </div>
        </section>

        <SkillScatterPlot skills={analysis.skills} />
      </div>
    </section>
  );
}

function SkillScatterPlot({ skills }: { skills: SkillAnalysis[] }) {
  const [selectedSkill, setSelectedSkill] = useState<SkillAnalysis | null>(null);
  const chartWrapperRef = useRef<HTMLDivElement | null>(null);
  const [chartWidth, setChartWidth] = useState(720);
  const maxDemand = Math.max(...skills.map((skill) => skill.demand_score), 0);
  const yMax = Math.min(100, Math.max(10, Math.ceil((maxDemand + 5) / 10) * 10));
  const defaultYDomain = useMemo<[number, number]>(() => [0, yMax], [yMax]);
  const [xDomain, setXDomain] = useState<[number, number]>(defaultXDomain);
  const [yDomain, setYDomain] = useState<[number, number]>(defaultYDomain);
  const [zoomSelection, setZoomSelection] = useState<{
    start: { x: number; y: number };
    end: { x: number; y: number };
  } | null>(null);
  const points = useMemo(() => {
    const sizes = skills.map((skill) => skill.employer_count);
    const maxSize = Math.max(...sizes, 0);

    return skills.map((skill) => ({
      ...skill,
      x: statusBandPositions[skill.status] + getSkillJitter(skill.name),
      y: skill.demand_score,
      radius: 4 + (maxSize ? (skill.employer_count / maxSize) * 6 : 0)
    }));
  }, [skills]);
  const selectionBounds = zoomSelection ? getSelectionBounds(zoomSelection) : null;
  const hasZoom = xDomain[0] !== defaultXDomain[0] || xDomain[1] !== defaultXDomain[1] || yDomain[0] !== defaultYDomain[0] || yDomain[1] !== defaultYDomain[1];

  useEffect(() => {
    const wrapper = chartWrapperRef.current;
    if (!wrapper) return;

    const resizeObserver = new ResizeObserver(([entry]) => {
      setChartWidth(Math.max(320, Math.floor(entry.contentRect.width)));
    });
    resizeObserver.observe(wrapper);
    return () => resizeObserver.disconnect();
  }, []);

  useEffect(() => {
    setYDomain(defaultYDomain);
  }, [defaultYDomain]);

  function resetZoom() {
    setXDomain(defaultXDomain);
    setYDomain(defaultYDomain);
    setZoomSelection(null);
  }

  function panChart(xRatio: number, yRatio: number) {
    setXDomain((current) => shiftDomain(current, defaultXDomain, xRatio));
    setYDomain((current) => shiftDomain(current, defaultYDomain, yRatio));
  }

  function startZoom(event: unknown) {
    const point = getChartDomainPoint(event, chartWidth, xDomain, yDomain);
    if (!point) return;
    setZoomSelection({ start: point, end: point });
  }

  function updateZoom(event: unknown) {
    if (!zoomSelection) return;
    const point = getChartDomainPoint(event, chartWidth, xDomain, yDomain);
    if (!point) return;
    setZoomSelection((current) => current ? { ...current, end: point } : current);
  }

  function finishZoom() {
    if (!zoomSelection) return;

    const bounds = getSelectionBounds(zoomSelection);
    const hasArea = Math.abs(bounds.x2 - bounds.x1) > 0.08 && Math.abs(bounds.y2 - bounds.y1) > Math.max(1, (yDomain[1] - yDomain[0]) * 0.04);
    if (hasArea) {
      setXDomain([bounds.x1, bounds.x2]);
      setYDomain([bounds.y1, bounds.y2]);
    }
    setZoomSelection(null);
  }

  return (
    <section className="card scatter-card">
      <div className="section-heading">
        <div>
          <h3>Skill gap map</h3>
          <p>Each dot is one skill - higher means more market demand, further right means stronger proof.</p>
        </div>
        <div className="chart-controls" aria-label="Chart zoom and pan controls">
          <button className="secondary-button compact-button icon-button" type="button" onClick={() => panChart(-0.2, 0)} disabled={!hasZoom} aria-label="Pan chart left"><ArrowLeft size={16} /></button>
          <button className="secondary-button compact-button icon-button" type="button" onClick={() => panChart(0.2, 0)} disabled={!hasZoom} aria-label="Pan chart right"><ArrowRight size={16} /></button>
          <button className="secondary-button compact-button icon-button" type="button" onClick={() => panChart(0, 0.2)} disabled={!hasZoom} aria-label="Pan chart up"><ArrowUp size={16} /></button>
          <button className="secondary-button compact-button icon-button" type="button" onClick={() => panChart(0, -0.2)} disabled={!hasZoom} aria-label="Pan chart down"><ArrowDown size={16} /></button>
          <button className="secondary-button compact-button" type="button" onClick={resetZoom} disabled={!hasZoom}>Reset zoom</button>
        </div>
      </div>
      <div className="scatter-chart-wrap" ref={chartWrapperRef}>
        <ScatterChart
          width={chartWidth}
          height={chartHeight}
          margin={chartMargin}
          onMouseDown={startZoom}
          onMouseMove={updateZoom}
          onMouseUp={finishZoom}
          onMouseLeave={() => setZoomSelection(null)}
        >
          <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <ReferenceArea x1={-0.5} x2={1.5} y1={50} y2={100} fill="rgba(220,38,38,0.06)" stroke="none">
            <Label value="High demand · gap to close" position="insideTopLeft" fill="#991b1b" fontSize={12} fontWeight={800} />
          </ReferenceArea>
          <ReferenceArea x1={1.5} x2={3.5} y1={50} y2={100} fill="rgba(5,150,105,0.06)" stroke="none">
            <Label value="High demand · proven" position="insideTopRight" fill="#047857" fontSize={12} fontWeight={800} />
          </ReferenceArea>
          <XAxis
            dataKey="x"
            type="number"
            domain={xDomain}
            ticks={[0, 1, 2, 3]}
            tickFormatter={(value) => strengthBandLabels[Number(value)] ?? ""}
            tickLine={false}
          />
          <YAxis
            dataKey="y"
            type="number"
            domain={yDomain}
            tickLine={false}
            label={{ value: "Market demand (% of roles)", angle: -90, position: "insideLeft", offset: 0 }}
          />
          <Tooltip content={<SkillScatterTooltip />} cursor={{ stroke: "#94a3b8", strokeDasharray: "3 3" }} />
          <Scatter
            data={points}
            isAnimationActive={false}
            shape={(props: unknown) => <SkillScatterDot {...(props as SkillScatterDotProps)} onClick={setSelectedSkill} />}
          />
          {selectionBounds ? (
            <ReferenceArea
              x1={selectionBounds.x1}
              x2={selectionBounds.x2}
              y1={selectionBounds.y1}
              y2={selectionBounds.y2}
              fill="rgba(37, 99, 235, 0.08)"
              stroke="#2563eb"
              strokeOpacity={0.45}
            />
          ) : null}
        </ScatterChart>
      </div>
      <SkillEvidenceDrawer skill={selectedSkill} onClose={() => setSelectedSkill(null)} />
    </section>
  );
}

function getSkillJitter(name: string) {
  const hash = name.split("").reduce((acc, character) => acc + character.charCodeAt(0), 0);
  return ((hash % 101) / 100) * 0.8 - 0.4;
}

function getSelectionBounds(selection: { start: { x: number; y: number }; end: { x: number; y: number } }) {
  return {
    x1: Math.min(selection.start.x, selection.end.x),
    x2: Math.max(selection.start.x, selection.end.x),
    y1: Math.min(selection.start.y, selection.end.y),
    y2: Math.max(selection.start.y, selection.end.y)
  };
}

function getChartDomainPoint(event: unknown, width: number, xDomain: [number, number], yDomain: [number, number]) {
  const chartEvent = event as { chartX?: number; chartY?: number } | null;
  if (!chartEvent || typeof chartEvent.chartX !== "number" || typeof chartEvent.chartY !== "number") return null;

  const plotWidth = width - chartMargin.left - chartMargin.right;
  const plotHeight = chartHeight - chartMargin.top - chartMargin.bottom;
  const plotX = Math.min(Math.max(chartEvent.chartX - chartMargin.left, 0), plotWidth);
  const plotY = Math.min(Math.max(chartEvent.chartY - chartMargin.top, 0), plotHeight);

  return {
    x: xDomain[0] + (plotX / plotWidth) * (xDomain[1] - xDomain[0]),
    y: yDomain[1] - (plotY / plotHeight) * (yDomain[1] - yDomain[0])
  };
}

function shiftDomain(current: [number, number], bounds: [number, number], ratio: number): [number, number] {
  const span = current[1] - current[0];
  const shift = span * ratio;
  let nextStart = current[0] + shift;
  let nextEnd = current[1] + shift;

  if (nextStart < bounds[0]) {
    nextStart = bounds[0];
    nextEnd = bounds[0] + span;
  }

  if (nextEnd > bounds[1]) {
    nextEnd = bounds[1];
    nextStart = bounds[1] - span;
  }

  return [nextStart, nextEnd];
}

type SkillScatterDotProps = {
  cx?: number;
  cy?: number;
  payload?: SkillScatterPoint;
  onClick: (skill: SkillAnalysis) => void;
};

function SkillScatterDot({ cx = 0, cy = 0, payload, onClick }: SkillScatterDotProps) {
  if (!payload) return null;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={payload.radius}
      fill={statusColours[payload.status]}
      stroke="#ffffff"
      strokeWidth={2}
      style={{ cursor: "pointer" }}
      tabIndex={0}
      role="button"
      aria-label={`Open evidence for ${payload.name}`}
      onClick={() => onClick(payload)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick(payload);
        }
      }}
    />
  );
}

function SkillScatterTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: SkillScatterPoint }> }) {
  const skill = payload?.[0]?.payload;
  if (!active || !skill) return null;

  return (
    <div className="scatter-tooltip">
      <strong>{skill.name}</strong>
      <span>{statusLabels[skill.status]}</span>
      <span>{skill.demand_score}% of roles</span>
      <span>{skill.listing_count} / {skill.total_listings} roles</span>
      <span>{skill.employer_count} employers</span>
    </div>
  );
}

function SkillEvidenceDrawer({ skill, onClose }: { skill: SkillAnalysis | null; onClose: () => void }) {
  if (!skill) return null;

  return ReactDOM.createPortal(
    <>
      <div className="skill-drawer-overlay" onClick={onClose} />
      <aside className="skill-drawer" aria-label={`${skill.name} evidence drawer`}>
        <div className="skill-drawer-header">
          <div>
            <p className="eyebrow">{statusLabels[skill.status]}</p>
            <h3>{skill.name}</h3>
          </div>
          <button className="skill-drawer-close" type="button" onClick={onClose} aria-label="Close evidence drawer">✕</button>
        </div>
        <div className="evidence-item-body">
          <span className="evidence-item-label">
            {skill.market_label} - {skill.confidence} confidence
          </span>
          <CandidateEvidenceList skill={skill} showFull />
        </div>
      </aside>
    </>,
    document.body
  );
}

function ResumeUsed({ resumeText, skills }: { resumeText: string; skills: SkillAnalysis[] }) {
  const firstHidden = skills.find((skill) => skill.status === "hidden_proof");
  const note = firstHidden
    ? `${firstHidden.name} is absent here; hidden proof comes from project evidence.`
    : null;

  return (
    <details className="card resume-used">
      <summary>
        <span><FileText size={18} /> Resume used</span>
        {note ? <span className="resume-note">{note}</span> : null}
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

function SkillDemandBar({ skill, maxCount }: { skill: SkillAnalysis; maxCount: number }) {
  const percent = Math.round((skill.listing_count / maxCount) * 100);
  return (
    <article className="skill-demand">
      <div>
        <strong>{skill.name}</strong>
        <span>{skill.listing_count} of {skill.total_listings} roles · {skill.employer_count} employers</span>
      </div>
      <div className="bar-track" aria-hidden="true">
        <span style={{ width: `${Math.min(percent, 100)}%` }} />
      </div>
    </article>
  );
}

function SkillEvidence({ skill }: { skill: SkillAnalysis }) {
  const topSources = [
    ...new Set(
      skill.candidate_evidence.slice(0, 2).map((e) => formatEvidenceSource(e.source))
    )
  ];

  return (
    <details className="evidence-item">
      <summary className="evidence-item-summary">
        <strong className="evidence-item-name">{skill.name}</strong>
        <span className="evidence-item-sources">
          {topSources.length
            ? topSources.map((src) => <span key={src} className="source-pill">{src}</span>)
            : <span className="source-pill">No evidence yet</span>}
        </span>
      </summary>
      <div className="evidence-item-body">
        <span className="evidence-item-label">
          {skill.market_label} — {skill.confidence} confidence
        </span>
        <CandidateEvidenceList skill={skill} />
      </div>
    </details>
  );
}

function PlanCard({ item, skills }: { item: BridgePlanItem; skills: SkillAnalysis[] }) {
  const matchingSkill = skills.find((skill) => item.title.toLowerCase().includes(skill.name.toLowerCase()));
  const actionLabel = item.action_type[0].toUpperCase() + item.action_type.slice(1);
  const [copied, setCopied] = useState(false);
  const skillName = matchingSkill?.name ?? item.title.replace(/^(Surface|Strengthen|Build proof for)\s+/, "");
  const marketSignal = matchingSkill?.market_evidence ?? item.why;
  const confidence = matchingSkill?.confidence ?? "medium";
  const recommendedAction = matchingSkill?.recommended_action ?? item.steps[0];
  const resumeDraft = item.resume_draft?.trim();
  const statusClass = matchingSkill ? `status-${matchingSkill.status}` : "";

  async function copyResumeDraft() {
    if (!resumeDraft) return;

    try {
      await navigator.clipboard.writeText(resumeDraft);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className={`card plan-card ${item.action_type} ${statusClass}`}>
      <div className="plan-card-header">
        <div>
          <p className="eyebrow">{actionLabel} - {item.time_estimate}</p>
          <h3>{item.title}</h3>
        </div>
        <span className="priority">{item.priority}</span>
      </div>

      <div className="plan-card-meta" aria-label="Bridge plan context">
        <span>{skillName}</span>
        <span>{confidence} confidence</span>
      </div>

      {resumeDraft ? (
        <div className="resume-draft resume-draft-hero">
          <div className="resume-draft-label">
            <span>{item.resume_draft_ai_refined ? "AI-refined resume bullet" : "Resume bullet"}</span>
            <button className="copy-button" type="button" onClick={copyResumeDraft} aria-label="Copy resume bullet">
              {copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p>{resumeDraft}</p>
        </div>
      ) : <div className="resume-draft empty-draft">No resume draft yet. Build proof first, then write the claim.</div>}

      <p className="market-signal"><strong>Market signal:</strong> {marketSignal}</p>
      <p className="recommended-action"><strong>Recommended action:</strong> {recommendedAction}</p>

      {matchingSkill ? (
        <details className="candidate-evidence">
          <summary>
            <span>Candidate evidence found</span>
            <small><CandidateEvidencePreview skill={matchingSkill} maxLength={MAX_CARD_EVIDENCE_CHARS} /></small>
          </summary>
          <CandidateEvidenceList skill={matchingSkill} showFull />
        </details>
      ) : (
        <div className="candidate-evidence-empty">No linked skill evidence was returned for this action.</div>
      )}

    </article>
  );
}

function makeHeadline(analysis: AnalysisResponse, targetPathwayId: PathwayId) {
  const targetRole = analysis.role_pathways.find((r) => r.id === targetPathwayId);
  const hiddenCount = analysis.skills.filter((skill) => skill.status === "hidden_proof").length;
  if (!targetRole) return "Your evidence has been mapped against the selected market snapshot.";
  if (hiddenCount > 0) return `You have ${hiddenCount} proof point${hiddenCount === 1 ? "" : "s"} to surface for ${targetRole.label} roles.`;
  return `Here's how to build your case for ${targetRole.label} roles.`;
}

function CandidateEvidencePreview({ skill, maxLength }: { skill: SkillAnalysis; maxLength: number }) {
  if (!skill.candidate_evidence.length) return <>No direct candidate evidence found yet.</>;
  const preview = skill.candidate_evidence
    .map((evidence) => getRelevantEvidenceText(evidence, skill.name))
    .join(" ");
  return <>{truncateEvidence(preview, maxLength)}</>;
}

function CandidateEvidenceList({ skill, showFull = false }: { skill: SkillAnalysis; showFull?: boolean }) {
  if (!skill.candidate_evidence.length) return <p className="muted">No direct candidate evidence found yet.</p>;

  return (
    <div className="candidate-evidence-list">
      {skill.candidate_evidence.map((evidence, index) => {
        const relevantEvidence = getRelevantEvidenceText(evidence, skill.name);
        const fullEvidence = cleanEvidenceExcerpt(evidence.excerpt);
        const hasMore = relevantEvidence !== fullEvidence;

        return (
          <div className="candidate-evidence-row" key={`${evidence.source}-${index}`}>
            <span className="source-pill">{formatEvidenceSource(evidence.source)}</span>
            <p>{highlightMatch(relevantEvidence, skill.name)}</p>
            {showFull && hasMore ? <p className="candidate-evidence-full">{fullEvidence}</p> : null}
            {!showFull && hasMore ? (
              <details className="inline-evidence-more">
                <summary>Show more</summary>
                <p>{fullEvidence}</p>
              </details>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function getRelevantEvidenceText(evidence: CandidateEvidence, skillName: string) {
  const clean = cleanEvidenceExcerpt(evidence.excerpt);
  const commaItems = clean.split(",").map((item) => item.trim()).filter(Boolean);

  if (commaItems.length >= 5) {
    const matchingIndex = commaItems.findIndex((item) => containsSkill(item, skillName));
    if (matchingIndex >= 0) {
      const start = Math.max(0, matchingIndex - 1);
      const end = Math.min(commaItems.length, matchingIndex + 2);
      const context = commaItems.slice(start, end).join(", ");
      return `${start > 0 ? "... " : ""}${context}${end < commaItems.length ? " ..." : ""}`;
    }
  }

  const matchIndex = clean.toLowerCase().indexOf(skillName.toLowerCase());
  if (matchIndex < 0) return truncateEvidence(clean, MAX_RENDERED_EVIDENCE_CHARS);

  const contextRadius = Math.floor((MAX_CARD_EVIDENCE_CHARS - skillName.length) / 2);
  const start = Math.max(0, matchIndex - contextRadius);
  const end = Math.min(clean.length, matchIndex + skillName.length + contextRadius);
  const excerpt = `${start > 0 ? "... " : ""}${clean.slice(start, end).trim()}${end < clean.length ? " ..." : ""}`;
  return excerpt.replace(/\s+/g, " ").trim();
}

function cleanEvidenceExcerpt(value: string) {
  return value.replace(/^Skills:\s*/i, "").replace(/\s+/g, " ").trim();
}

function formatEvidenceSource(source: string) {
  if (source.startsWith("repository:")) {
    const path = source.replace("repository:", "").trim();
    return path ? `Repository · ${path}` : "Repository";
  }

  const labels: Record<string, string> = {
    experience: "Experience",
    project: "Project",
    resume: "Resume",
    resume_summary: "Resume summary",
    skills_section: "Skills section"
  };

  return labels[source] ?? source.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function containsSkill(value: string, skillName: string) {
  const escaped = skillName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|\\W)${escaped}(\\W|$)`, "i").test(value);
}

function highlightMatch(value: string, skillName: string) {
  const lowerValue = value.toLowerCase();
  const lowerSkill = skillName.toLowerCase();
  const matchIndex = lowerValue.indexOf(lowerSkill);

  if (matchIndex < 0) return value;

  return (
    <>
      {value.slice(0, matchIndex)}
      <mark>{value.slice(matchIndex, matchIndex + skillName.length)}</mark>
      {value.slice(matchIndex + skillName.length)}
    </>
  );
}

function truncateEvidence(value: string, maxLength: number) {
  const clean = value.replace(/\s+/g, " ").trim();
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength - 3).trim()}...`;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

createRoot(document.getElementById("root")!).render(<App />);
