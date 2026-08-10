# AIVOA Complaint Intelligence — Agent Instructions

## Project

Build an AI-powered Pharmaceutical Customer Complaint Management System
for the AIVOA AI Product Engineer internship assignment.

Project name:

AIVOA Complaint Intelligence

## Primary objective

A QA/QMS user must be able to:

1. Paste a customer complaint/email/text.
2. Upload a complaint PDF.
3. Send the input for AI analysis.
4. Extract structured complaint information.
5. Populate the complaint form.
6. Perform AI-assisted risk assessment.
7. Review and correct AI-generated information through the AI Copilot.
8. Save the complaint to PostgreSQL.
9. View saved complaints.
10. Use selected AI bonus features.

The system should behave as an AI Copilot for a pharmaceutical QA workflow,
not as an autonomous decision-making system.

---

# MANDATORY TECHNOLOGY STACK

Frontend:

- React
- Vite
- Redux Toolkit
- React Redux
- Axios
- Google Inter font

Backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy

AI:

- LangGraph
- Groq
- Primary model: gemma2-9b-it

Database:

- PostgreSQL

Document processing:

- PDF text extraction
- Production-grade OCR is NOT required

---

# LOCKED ARCHITECTURE

Frontend:
React
↓
Redux Toolkit
↓
FastAPI

Backend:
FastAPI
↓
LangGraph
↓
Groq / gemma2-9b-it

Persistence:
FastAPI / SQLAlchemy
↓
PostgreSQL

Do NOT replace these technologies with:

- Node.js
- Express
- MongoDB
- Next.js
- Firebase
- Supabase
- OpenAI
- Gemini
- another AI orchestration framework

unless explicitly instructed by the project owner.

---

# CORE USER WORKFLOW

Text input:

User complaint
↓
React
↓
POST /api/complaints/analyze
↓
FastAPI
↓
LangGraph
↓
Structured complaint result
↓
Redux
↓
Complaint form + risk assessment

PDF input:

PDF
↓
FastAPI upload
↓
PDF text extraction
↓
LangGraph
↓
Structured complaint result
↓
Redux
↓
Complaint form + risk assessment

Conversational correction:

User correction
↓
FastAPI
↓
LangGraph / complaint context
↓
Structured field updates
↓
Redux
↓
Complaint form

Save:

Reviewed complaint
↓
POST /api/complaints
↓
PostgreSQL

---

# LANGGRAPH WORKFLOW

The main LangGraph workflow must contain explicit nodes:

START
↓
normalize_input
↓
extract_complaint
↓
validate_complaint
↓
classify_complaint
↓
assess_risk
↓
recommend_action
↓
finalize_result
↓
END

Keep the LangGraph implementation explicit and understandable.

Do not hide the complete AI workflow inside one giant function.

---

# STRUCTURED AI OUTPUT

The LLM must produce structured data.

Core fields:

- complaint_source
- customer_name
- product_name
- product_strength
- batch_number
- manufacturing_date
- expiry_date
- affected_quantity
- affected_quantity_unit
- complaint_type
- complaint_date
- complaint_description
- severity
- risk_level
- initial_risk_assessment
- suggested_next_action
- confidence
- missing_fields

The AI must NOT invent unavailable information.

Missing information must be explicitly represented.

---

# RISK ASSESSMENT

AI should provide:

- severity
- risk level
- reasoning
- suggested next action
- confidence

Application-level validation/rules may supplement AI output.

The system must present AI results as recommendations for human review.

Never present AI output as an automatically approved pharmaceutical quality decision.

Never claim that the system automatically initiates recalls,
regulatory actions, or other high-impact pharmaceutical decisions.

---

# CORE FRONTEND

Use a polished two-panel workflow inspired by the provided AIVOA reference:

Left:

- Log Customer Complaint form
- Complaint fields
- AI Risk Assessment
- Save Complaint

Right:

- AI Copilot
- Complaint text input
- PDF upload
- Conversation
- Processing state
- AI responses

The UI does NOT need to pixel-match the reference screenshot.

Prioritize:

- clean SaaS-style design
- professional pharmaceutical/QMS appearance
- excellent spacing
- clear hierarchy
- responsive layout
- useful loading/error/empty states

---

# REDUX STRUCTURE

Use Redux Toolkit.

Suggested slices:

- complaintSlice
- copilotSlice
- riskSlice
- uiSlice

Redux must be meaningfully used for shared application state.

Do not install Redux and then manage everything through local component state.

---

# DATABASE

Use PostgreSQL.

Core tables:

complaints
complaint_documents
copilot_messages
audit_events

Use SQLAlchemy models.

Do not over-engineer database architecture.

---

# BONUS FEATURES

Implement exactly these three bonus features if time permits:

1. Complaint Completeness Checker
2. Duplicate Complaint Detection
3. CAPA Recommendation

Do NOT attempt all possible bonus features.

Do NOT build:

- authentication
- multi-tenancy
- complex RBAC
- full QMS
- production OCR
- email integration
- Kubernetes
- microservices
- complex vector database
- full CAPA lifecycle
- large admin dashboard

Focus on the assignment workflow.

---

# CODE QUALITY RULES

Prefer:

- small modules
- clear naming
- typed Pydantic schemas
- reusable services
- explicit error handling
- meaningful comments only where needed
- clean API boundaries
- separation of AI, API, database and UI responsibilities

Avoid:

- giant files
- duplicated logic
- magic values
- hardcoded API keys
- hardcoded database credentials
- unnecessary abstractions
- premature optimization

---

# SECURITY

Never commit:

- .env
- API keys
- database passwords
- secrets

Create:

.env.example

Use environment variables.

---

# DEVELOPMENT PROCESS

Before making major changes:

1. Inspect the existing repository.
2. Explain the proposed implementation.
3. Identify files that will change.
4. Implement incrementally.
5. Run relevant tests/checks.
6. Fix errors.
7. Verify the result.
8. Summarize changes.

Do not rewrite working code unnecessarily.

Do not introduce new libraries unless there is a clear reason.

---

# IMPORTANT

The project must remain understandable to the developer.

Do not generate large amounts of code without explaining:

- what it does
- why it exists
- how it connects to the architecture

The final implementation must be explainable during an internship interview.

The company explicitly expects the candidate to understand and explain
the implementation and may ask the candidate to modify or extend it.

---

# FINAL DEMONSTRATION

The final demo must be able to show:

1. Paste complaint
2. AI extraction
3. Form population
4. AI risk assessment
5. Conversational correction
6. PDF upload
7. PDF extraction
8. Complaint saving
9. Duplicate detection
10. CAPA recommendation

Then demonstrate the code path:

Frontend
→ API
→ FastAPI
→ LangGraph
→ Groq
→ structured result
→ Redux
→ form/risk assessment
→ PostgreSQL

The final repository must include:

- README
- architecture documentation
- setup instructions
- .env.example
- sample complaint data
- clean Git history
