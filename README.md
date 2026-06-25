# growlab_project

## Overview
Help final-year and entry-level technical graduates translate their existing degree, projects, and public portfolio evidence into a clear, honest route toward real roles currently being advertised.

This document is the implementation brief for Codex. Build the MVP described here without adding unrelated features or redesigning the product premise.

---

## 1. The problem

Entry-level candidates face three connected problems:

1. **Resume translation gap**  
   Graduates describe projects from university, while employers use job-specific language and ATS keyword filters.

2. **Market-signal gap**  
   Graduates do not know which skills recur across relevant entry-level roles in their selected location right now.

3. **Evidence gap**  
   A candidate may have adjacent or hidden experience, but their resume and portfolio do not make that evidence visible or credible to a recruiter.

Existing ATS/resume tools primarily score keyword presence. GradBridge should instead answer:

> **Which roles am I closest to now, what proof already exists for the skills employers care about, and what is the smallest honest action I can take to close the most important gaps?**

---

## 2. Product definition

**GradBridge** is a labour-market translator and evidence builder for technical graduates.

A user provides:

- Resume text or a PDF resume
- Target role pathway
- Target location
- Optional public GitHub username or selected public repository URL

GradBridge then:

1. Uses a current/cached job-market snapshot to identify recurring skills for the chosen role pathway.
2. Extracts candidate evidence from the resume and optional public GitHub repository.
3. Labels each important skill as:
   - **Strong proof**
   - **Hidden proof**
   - **Adjacent proof**
   - **No proof yet**
4. Produces a concise, practical “Bridge Plan”:
   - what to surface in the resume;
   - what to strengthen in an existing project;
   - what small proof artifact to build next;
   - honest, reviewable resume bullet suggestions.

### Core promise

> GradBridge does **not** tell people to keyword-stuff or invent experience. It makes existing evidence visible and gives them the smallest credible next step toward a role.

---

## 3. Hackathon MVP scope

Build the complete happy path for **one graduate, one selected role pathway, and a curated/cached job-market snapshot**.

### In scope

- Resume paste and PDF upload
- Three target role pathways:
  1. AI & Automation
  2. Graduate Software / Full-Stack
  3. Embedded / Firmware
- Location selector with:
  - Auckland
  - New Zealand
  - Remote-friendly
- Cached job snapshot containing 25–50 technical entry-level / graduate listings
- Optional Adzuna integration behind a refresh button
- Optional public GitHub repository analysis
- Market skill ranking
- Candidate evidence map
- Role-fit cards
- Bridge Plan with concrete, evidence-grounded actions
- Demo profile / demo mode that works without API keys or internet access

### Explicitly out of scope

What GradBridge does not do in MVP:

- User authentication
- Payments
- Direct job applications
- LinkedIn scraping or Indeed scraping
- Private GitHub repository access
- Full GitHub account scanning by default
- Resume auto-editing or auto-submission
- A generic chatbot
- “Culture fit” scoring
- Employment probability / interview probability claims
- Support for every industry or degree
- A complex recommendation engine based on opaque AI scoring

---

## 4. User journey

### Screen 1 — Intake

Inputs:

- Resume PDF upload
- Target role pathway
- Location
- Optional public GitHub repository URL
- `Analyse my bridge` button
- `Try demo profile` button

The intake should feel quick and non-intimidating.

### Screen 2 — Role Readiness Dashboard

Show:

- Market snapshot metadata:
  - number of relevant roles analysed;
  - selected location;
  - last refreshed timestamp;
  - source attribution.
- A headline insight, such as:
  - “You are closest to AI & Automation roles.”
  - “Your biggest opportunity is making existing project evidence more visible.”
- Three role cards:
  - role pathway;
  - evidence coverage percentage;
  - market demand label;
  - one-sentence explanation.
- Top in-demand skills for the selected pathway.
- Skill status groups:
  - Strong proof
  - Hidden proof
  - Adjacent proof
  - No proof yet

