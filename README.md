# AIVOA Complaint Intelligence

AI-powered Pharmaceutical Customer Complaint Management System built for the AIVOA AI Product Engineer internship assignment.

---

## 1. Project Overview

**AIVOA Complaint Intelligence** is a specialized QA/QMS Copilot application designed for pharmaceutical quality management teams. It automates the intake, extraction, classification, risk assessment, and field population of customer complaints submitted via raw text or PDF documents.

### Key Objectives
1. **Intake**: Accept customer complaints via free-text input or uploaded PDF documents.
2. **AI Analysis**: Process unstructured text through an explicit 7-node LangGraph orchestration workflow backed by Groq LLM inference.
3. **Structured Extraction**: Extract 16+ structured pharmaceutical parameters (product info, batch numbers, dates, complaint types, etc.) with explicit missing-field identification.
4. **Risk Assessment**: Compute severity (Low, Medium, High, Critical), risk level (Minor, Major, Critical), confidence score, and suggested QA next steps using a negation-aware risk engine.
5. **Conversational Copilot**: Allow QA users to review, correct, and update extracted complaint details interactively through natural language chat.
6. **Persistence**: Save, review, update, and manage structured complaints in PostgreSQL.
7. **Bonus QA Tools**: Provide Complaint Completeness Checking, Rule-Based Duplicate Complaint Detection, and Automated CAPA Recommendations.

> **AI Copilot Philosophy**: The system operates as an assistant to human QA professionals. It provides recommendations and structured drafts for human review and final authorization. It does NOT make autonomous regulatory decisions or trigger automated recalls.

---

## 2. Core Features

- **Unstructured Text Analysis**: Analyzes raw emails, phone transcripts, or customer service logs.
- **PDF Document Extraction & Analysis**: In-memory PDF text parsing (`pypdf`) with automated AI field extraction.
- **Auto-Populated Complaint Form**: Live synchronization between AI extraction output and the structured complaint form.
- **Negation-Aware Risk Engine**: Evaluates severity and risk levels while correctly interpreting explicit negations (e.g., *"No contamination reported"* does not trigger a Critical flag).
- **Interactive AI Copilot**: Right-panel chat interface for reviewing analysis logic and issuing field updates.
- **Full CRUD Persistence**: Complete PostgreSQL integration to save, filter, edit (partial update), view history, and delete complaints.
- **Responsive Workspace**: Bounded 100vh dual-panel desktop layout (`> 1024px`) with independent left/right scrolling, reflowing naturally into a single-column layout on mobile devices.

---

## 3. Bonus Features

1. **Complaint Completeness Checker**
   - Evaluates complaint readiness against the 5 core required fields (`customer_name`, `product_name`, `batch_number`, `complaint_type`, `complaint_description`).
   - Displays real-time readiness status (`🟢 Complaint Ready` vs `🟠 Information Needed`) and highlights missing optional vs required fields.

2. **Duplicate Complaint Detection**
   - Rule-based, deterministic database matching against existing complaints in PostgreSQL.
   - Categorizes potential matches into **HIGH** confidence (matching `product_name` + `batch_number`) and **MEDIUM** confidence (matching `product_name` + `customer_name`).

3. **CAPA Recommendation Engine**
   - Recommends tailored Corrective and Preventive Actions (CAPA) with assigned priorities (Low, Medium, High, Critical) based on risk level, severity, and missing data points.

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| **Frontend Framework** | React 19, Vite 8 |
| **State Management** | Redux Toolkit 2, React Redux 9 |
| **HTTP Client** | Axios (with standardized error boundary) |
| **Typography** | Inter font stack |
| **Backend Framework** | Python 3.11+, FastAPI, Pydantic v2 |
| **ORM & Database** | SQLAlchemy v2, PostgreSQL, `psycopg2-binary`, Alembic |
| **AI Orchestration** | LangGraph, LangChain Core |
| **AI Model & Inference** | Groq API (`langchain-groq`), environment-configurable model |
| **Document Processing** | `pypdf` (in-memory PDF text extraction) |
| **Testing** | Pytest, HTTPX |

