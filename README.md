# SmartCareerFit Assistant

An AI-powered career tool that analyzes your resume against a job description, scores your fit, identifies skill gaps, and generates an ATS-optimized resume and personalized cover letter — all running locally with Ollama.

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

## Tech Stack

- **UI**: [Streamlit](https://streamlit.io)
- **AI Agents**: [PydanticAI](https://docs.pydantic.dev/latest/concepts/pydantic_ai/) with [Ollama](https://ollama.com) (default model: `llama3.2`)
- **PDF Generation**: [ReportLab](https://www.reportlab.com)
- **Database**: SQLite via a lightweight repository layer
- **Validation**: [Pydantic v2](https://docs.pydantic.dev)

---

## Project Structure

```
SmartCareerFitAssistant/
├── app.py                    # Streamlit entry point
├── main.py                   # CLI entry point
├── src/
│   ├── agents/
│   │   ├── extractor.py      # Resume & job description parsers (LLM agents)
│   │   ├── analyzer.py       # Fit scorer & skill gap analyzer
│   │   └── generator.py      # Resume writer & cover letter writer
│   ├── models/
│   │   ├── resume.py         # ResumeData schema
│   │   ├── job.py            # JobRequirements schema
│   │   └── analysis.py       # FitScore, SkillGapReport, FullAnalysis
│   ├── services/
│   │   ├── pipeline.py       # Orchestrates all agents end-to-end
│   │   └── pdf_parser.py     # Extracts text from uploaded PDFs
│   ├── db/
│   │   ├── database.py       # SQLite initialization
│   │   └── repository.py     # Save/query analyses
│   ├── utils/
│   │   └── pdf.py            # Professional PDF rendering with ReportLab
│   └── config.py             # Settings (model name, DB path, Ollama URL)
├── ui/
│   ├── results.py            # Results tabs renderer
│   ├── sidebar.py            # Sidebar profile panel
│   ├── components.py         # Score cards, skill chips, result boxes
│   └── styles.py             # Global CSS injection
├── tests/
│   ├── test_database.py
│   └── test_models.py
└── data/
    └── career_assistant.db   # SQLite database (auto-created)
```

---

## Prerequisites

1. **Python 3.11+**
2. **Ollama** running locally with a compatible model pulled:

```bash
ollama pull llama3.2
ollama serve
```

---

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd SmartCareerFitAssistant

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables (optional)

Create a `.env` file to override defaults:

```env
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434/v1
DB_PATH=data/career_assistant.db
```

---

## Running the App

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

1. **Upload your resume** — paste text or upload a PDF.
2. **Paste the job description** — copy it from any job posting.
3. **Click "Analyze & Generate All Outputs"** — the pipeline runs in ~2–5 minutes on local hardware.
4. **Review your results** across four tabs:
   - **Fit Analysis** — score breakdown and skill chips
   - **Optimized Resume** — ATS-ready Markdown + download PDF
   - **Cover Letter** — tailored letter + download PDF
   - **Learning Roadmap** — prioritized skill gaps with learning suggestions

> Results persist in the session — clicking "Download PDF" does **not** reset the page.

---

## Pipeline Architecture

```
Resume Text + Job Description
        │
        ▼
  [Extractor Agents]
  ResumeData + JobRequirements
        │
        ▼
  [Analyzer Agents]
  FitScore + SkillGapReport
        │
        ▼
  [Generator Agents]
  Optimized Resume + Cover Letter
        │
        ▼
  [SQLite Repository]       [Streamlit UI + PDF Export]
```

Each stage uses a PydanticAI `Agent` backed by a local Ollama model. All agents run asynchronously and are orchestrated by `src/services/pipeline.py`.

---

## Running Tests

```bash
pytest tests/
```

---

## Configuration

| Setting | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint |
| `DB_PATH` | `data/career_assistant.db` | SQLite file path |
| `DEBUG` | `true` | Enable debug logging |