### Screen 3 — Bridge Plan

Show the three highest-value actions:

1. **Surface** — use evidence the candidate already has.
2. **Strengthen** — improve an existing project in 1–3 hours.
3. **Build** — create a focused proof artifact only where no relevant evidence exists.

Each skill/action card must include:

- Skill name
- Market signal / demand level
- Candidate evidence found
- Confidence level
- Recommended action
- Optional honest resume bullet draft
- “Why this matters” explanation

---

## 5. Product principles and safety rules

### Evidence before claims

Never claim a candidate has a skill solely because:

- it appears once in an import statement;
- a repository uses a language;
- an LLM infers it without source evidence;
- it is listed in a generic skills section.

Use evidence levels:

| Evidence source | Confidence |
|---|---|
| Resume/project bullet with concrete contribution | High |
| Candidate-confirmed public repository with relevant code/config | High |
| README/project documentation | Medium |
| Dependency, import, or detected programming language | Low |
| Skill listed without supporting detail | Low |

### Honest recommendations

- Never auto-add a skill to a resume.
- Show a suggested bullet only when it is grounded in resume/project evidence.
- When evidence is weak, say “confirm this” or recommend a smaller proof-building action.
- When no evidence exists, recommend an achievable mini-project or extension—not a misleading resume claim.
- Use **evidence coverage**, never “employability score,” “hireability score,” or “chance of getting hired.”

### Transparent market claims

Do not claim a skill is “the most in-demand skill in New Zealand.”

Use grounded wording such as:

> “Docker appeared in 14 of 37 relevant roles in this selected market snapshot.”

Always display:

- number of roles analysed;
- role pathway;
- location;
- capture/refresh timestamp;
- source attribution.

### LLM role

The LLM is a **translator**, not the source of truth.

Use deterministic logic for:

- skill extraction;
- matching;
- demand scores;
- evidence confidence;
- role coverage scores.

Use an LLM only for:

- explaining evidence;
- normalising language after deterministic extraction;
- generating concise resume bullet drafts;
- proposing targeted, constrained proof-building actions.

LLM outputs should be structured JSON and validated with Pydantic/Zod schemas.

---

## 6. Skill model

Use a small, explicit technical skills taxonomy for the MVP. Do not attempt a giant universal ontology.

Suggested categories:

```ts
export const SKILL_TAXONOMY = {
  languages: [
    "Python", "TypeScript", "JavaScript", "C", "C++", "Java", "SQL"
  ],
  web: [
    "React", "Next.js", "Node.js", "REST APIs", "GraphQL", "HTML/CSS"
  ],
  data_ai: [
    "Pandas", "NumPy", "Machine Learning", "LLMs", "RAG",
    "Data Pipelines", "Data Visualisation"
  ],
  cloud_devops: [
    "Git", "GitHub", "Docker", "CI/CD", "AWS", "Azure", "GCP",
    "Linux", "Testing"
  ],
  databases: [
    "SQLite", "PostgreSQL", "MySQL", "MongoDB", "Redis"
  ],
  embedded: [
    "Embedded C", "STM32", "Microcontrollers", "CAN", "UART",
    "SPI", "I2C", "RTOS", "PCB Design"
  ],
  professional: [
    "Technical Communication", "Project Ownership", "Agile",
    "Stakeholder Communication", "Team Leadership"
  ]
};
```

Include aliases, for example:

```ts
{
  "Postgres": "PostgreSQL",
  "React.js": "React",
  "RESTful APIs": "REST APIs",
  "Github": "GitHub",
  "Docker Compose": "Docker",
  "C/C++": "C++"
}
```

---

## 7. Market-signal logic

### Entry-level filter

A listing should score higher when it contains terms such as:

- graduate
- junior
- entry level
- intern
- associate
- 0–2 years
- recent graduate

A listing should be excluded/down-weighted when it contains:

- senior
- principal
- lead
- manager
- 3+ years required
- 5+ years required

### Demand score (raw counts first)