---

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             REACT 19 / VITE FRONTEND                            │
│  ┌───────────────────────────┐           ┌───────────────────────────────────┐  │
│  │   Left Complaint Panel    │           │         Right AI Copilot          │  │
│  │ (Form, Risk, CAPA, Dupes) │           │ (Chat, PDF Upload, Text Input)    │  │
│  └─────────────┬─────────────┘           └─────────────────┬─────────────────┘  │
│                └────────────────────┬──────────────────────┘                    │
│                                     │ Redux Toolkit State                       │
└─────────────────────────────────────┼───────────────────────────────────────────┘
                                      │ REST API (Axios)
┌─────────────────────────────────────▼───────────────────────────────────────────┐
│                               FASTAPI BACKEND                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                          LangGraph Workflow Engine                        │  │
│  │  START ──> normalize_input ──> extract_complaint ──> validate_complaint   │  │
│  │     ──> classify_complaint ──> assess_risk ──> recommend_action          │  │
│  │     ──> finalize_result ──> END                                           │  │
│  └───────────────────────────────┬───────────────────────────────────────────┘  │
│                                  │                                              │
│          ┌───────────────────────┴───────────────────────┐                      │
│          │                                               │                      │
│   ┌──────▼──────┐                                 ┌──────▼──────┐               │
│   │  Groq API   │                                 │ PostgreSQL  │               │
│   │ (LLM Engine)│                                 │ (SQLAlchemy)│               │
│   └─────────────┘                                 └─────────────┘               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Directory Structure

```
aivoa-complaint-intelligence/
├── AGENTS.md                   # Core project guidelines & specifications
├── README.md                   # Project documentation
├── backend/
│   ├── .env.example            # Environment template for backend
│   ├── run.py                  # Uvicorn entry point script
│   ├── requirements.txt        # Python dependency manifest
│   ├── app/
│   │   ├── main.py             # FastAPI application setup & router mounting
│   │   ├── ai/                 # LangGraph workflow, nodes, state & Groq service
│   │   │   ├── graph.py        # 7-node LangGraph pipeline builder
│   │   │   ├── groq_service.py # Groq client & extraction service
│   │   │   ├── state.py        # ComplaintState TypedDict definition
│   │   │   └── nodes/          # Individual workflow node implementations
│   │   ├── api/                # FastAPI APIRouter endpoints
│   │   │   ├── analysis.py     # POST /api/complaints/analyze
│   │   │   ├── complaints.py   # Full CRUD + duplicate detection routes
│   │   │   ├── documents.py    # PDF text extraction & analysis routes
│   │   │   └── health.py       # GET /api/health
│   │   ├── core/               # Configuration settings (Pydantic settings)
│   │   ├── db/                 # SQLAlchemy database session & ORM models
│   │   │   └── models/         # Complaint, Document, CopilotMessage, AuditEvent
│   │   ├── schemas/            # Pydantic validation schemas
│   │   └── services/           # PDF processing & Duplicate matching logic
│   └── tests/                  # Backend test suite (9 test files)
└── frontend/
    ├── .env.example            # Environment template for frontend
    ├── package.json            # Node.json dependency manifest
    ├── vite.config.js          # Vite build configuration
    ├── index.html              # HTML shell
    └── src/
        ├── App.css             # Main design system & layout styles
        ├── App.jsx             # Root React component
        ├── main.jsx            # React mounting entry point
        ├── app/                # Redux store configuration
        ├── components/
        │   ├── complaint/      # Form, Risk, CAPA, Completeness, Duplicate components
        │   ├── copilot/        # Copilot panel, Input bar, Message list
        │   ├── documents/      # Document upload component
        │   └── layout/         # AppShell navigation wrapper
        ├── features/           # Redux slices (complaints, copilot, risk, ui)
        └── services/           # Axios API client & endpoints
```

---

## 7. Prerequisites

