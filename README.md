# Multi-Agent Industrial Troubleshooting AI

A production-grade, multi-agent RAG-based industrial troubleshooting assistant and diagnostic coordination platform designed for manufacturing plants, automation systems, and process facilities. The system enables plant operators, maintenance engineers, and technicians to diagnose equipment failures step-by-step, retrieve verified technical documentation via hybrid RAG retrieval, and automatically escalate complex issues to verified parts, field engineers, or certified training courses.

> **Note:** Originally prototyped as an internal R&D concept ("Goose Sense") for dairy and process automation, this project has been refactored into an open, standalone industrial troubleshooting platform.

---

## Architecture Overview

The system is built as a modular monorepo combining a high-performance **FastAPI AI Coordination Backend** (`apps/sense-api`) and an interactive **Next.js Web Portal** (`apps/portal`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Diagnostic Web Portal (Next.js 16)                 │
│         Interactive Diagnostic UI • Checklists • Media Playback        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP /chat (JSON)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Coordination Engine (FastAPI 3.0)                    │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Two-Pass Intent Classifier                    │  │
│  │       Regex Rule Pass (Fast) ──► LLM Fallback Classifier         │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ Intent: TROUBLESHOOTING /        │
│                                     │         PRODUCT / TALENT /       │
│                                     │         TRAINING / GENERAL_QA    │
│                                     ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Specialist Agent Router                     │  │
│  │  • TroubleshootingAgent (Strict Decision Trees + Safety Prompts) │  │
│  │  • ProductRecommendationAgent (Hardware Spec Matching)           │  │
│  │  • TrainingRecommendationAgent (Course & Skill Matching)         │  │
│  │  • TalentRecommendationAgent  (Contractor & Field Staffing)      │  │
│  │  • GeneralQAAgent             (General Industrial Inquiries)     │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│                                     ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Hybrid RAG Engine                           │  │
│  │  ┌─────────────────────────┐       ┌──────────────────────────┐  │  │
│  │  │  Pinecone Vector Search │       │   BM25 Keyword Search    │  │  │
│  │  │ (Gemini Embeddings 768d)│       │  (rank-bm25 in-memory)   │  │  │
│  │  └────────────┬────────────┘       └────────────┬─────────────┘  │  │
│  │               │                                 │                │  │
│  │               └───────────────┬─────────────────┘                │  │
│  │                               ▼                                  │  │
│  │            Reciprocal Rank Fusion (RRF: k=60)                    │  │
│  │             (Vector Weight: 0.6 | BM25 Weight: 0.4)              │  │
│  │                               │                                  │  │
│  │                               ▼                                  │  │
│  │              Cohere Rerank v3 (Fallback: Score)                  │  │
│  └───────────────────────────────┬──────────────────────────────────┘  │
│                                  │ Grounded Context                    │
│                                  ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     Multi-Provider LLM Layer                     │  │
│  │     Google Gemini 1.5 Flash (Default) • OpenAI • Local Ollama    │  │
│  │                SQLite Response Cache & Turn Memory               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

1. **Structured Diagnostic Decision Trees**
   - Curated engineering decision trees for critical dairy plant equipment: pasteurizers, clean-in-place (CIP) skids, centrifugal pumps, pneumatic valves, steam boilers, RTD/temperature sensors, conveyor belts, and compressors.
   - Enforces a **Clarifying State** (diagnostic verification) before outputting a **Resolved State** with safety warnings, actionable 5–7 step mechanical guides, visual reference schematics, and instructional video playback.

2. **Hybrid RAG Pipeline**
   - Combines dense semantic search (Pinecone) with exact sparse lexical matching (BM25Okapi).
   - Fuses ranked candidate lists using weighted **Reciprocal Rank Fusion (RRF)**.
   - Re-scores top candidates using **Cohere Rerank v3** for precision context injection into LLM prompts.

3. **Multi-Agent Intent Routing**
   - Automatically directs user queries to specialist agents based on intent:
     - `TROUBLESHOOTING`: Equipment fault resolution and diagnostic verification.
     - `PRODUCT_SEARCH`: Hardware procurement from industrial catalog (Grundfos, Siemens, Schneider, Endress+Hauser).
     - `TRAINING_REQUEST`: Curriculum recommendations for automation and maintenance (PLC programming, safety, CIP).
     - `ENGINEERING_TALENT`: Technical staffing and contractor matching.
     - `GENERAL_QA`: Broad industrial inquiry fallback.

4. **Ecosystem Escalation**
   - Built-in referral routing connects unresolved equipment breakdowns directly to relevant commercial channels: parts ordering, emergency field technician dispatch, engineering consultancy, and training.

---

## Monorepo Layout

```text
multi-agent-industrial-troubleshooting-ai/
├── apps/
│   ├── portal/              # Core Diagnostic Web Portal (Next.js 16, Port 3004)
│   ├── sense-api/           # Core AI Coordination & Hybrid RAG Engine (FastAPI, Port 8001)
│   ├── goose-digital/       # [Optional Demo] IIoT Telemetry & SCADA Dashboard (Port 3001)
│   ├── goose-elevate/       # [Optional Demo] Industrial Training Platform UI (Port 3002)
│   ├── goose-mart/          # [Unbuilt Placeholder] Scaffolding template
│   └── hire-my-engineer/    # [Unbuilt Placeholder] Scaffolding template
├── packages/
│   ├── database/            # Shared interface stubs (@goose/database)
│   └── ui/                  # Shared UI components (@goose/ui)
├── docker-compose.yml       # Docker container orchestration
├── start.ps1                # Primary PowerShell launcher (starts sense-api + portal)
└── package.json             # Root npm workspaces definition
```

> **Note on Placeholder Apps & Recommendation Routing**:\
> - `apps/goose-mart` and `apps/hire-my-engineer` are unbuilt starter scaffolds bootstrapped via `create-next-app`. They are non-core placeholders and not required to run.
> - The specialist recommendation agents (Product, Talent, Training) already link out directly to real public platforms (`https://www.goosefly.in/goosemart`, `https://www.hiremyengineer.com/`, `https://www.gooseelevate.com/`). No auxiliary local micro-services are needed for those links to work.

---

## Tech Stack

- **Frontend (`apps/portal`)**:
  - Next.js 16 (App Router, Turbopack)
  - React 19
  - Tailwind CSS v4
  - Lucide React
  - React Markdown & Remark GFM
- **Backend (`apps/sense-api`)**:
  - Python 3.11+ / FastAPI / Uvicorn
  - LangChain & LangChain Google GenAI
  - Pinecone Vector Client (`pinecone`)
  - Rank-BM25 (`rank_bm25`)
  - Cohere API Client (`cohere`)
  - SQLite3 with WAL journal mode (conversation memory, scraped catalog, response caching)
  - PyPDF2, python-docx, pandas, openpyxl (document ingestion)

---

## Setup & Running Locally

The working core of this platform consists of two services:
1. **The AI Coordination Backend** (`apps/sense-api` on port `8001`) — handles intent classification, decision-tree diagnostics, hybrid RAG retrieval, and multi-agent LLM routing.
2. **The Diagnostic Web Portal** (`apps/portal` on port `3004`) — provides the user chat interface, step-by-step diagnostic checklists, verified citation viewer, and manual ingestion.

### 1. Prerequisites

- **Node.js**: v18.18+ or v20+
- **Python**: v3.11 or v3.12
- **Google Gemini API Key**: [Get a Gemini API Key](https://ai.google.dev/)
- **Pinecone Account**: [Pinecone Console](https://www.pinecone.io/) (for vector retrieval)

---

### 2. Environment Configuration

Copy the example environment files in both the API backend and Portal frontend:

#### Backend Configuration (`apps/sense-api/.env`)
```bash
cp apps/sense-api/.env.example apps/sense-api/.env
```
Edit `apps/sense-api/.env`:
```env
LLM_PROVIDER="gemini"
GEMINI_API_KEY="your_gemini_api_key_here"
PINECONE_API_KEY="your_pinecone_api_key_here"
PINECONE_ENVIRONMENT="us-east-1"
PINECONE_INDEX_NAME="goose-manuals"

# Optional: Cohere Reranker (falls back to reciprocal rank fusion score if omitted)
COHERE_API_KEY="your_cohere_api_key_here"
```

#### Frontend Configuration (`apps/portal/.env.local`)
```bash
cp apps/portal/.env.example apps/portal/.env.local
```
Edit `apps/portal/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

---

### 3. Quick Launch (Windows)

To launch both the FastAPI backend and Next.js portal automatically in one command:
```powershell
./start.ps1
```
This script initializes `sense-api` on port 8001, launches `portal` on port 3004, and automatically opens **`http://localhost:3004`** in your browser.

---

### 4. Manual Step-by-Step Launch

If you prefer starting each service manually in separate terminals:

#### Step 4a: Start the Backend (`apps/sense-api`)
```bash
cd apps/sense-api

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
Interactive API documentation will be available at **`http://localhost:8001/docs`**.

#### Step 4b: Start the Diagnostic Portal (`apps/portal`)
In a second terminal:
```bash
cd apps/portal

# Install dependencies
npm install

# Start development server on port 3004
npm run dev -- -p 3004
```
Open **`http://localhost:3004`** in your browser to interact with the assistant.

---

## Optional: Standalone Demo Apps

The repository includes two independent demo applications originally prototyped alongside the project. These are completely optional and not required for the core troubleshooting assistant to function:

1. **`apps/goose-digital` (Port 3001)** — An IIoT telemetry & SCADA status dashboard demonstrating live machine metric monitoring.
   ```bash
   cd apps/goose-digital
   npm install
   npm run dev -- -p 3001
   ```
   Access at `http://localhost:3001`.

2. **`apps/goose-elevate` (Port 3002)** — A sample course syllabus and certification mockup for industrial plant operator training.
   ```bash
   cd apps/goose-elevate
   npm install
   npm run dev -- -p 3002
   ```
   Access at `http://localhost:3002`.

*(Note: `apps/goose-mart` and `apps/hire-my-engineer` are unbuilt placeholder scaffolds and do not need to be run).*

---

## Document Ingestion

To ingest machinery manuals, standard operating procedures (SOPs), or datasheets into the hybrid RAG index:
- Use the **Attachment** icon in the Portal chat input to upload PDF, Word (`.docx`), Excel/CSV (`.xlsx`, `.csv`), or plain text files.
- Files are parsed, split into 800-character overlapping chunks, embedded, and indexed into both the Pinecone vector index and the local BM25 corpus.

---

## License

ISC License. Distributed for industrial automation research, development, and demonstration purposes.