Design rule: the headline number is always a raw, countable fact, never a synthesised score.
With a 25–50 listing snapshot, any weighted formula is false precision — the weights
cannot be justified ("why is employer-frequency 45% and not 40%?"), and an unjustifiable
number undermines the evidence-led promise. So demand is reported as counts the user (and
a judge) can verify by hand:

For each skill within a selected role pathway and location, compute and store:

```text
listing_count        = relevant listings mentioning the skill
total_listings       = relevant listings in the snapshot
employer_count       = distinct employers mentioning the skill
required_count       = listings where the skill appears as required/essential
```

The primary display is always the raw count, e.g.
"Docker — appeared in 14 of 37 relevant roles (9 listed it as required)."

Sorting uses a simple, explainable two-factor key — not a weighted score with invented
coefficients:

```text
sort skills by (employer_count, required_count) descending
```
Rationale this defends in one sentence: a skill is more in-demand when more distinct
employers ask for it, and among those, when it is required rather than merely preferred.
Both factors are countable and need no magic weights.

Required-vs-preferred is detected from nearby phrases:

- required / essential / must have  → required
- experience with / familiarity      → neutral
- nice to have / preferred / bonus    → preferred

A coarse label may accompany the count (derived from employer_count, with explicit
thresholds documented in docs/product-decisions.md), but the label never replaces the count:
- Core demand — appears across most employers in the snapshot
- Growing signal — appears across several employers
- Differentiator — appears in a minority, useful for standing out
- Low signal — rare in this snapshot

> Never display a skill's demand without also displaying the count it is derived from and
the snapshot size. The number must be auditable.

### Deduplication

The same job can appear across multiple sources. Deduplicate using a normalized key:

```text
normalized company + normalized title + normalized location + posting date
```

Optionally use text similarity on descriptions as a second pass.

---

## 8. Candidate evidence classification

For every important market skill, classify the candidate as follows:

| Status | Definition | Example action |
|---|---|---|
| Strong proof | Direct, relevant evidence in resume/project | Surface prominently in a role-targeted resume |
| Hidden proof | Evidence exists but is not visible in the resume | Add an evidence-backed project bullet |
| Adjacent proof | Related capability exists but does not fully prove the skill | Extend an existing project |
| No proof yet | No relevant evidence found | Build one small proof artifact |

Example:

```text
Skill: Docker
Market signal: Core demand — 14/37 relevant roles

Evidence:
- Dockerfile found in selected repository
- Not mentioned in resume
- README has no setup/deployment instructions

Status: Hidden proof
Confidence: Medium

Action:
Document the containerised setup and only add Docker to the resume if the candidate personally created or maintained it.

Resume draft:
“Containerised a Python job-discovery application with Docker to support reproducible local deployment.”
```

---

## 9. Suggested technical stack

Use a pragmatic monorepo and optimise for speed, clarity, and a polished demo.

### Frontend

- **Vite + React 19** with **TypeScript** — a single-page tool behind an "Analyse" button.
  There is no SSR, SEO, or file-based-routing requirement, so a thin SPA build is the right
  fit and keeps the demo's failure surface small. 
- **React Router** for the 2–3 client routes (intake / dashboard / demo) — only if needed;
  conditional rendering is fine for an MVP this small.
- **Tailwind CSS** for styling
- **shadcn/ui** for accessible base components
- **Lucide React** for icons
- **Recharts** for small, readable charts
- **React Hook Form + Zod** for intake validation
- Plain `fetch` (or a thin wrapper) for the one `POST /analyse` call. A data-fetching
  library is optional at this scale — do not add one unless loading/error handling gets messy.

### Backend

- **FastAPI** with Python 3.12
- **Pydantic v2** for request/response schemas
- **SQLModel** or SQLAlchemy for data access
- **SQLite** for MVP persistence
- **httpx** for Adzuna/GitHub requests
- **pypdf** for PDF text extraction
- **python-docx** only if DOCX resume upload is added later
- **RapidFuzz** for lightweight description/title matching and deduplication