Before running the application, ensure you have installed:
- **Python**: v3.11 or higher
- **Node.js**: v18.0 or higher (with `npm`)
- **PostgreSQL**: v14 or higher running locally or accessible via network
- **Groq API Key**: Obtain a free API key from [console.groq.com](https://console.groq.com)

---

## 8. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   - *Windows*:
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - *Linux / macOS*:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your PostgreSQL database credentials and Groq API key:
   ```ini
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aivoa_complaints
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   GROQ_MODEL=llama-3.3-70b-versatile
   PORT=8000
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

5. **Create the PostgreSQL database**:
   Run via your PostgreSQL CLI or GUI (`pgAdmin`, `psql`):
   ```sql
   CREATE DATABASE aivoa_complaints;
   ```
   *Note: Database tables are automatically initialized by SQLAlchemy on application startup.*

6. **Start the FastAPI backend server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Or run using the convenience script:
   ```bash
   python run.py
   ```
   The backend API will be available at `http://127.0.0.1:8000`. Interactive API documentation is accessible at `http://127.0.0.1:8000/docs`.

---

## 9. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Ensure `.env` contains:
   ```ini
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

4. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The application will be accessible in your web browser at `http://localhost:5173`.

---

## 10. Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example / Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/aivoa_complaints` |
| `GROQ_API_KEY` | Groq API Key for LLM inference | `gsk_...` |
| `GROQ_MODEL` | Selected LLM model for extraction | `llama-3.3-70b-versatile` (or `gemma2-9b-it`) |
| `PORT` | Backend service execution port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173,http://127.0.0.1:5173` |

> **Model Configuration Note**: While `AGENTS.md` specifies `gemma2-9b-it` as the primary target model, the system is fully model-agnostic. The runtime `GROQ_MODEL` environment variable controls which model is invoked during execution.

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL for FastAPI backend API | `http://127.0.0.1:8000` |

---

## 11. API Reference

| Endpoint | Method | Description | Request Body / Params |
|---|---|---|---|
| `/` | `GET` | API welcome & service metadata | None |
| `/api/health` | `GET` | Health check endpoint | None |
| `/api/complaints/analyze` | `POST` | Process raw text complaint via LangGraph | `{ "input_text": "...", "source_type": "email" }` |
| `/api/documents/extract-text` | `POST` | Extract raw text from PDF document | `multipart/form-data` (`file`) |
| `/api/documents/analyze` | `POST` | Upload PDF and run full AI analysis | `multipart/form-data` (`file`) |
| `/api/complaints` | `POST` | Save a new structured complaint to DB | `ComplaintCreate` JSON payload |
| `/api/complaints` | `GET` | Fetch paginated & filtered list of complaints | Query: `page`, `page_size`, `status`, `severity`, `product_name` |
| `/api/complaints/check-duplicates` | `POST` | Run rule-based duplicate check | `{ "product_name": "...", "batch_number": "...", "customer_name": "..." }` |
| `/api/complaints/{complaint_id}` | `GET` | Fetch single complaint details by ID | Path parameter `complaint_id` |
| `/api/complaints/{complaint_id}` | `PATCH` | Perform partial update on saved complaint | Path parameter `complaint_id` + partial JSON payload |
| `/api/complaints/{complaint_id}` | `DELETE` | Delete complaint & cascaded audit history | Path parameter `complaint_id` |
| `/docs` | `GET` | Auto-generated Swagger OpenAPI interface | None |

---

## 12. LangGraph Workflow

AI analysis follows an explicit 7-node sequential state graph:

1. **`normalize_input`**: Cleanses raw text, normalizes whitespace, and initializes the message state thread.
2. **`extract_complaint`**: Invokes Groq via `langchain-groq` using Pydantic structured output schemas to extract structured fields. Includes graceful fallback handling if `GROQ_API_KEY` is omitted.
3. **`validate_complaint`**: Inspects required core fields (`customer_name`, `product_name`, `batch_number`, `complaint_type`, `complaint_description`) and populates `missing_fields` and `validation_errors`.
4. **`classify_complaint`**: Maps the complaint to standard quality management categories.
5. **`assess_risk`**: Applies a negation-aware risk assessment engine to assign severity (Low, Medium, High, Critical) and risk levels (Minor, Major, Critical).
6. **`recommend_action`**: Generates recommended QA follow-up actions based on risk severity and missing information.
7. **`finalize_result`**: Formats the final response dictionary with confidence scoring ready for frontend hydration.

---

## 13. AI Structured Output Fields

The extraction engine attempts to populate the following structured parameters:

- `complaint_source`: Source channel (`email`, `web_form`, `pdf_upload`, `phone`, `letter`, `other`)
- `customer_name`: Name of customer or healthcare professional
- `product_name`: Commercial product name
- `product_strength`: Dosage / strength format (e.g., `250mg`, `10mg Tablets`)
- `batch_number`: Lot / Batch number
- `manufacturing_date`: Manufacturing date (`YYYY-MM-DD`)
- `expiry_date`: Expiration date (`YYYY-MM-DD`)
- `affected_quantity`: Numeric count of affected units
- `affected_quantity_unit`: Unit of measure (`tablets`, `capsules`, `vials`, `bottles`)
- `complaint_type`: Primary defect classification (`Quality`, `Efficacy`, `Packaging`, `Adverse Event`, `Other`)
- `complaint_date`: Reported date
- `complaint_description`: Full detailed summary of the issue
- `severity`: Assigned severity rating (`Low`, `Medium`, `High`, `Critical`)
- `risk_level`: Evaluated risk tier (`Minor`, `Major`, `Critical`)
- `initial_risk_assessment`: Detailed rationale for the assigned risk level
- `suggested_next_action`: Recommended QA / QMS immediate action
- `confidence`: AI confidence score (`0.0` to `1.0`)
- `missing_fields`: Array of missing core field keys

---

## 14. Risk Assessment Behavior

- **Safety & Negation Aware**: The risk engine recognizes explicit negations. For example:
  - *"Foreign particles found in capsules"* ➔ **Critical**
  - *"No foreign particles or contamination observed"* ➔ **Low**
- **Completeness Independence**: Missing optional fields (e.g., expiry date) raise informational warnings but do **not** artificially inflate or downgrade a genuine safety concern.
- **Human-in-the-Loop**: All AI risk ratings and actions are presented as advisory suggestions for QA review.

---

## 15. Sample Complaint Data

Use these sample complaint texts directly in the application interface to test the extraction and risk engine:

### Sample 1: Critical Contamination Report
```text
Dear QA Team, I am writing to report a serious concern regarding batch BC-2024-001 of Cardivex 10mg Tablets. Upon opening the bottle, I noticed what appeared to be black foreign particles embedded within several tablets. The product was purchased at MedPlus Pharmacy on October 15, 2024. I am extremely concerned about patient safety as I have already consumed 3 tablets from this batch before noticing the contamination. Customer: Dr. Sarah Mitchell, Contact: sarah.mitchell@hospital.org
```

### Sample 2: High Efficacy / Potency Complaint
```text
I have been taking Gluconorm 500mg tablets from batch GL-2024-089 for the past two weeks and my blood sugar levels are not being controlled as expected. The tablets from the new batch seem different from what I usually receive. I am concerned about the product potency. My name is John Reeves and my doctor is investigating this matter urgently.
```

### Sample 3: Medium Packaging Defect
```text
Customer complaint received from Mary Thompson regarding damaged packaging of Amoxicillin 250mg Capsules, batch AM-2024-055. Multiple capsules found broken in the blister pack. Manufacturing date January 2024, expiry March 2026. Quantity affected: approximately 15 capsules from a pack of 30. No adverse events reported but customer requests replacement.
```

### Sample 4: Low Risk Information Inquiry
```text
Customer Maya Nair has a general product information inquiry regarding Aivoa TestClear 250mg Capsules from batch LOWQA-2026-002. The customer is requesting clarification about the product's storage instructions. No product defect, damage, contamination, adverse event, potency issue, or safety concern has been reported. Complaint Type: Other.
```

---

## 16. Testing

The backend includes a comprehensive test suite covering API contracts, LangGraph nodes, database CRUD operations, PDF extraction, and duplicate detection (**84 passed tests across 9 test modules**, 100% pass rate).

### Execute All Backend Tests
```bash
cd backend
pytest tests/ -v
```

---

## 17. Production Build

To test or generate the production build for the React frontend:

```bash
cd frontend
npm run build
```

This compiles optimized static assets into `frontend/dist/`. To preview the production bundle locally:
```bash
npm run preview
```

---

## 18. Known Limitations

In accordance with project scope guidelines (`AGENTS.md`), the following features are intentionally out of scope:
- User Authentication & Multi-Tenancy (RBAC, JWT)
- Optical Character Recognition (OCR) for scanned image PDFs
- Direct Email Inbox Integration / SMTP Polling
- Production Kubernetes Deployment / Microservices Infrastructure
- Automated Regulatory Submissions or Automatic Recall Triggers

---

## 19. Security Notes

- **Secrets Management**: Environment variable template files (`.env.example`) contain placeholders only. Actual `.env` files containing secrets are gitignored.
- **Sanitization**: API loggers sanitize API keys before outputting trace logs.
- **CORS Restrictions**: Backend API CORS policy is restricted to local development origins (`localhost:5173`) by default.
