# SmartCareerFit Assistant

An AI-powered career tool that analyzes your resume against a job description, scores your fit, identifies skill gaps, and generates an ATS-optimized resume and personalized cover letter — powered by the Claude API.

---

## Features

| Feature | Description |
|---|---|
| **Fit Scoring** | Overall score (0–100) with sub-scores for skill match, experience alignment, and keyword coverage |
| **Skill Gap Analysis** | Identifies missing hard and soft skills with a prioritized learning roadmap |
| **Skill Confirmation Assistant** | Asks the user to confirm missing skills, saves answers, auto-recalculates fit score, and reuses answers in future analyses |
| **Resume Optimizer** | Rewrites your resume in ATS-friendly Markdown, tailored to the target job — no fabrication |
| **Cover Letter Generator** | Produces a concise, tailored 3–4 paragraph cover letter |
| **GitHub Project Import** | Imports public GitHub projects, prioritizes projects matching the current job description, and adds them to resume Projects |
| **Profile Memory** | Saves contact fields (phone, LinkedIn, GitHub) so they are auto-filled on future sessions and still editable |
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

1. **Sign up or sign in** — create an account (or use the *Forgot password* tab to reset).
2. **Upload your resume once** — use **Upload Resume** (paste text or PDF). It's saved to your account; use **Replace Resume** or **Remove** any time.
3. **Paste the job description** — copy it from any job posting.
4. **(Optional) Import GitHub projects** — enter your GitHub username and import public projects. The app prioritizes repos that match the current job description and adds them under **Projects**.
5. **Click Analyze** — the pipeline runs all 7 agents against your saved resume.
6. **Confirm missing skills in chat** — when prompted, answer whether you have each skill. Answers are saved, added to your profile context, and the fit score refreshes automatically.
7. **Review your results** across four tabs:
   - **Fit Analysis** — score breakdown and skill chips
   - **Optimized Resume** — ATS-ready Markdown + download PDF
   - **Cover Letter** — tailored letter + download PDF
   - **Learning Roadmap** — prioritized skill gaps with learning suggestions
8. **Sign out** from the header when you're done.

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

Endpoints marked **🔒** require an `Authorization: Bearer <token>` header (token returned by `/api/auth/login` or `/api/auth/register`).

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create an account → returns JWT token + user |
| `POST` | `/api/auth/login` | Sign in → returns JWT token + user |
| `GET` | `/api/auth/me` | 🔒 Current user |
| `POST` | `/api/auth/forgot` | Issue a password reset token (returned in dev) |
| `POST` | `/api/auth/reset` | Reset password with a token + new password |
| `GET` | `/api/resume` | 🔒 Get the user's saved resume |
| `PUT` | `/api/resume` | 🔒 Save/replace the user's resume |
| `DELETE` | `/api/resume` | 🔒 Remove the user's saved resume |
| `POST` | `/api/upload-pdf` | 🔒 Extract resume text from a PDF and persist it |
| `POST` | `/api/analyze` | 🔒 Run the full 7-agent pipeline against the saved resume |
| `GET` | `/api/analyses` | Fetch all saved analyses |
| `POST` | `/api/download/resume` | Generate and download resume PDF |
| `POST` | `/api/download/cover-letter` | Generate and download cover letter PDF |
| `POST` | `/api/user/skills` | Persist a confirmed skill for a user |
| `GET` | `/api/user/skills/{user_name}` | Retrieve saved skills for a user |
| `GET` | `/api/user/skill-confirmations` | 🔒 Get saved skill confirmation decisions for current user |
| `POST` | `/api/user/skill-confirmations` | 🔒 Save one skill decision (`has_skill` true/false) |
| `GET` | `/api/user/profile` | 🔒 Get saved profile contact fields (phone/linkedin/github) |
| `PUT` | `/api/user/profile` | 🔒 Save profile contact fields (phone/linkedin/github) |
| `POST` | `/api/github/import` | 🔒 Import public GitHub repos (optionally filtered by current job text) into resume Projects |

The `JWT_SECRET` env var sets the JWT signing secret (defaults to a dev placeholder — set it in production).

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
