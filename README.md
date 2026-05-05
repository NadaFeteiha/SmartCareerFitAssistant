# SmartCareerFit Assistant

An AI-powered career tool that analyzes your resume against a job description, scores your fit, identifies skill gaps, and generates an ATS-optimized resume and personalized cover letter — powered by the Claude API.

---

## Features

| Feature | Description |
|---|---|
| **Fit Scoring** | Overall score (0–100) with sub-scores for skill match, experience alignment, and keyword coverage |
| **Skill Gap Analysis** | Identifies missing hard and soft skills with a prioritized learning roadmap |
| **Resume Optimizer** | Rewrites your resume in ATS-friendly Markdown, tailored to the target job — no fabrication |
| **Cover Letter Generator** | Produces a concise, tailored 3–4 paragraph cover letter |
| **PDF Export** | Downloads a professionally formatted PDF for both the resume and cover letter |

---

## AI Agents (7)

All agents call the [Claude API](https://docs.anthropic.com) using **tool use** (MCP-style structured outputs) — no JSON parsing or repair needed. They are orchestrated in sequence by `backend/src/services/pipeline.py`.

| # | Module | Function | Role |
|---|--------|----------|------|
| 1 | `extractor.py` | `extract_resume` | Parses raw resume text into structured `ResumeData` (name, summary, skills, experience, education) |
| 2 | `extractor.py` | `extract_job` | Parses the job posting into structured `JobRequirements` (title, keywords, responsibilities, required skills) |
| 3 | `keyword_optimizer.py` | `extract_top_jd_keywords` | Pulls up to **10** high-value ATS keywords from the job description; merged with extractor keywords |
| 4 | `analyzer.py` | `score_candidate` | Produces `FitScore`: overall 0–100, sub-scores (skill match, experience alignment, keyword coverage), strengths, and explanation |
| 5 | `analyzer.py` | `analyze_gaps` | Produces `SkillGapReport`: missing hard/soft skills, structured missing requirements, and a prioritized learning roadmap |
| 6 | `generator.py` | `write_resume` | Rewrites the resume as ATS-oriented Markdown (no fabrication; aligns wording with the job and keywords) |
| 7 | `generator.py` | `write_cover_letter` | Writes a tailored 3–4 paragraph cover letter for the target role and company |

**Flow:** extract resume → extract job → optimize keywords → score fit → analyze gaps → generate resume → generate cover letter.

---

## Tech Stack

- **Frontend**: [React](https://react.dev) + [Vite](https://vitejs.dev) + [Tailwind CSS](https://tailwindcss.com)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org)
- **AI Agents**: [Claude API](https://docs.anthropic.com) (`claude-sonnet-4-6`) with tool use for structured outputs
- **PDF Generation**: [ReportLab](https://www.reportlab.com)
- **Database**: SQLite via a lightweight repository layer
- **Validation**: [Pydantic v2](https://docs.pydantic.dev)

---

## Project Structure

```
SmartCareerFitAssistant/
├── backend/
│   ├── api.py                    # FastAPI app — all HTTP endpoints
│   ├── pyproject.toml
│   └── src/
│       ├── agents/
│       │   ├── extractor.py       # extract_resume + extract_job (tool use)
│       │   ├── keyword_optimizer.py  # extract_top_jd_keywords (tool use)
│       │   ├── analyzer.py        # score_candidate + analyze_gaps (tool use)
│       │   └── generator.py       # write_resume + write_cover_letter
│       ├── models/
│       │   ├── resume.py          # ResumeData schema
│       │   ├── job.py             # JobRequirements schema
│       │   └── analysis.py        # FitScore, SkillGapReport, FullAnalysis
│       ├── services/
│       │   ├── pipeline.py        # Orchestrates all agents end-to-end
│       │   └── pdf_parser.py      # Extracts text from uploaded PDFs
│       ├── database/
│       │   ├── database.py        # SQLite initialization
│       │   └── repository.py      # Save/query analyses and user skills
│       ├── utils/
│       │   ├── pdf.py             # PDF rendering with ReportLab
│       │   ├── resume_sections.py # Markdown skill injection & consolidation
│       │   └── skill_validation.py  # Filter implausible gap skills
│       └── config.py              # Settings (model, DB path, API key)
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/client.ts          # API client
│   │   ├── components/            # Header, Hero, InputPanel, Sidebar
│   │   │   └── results/           # FitAnalysis, OptimizedResume, CoverLetter, LearningRoadmap
│   │   ├── types/index.ts
│   │   └── styles/index.css
│   ├── package.json
│   └── vite.config.ts
└── tests/
    ├── test_database.py
    └── test_models.py
```

---

## Prerequisites

1. **Python 3.11+**
2. **Node.js 18+**
3. An **Anthropic API key** — get one at [console.anthropic.com](https://console.anthropic.com)

---

## Setup

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -e .

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### Frontend

```bash
cd frontend
npm install
```

---

## Running the App

Start both servers (in separate terminals):

```bash
# Terminal 1 — backend
cd backend
uvicorn api:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Usage

1. **Upload your resume** — paste text or upload a PDF.
2. **Paste the job description** — copy it from any job posting.
3. **Click Analyze** — the pipeline runs all 7 agents in sequence.
4. **Review your results** across four tabs:
   - **Fit Analysis** — score breakdown and skill chips
   - **Optimized Resume** — ATS-ready Markdown + download PDF
   - **Cover Letter** — tailored letter + download PDF
   - **Learning Roadmap** — prioritized skill gaps with learning suggestions

---

## Pipeline Architecture

```
Resume Text + Job Description
        │
        ▼
  [Extractor Agents]  — Claude tool use
  ResumeData + JobRequirements
        │
        ▼
  [Keyword Optimizer]  — Claude tool use
  Merged keyword list for ATS targeting
        │
        ▼
  [Analyzer Agents]  — Claude tool use
  FitScore + SkillGapReport
        │
        ▼
  [Generator Agents]  — Claude text generation
  Optimized Resume + Cover Letter
        │
        ▼
  [SQLite Repository]       [FastAPI + React UI + PDF Export]
```

Agents use Claude's **tool use** feature (`tool_choice: required`) to guarantee structured outputs — no regex, no JSON repair, no retries for malformed output.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload-pdf` | Extract text from a resume PDF |
| `POST` | `/api/analyze` | Run the full 7-agent pipeline |
| `GET` | `/api/analyses` | Fetch all saved analyses |
| `POST` | `/api/download/resume` | Generate and download resume PDF |
| `POST` | `/api/download/cover-letter` | Generate and download cover letter PDF |
| `POST` | `/api/user/skills` | Persist a confirmed skill for a user |
| `GET` | `/api/user/skills/{user_name}` | Retrieve saved skills for a user |

---

## Running Tests

```bash
cd backend
pytest tests/
```

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(required)_ | Claude API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `DB_PATH` | `data/career_assistant.db` | SQLite file path |
| `DEBUG` | `false` | Enable debug logging |
