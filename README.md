# Goose Sense: Industrial R&D Troubleshooting & Ecosystem Assistant

An AI-powered industrial troubleshooting coordination layer and retrieval system designed for dairy automation and process manufacturing plants. Goose Sense enables plant operators, maintenance engineers, and technicians to diagnose equipment failures step-by-step, review technical documentation via hybrid RAG retrieval, and automatically escalate complex issues to verified parts, field engineers, or certified training courses.

---

## Architecture Overview

Goose Sense is built as a modular monorepo combining a high-performance **FastAPI AI Coordination Backend** (`apps/sense-api`) and an interactive **Next.js Web Portal** (`apps/portal`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Goose Sense Portal (Next.js 16)                 │
│         Interactive Diagnostic UI • Checklists • Media Playback        │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP /chat (JSON)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Goose Sense API (FastAPI 3.0)                     │
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
goose-ecosystem/
├── apps/
│   ├── portal/              # Main Next.js Chatbot Web Interface (Port 3004)
│   ├── sense-api/           # Python FastAPI AI Coordination & Hybrid RAG Engine (Port 8001)
│   ├── goose-digital/       # IIoT Telemetry & SCADA Dashboard (Port 3001)
│   ├── goose-elevate/       # Industrial Training Platform UI (Port 3002)
│   ├── goose-mart/          # [Placeholder] Unbuilt storefront template (Port 3000)*
│   └── hire-my-engineer/    # [Placeholder] Unbuilt talent directory template (Port 3003)*
├── packages/
│   ├── database/            # Shared interface stubs (@goose/database)
│   └── ui/                  # Shared UI components (@goose/ui)
├── docker-compose.yml       # Docker container orchestration
├── start-ecosystem.ps1      # PowerShell launcher for all services
└── package.json             # Root npm workspaces definition
```

> **Note on Placeholder Apps**:\
> `apps/goose-mart` and `apps/hire-my-engineer` are unbuilt starter scaffolds bootstrapped via `create-next-app`. They are non-core placeholder targets; all catalog hardware and engineer profile data are maintained and served directly by the `sense-api` SQLite database.

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

# Optional: Cohere Reranker (falls back to internal score sort if omitted)
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

### 3. Start the Backend (`apps/sense-api`)

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

# Start the FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
The backend API documentation will be available at: **`http://localhost:8001/docs`**

---

### 4. Start the Portal Frontend (`apps/portal`)

In a new terminal window:
```bash
cd apps/portal

# Install dependencies
npm install

# Start development server on port 3004
npm run dev -- -p 3004
```
Open **`http://localhost:3004`** in your browser.

---

### 5. Running the Complete Ecosystem

To start all micro-apps simultaneously on Windows:
```powershell
./start-ecosystem.ps1
```
This will launch:
- `http://localhost:3000` — Goose Mart (Placeholder)
- `http://localhost:3001` — Goose Digital (Telemetry Dashboard)
- `http://localhost:3002` — Goose Elevate (Course Syllabus)
- `http://localhost:3003` — HireMyEngineer (Placeholder)
- `http://localhost:3004` — Goose Sense Portal (Main Chatbot)
- `http://localhost:8001` — Goose Sense API (FastAPI Backend)

---

## Document Ingestion

To ingest machinery manuals, standard operating procedures (SOPs), or datasheets into the hybrid RAG index:
- Use the **Attachment** icon in the Portal chat input to upload PDF, Word (`.docx`), Excel/CSV (`.xlsx`, `.csv`), or plain text files.
- Files are parsed, split into 800-character overlapping chunks, embedded, and indexed into both the Pinecone vector index and the local BM25 corpus.

---

## License

ISC License. Distributed for industrial automation research, development, and demonstration purposes.