### Data and integrations

- **Adzuna API** as the primary optional job-data source
- Curated `jobs_snapshot.json` as the mandatory fallback/demo data
- **GitHub public REST API** only for an explicitly supplied public repository URL
- LLM via an environment-configured provider:
  - Default implementation: Gemini Flash or equivalent fast model
  - Keep a provider abstraction so the app still works with demo fixtures if no key exists

### Development / deployment

- Docker Compose for local development is optional but encouraged
- Frontend deploy target: Vercel
- Backend deploy target: Render or Railway
- Ensure the local demo can run without any cloud dependencies

---

## 10. Repository structure

```text
gradbridge/
├── README.md
├── .env.example
├── docker-compose.yml                  # optional for local development
├── apps/
│   ├── web/                            # Next.js frontend
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── analyse/page.tsx
│   │   │   └── demo/page.tsx
│   │   ├── components/
│   │   │   ├── intake/
│   │   │   ├── dashboard/
│   │   │   ├── bridge-plan/
│   │   │   └── ui/
│   │   ├── lib/
│   │   └── types/
│   └── api/                            # FastAPI backend
│       ├── app/
│       │   ├── main.py
│       │   ├── routers/
│       │   │   ├── analyse.py
│       │   │   ├── market.py
│       │   │   └── github.py
│       │   ├── services/
│       │   │   ├── resume_parser.py
│       │   │   ├── job_service.py
│       │   │   ├── job_normalizer.py
│       │   │   ├── skill_extractor.py
│       │   │   ├── evidence_matcher.py
│       │   │   ├── bridge_plan.py
│       │   │   └── llm_service.py
│       │   ├── models/
│       │   └── schemas/
│       └── requirements.txt
├── data/
│   ├── jobs_snapshot.json
│   ├── demo_candidate.json
│   └── skill_taxonomy.json
└── docs/
    └── product-decisions.md
```

---

## 11. API contract for the MVP

### `POST /analyse`

Request:

```json
{
  "resume_text": "string",
  "target_pathway": "ai_automation",
  "location": "auckland",
  "github_repo_url": "https://github.com/example/repo",
  "use_demo_data": false
}
```

Response shape:

```json
{
  "market_snapshot": {
    "listing_count": 37,
    "distinct_employers": 22,
    "location": "Auckland",
    "captured_at": "2026-06-25T10:00:00Z",
    "sources": ["Adzuna", "Cached demo snapshot"]
  },
  "role_pathways": [
    {
      "id": "ai_automation",
      "label": "AI & Automation",
      "evidence_coverage": 74,
      "market_demand": "high",
      "summary": "Strong alignment through Python, APIs, databases, and project ownership."
    }
  ],
  "skills": [
    {
      "name": "Python",
      "market_label": "Core demand",
      "demand_score": 82,
      "status": "strong_proof",
      "confidence": "high",
      "market_evidence": "Present in 28 of 37 relevant listings",
      "candidate_evidence": [
        {
          "source": "resume",
          "excerpt": "Built a Python..."
        }
      ],
      "recommended_action": "Surface in a targeted project bullet."
    }
  ],
  "bridge_plan": [
    {
      "priority": 1,
      "action_type": "surface",
      "title": "Make API integration visible",
      "time_estimate": "15 minutes",
      "why": "REST APIs appear in 16 of 37 relevant listings.",
      "steps": [
        "Update your project bullet...",
        "Add a concise architecture section..."
      ],
      "resume_draft": "Built..."
    }
  ]
}
```

### `GET /market-summary`

Return cached aggregate data for the selected role pathway and location.

### `POST /demo-analysis`

Return a deterministic analysis response. This is the fallback for judge demos.

---

## 12. UI and visual design system

### Brand personality

The product should feel:

- trustworthy;
- calm;
- practical;
- modern;
- optimistic;
- evidence-led rather than flashy.

It should feel like a career product built for thoughtful technical graduates, not a gamified AI toy.

### Non-negotiable theme rule

> **Use a clean white background. Do not use a dark UI. Do not use full-page gradients.**

### Colour palette

Use these consistently:

```css
--background: #FFFFFF;
--surface: #F8FAFC;
--surface-subtle: #F1F5F9;
--border: #E2E8F0;

--text-primary: #0F172A;
--text-secondary: #475569;
--text-muted: #64748B;

--primary: #2563EB;
--primary-hover: #1D4ED8;
--primary-soft: #EFF6FF;

--success: #059669;
--success-soft: #ECFDF5;

--warning: #D97706;
--warning-soft: #FFFBEB;

--danger: #DC2626;
--danger-soft: #FEF2F2;

--purple-accent: #7C3AED;
--purple-soft: #F5F3FF;
```

### Skill status colours

- Strong proof: green
- Hidden proof: blue
- Adjacent proof: amber
- No proof yet: red/rose, used sparingly and constructively

### Layout guidance

- White page background
- Light grey cards with subtle borders
- Generous whitespace
- Use a max-width content container
- Rounded corners: 10–14px
- Soft, restrained shadows only where hierarchy needs it
- Typography should be clear and professional:
  - Inter, Geist, or system font
- No excessive glassmorphism
- No neon/glow effects
- No large hero illustration required for MVP
- Do not overwhelm users with huge dense tables

### Dashboard composition

Recommended hierarchy:

1. Header: GradBridge logo + “Market snapshot” metadata
2. Insight banner with a plain-language headline
3. Role readiness cards
4. Skill evidence map
5. Bridge Plan
6. Transparent methodology/disclaimer section

### Copy tone

Use direct and supportive language:

- Good: “You already have evidence for this skill. It is just not visible in your resume.”
- Good: “This is a focused gap—not a reason to start over.”
- Avoid: “You are underqualified.”
- Avoid: “Beat the ATS.”
- Avoid: “Guaranteed to get more interviews.”

---

## 13. Demo candidate

Include a deterministic demo profile representing a final-year Computer Systems Engineering graduate with experience such as:

- Python automation / data processing
- React + TypeScript web app
- REST API integration
- SQLite or PostgreSQL
- STM32 / CAN / embedded work
- Git/GitHub
- project leadership / multidisciplinary team collaboration

The demo should illustrate this key moment:

> “I thought I was underqualified for automation roles. Actually, I already have Python, APIs, databases, and project ownership. I need to surface two things and spend one afternoon strengthening one existing project.”

---

## 14. Implementation order

Build in this order:

1. Create the monorepo and basic FastAPI + Vite/React connection.
2. Add `jobs_snapshot.json` and `demo_candidate.json`.
3. Implement deterministic skill extraction from:
   - job descriptions;
   - resume text;
   - demo data.
4. Implement market demand scoring and evidence classification.
5. Implement `POST /demo-analysis`.
6. Build the intake page.
7. Build the dashboard and Bridge Plan using demo data first.
8. Wire real API analysis after the demo route is polished.
9. Add optional Adzuna and GitHub integrations.
10. Add loading, empty, and error states.
11. Test the full demo with internet disabled / no API keys.

### Definition of done

The MVP is done when a judge can:

1. Load the demo candidate;
2. choose “AI & Automation” and “Auckland”;
3. see a credible role readiness explanation;
4. see current/cached skill demand;
5. understand the difference between strong, hidden, adjacent, and missing evidence;
6. receive three useful next steps;
7. understand that the recommendations are evidence-based and honest.

---

## 15. Environment variables

Create `.env.example`:

```bash
# Backend
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
GITHUB_TOKEN=
LLM_API_KEY=
LLM_PROVIDER=gemini

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The app must still function with all variables empty by using cached demo data.

---

## 16. Final product statement

> **GradBridge helps technical graduates turn resumes, projects, and selected GitHub evidence into a clear map of the entry-level roles they can target now, the skills employers are asking for, and the smallest credible actions needed to close the gap.**
