# Legal AI Document Processing System

A full-stack AI-powered legal document processing system that analyzes documents, extracts information, and generates professional legal drafts (case summaries, checklists, memos, etc.) with grounding scores and supporting evidence.

## 🎯 Core Features

### Document Management
- **Upload & Processing**: Drag-and-drop document upload (PDF, DOCX, TXT, images)
- **OCR Extraction**: Automatic text extraction with configurable OCR providers (Tesseract, PaddleOCR, EasyOCR)
- **Quality Scoring**: OCR quality metrics for each document
- **Document Details**: Full metadata, extracted text preview, processing status

### AI Draft Generation
- **Multiple Draft Types**:
  - **Case Summary**: Structured legal case analysis with parties, claims, and relief sought
  - **Notice Summary**: Regulatory/notice analysis with deadlines and requirements
  - **Checklist**: Compliance verification checklist with risk levels and red flags
  - **Memo**: Internal legal memorandum with analysis and recommendations
  - **Title Review**: Real estate title examination report

### Quality Metrics
- **Grounding Score**: How well draft content is supported by source evidence (0-100%)
- **Completeness Score**: How thoroughly all document information is covered (0-100%)
- **Supporting Evidence**: Retrieved evidence chunks with similarity scores

### Learning System
- **Edit Recording**: Capture operator edits with reasoning and feedback categories
- **Pattern Learning**: Extract improvement patterns from edits
- **Context Preservation**: Use learned patterns in future generations for this document

### Professional UI
- **Modal-Based Workflow**: Focused, distraction-free editing experience
- **Detail Views**: Complete draft information with all supporting evidence
- **Side-by-Side Editing**: Compare original and edited content
- **Quick Actions**: View, Edit, Delete operations throughout interface

### Architecture Diagrams
![High-Level Architecture](https://i.imgur.com/7ZkQZ7L.png)  
*High-level component diagram showing data flow between all system parts*

![Database Schema](https://i.imgur.com/5XQZ9yY.png)  
*Entity-Relationship diagram showing foreign key relationships and cascade deletions*

![Upload Flow](https://i.imgur.com/9KdPZ7x.png)  
*Document upload & processing workflow*

![Draft Flow](https://i.imgur.com/3WqRf2L.png)  
*Draft generation, editing, and version control flow*

---

## 🏗️ Architecture

### Technology Stack
```
Frontend:
  - Next.js 14 (React)
  - TypeScript
  - Tailwind CSS
  - Axios for API calls

Backend:
  - FastAPI (Python)
  - SQLAlchemy ORM
  - SQLite (development) / PostgreSQL (production)
  - ChromaDB (vector database)
  - LangChain (LLM orchestration)
  - OpenAI GPT-4o (LLM)

OCR & Processing:
  - PyPDF2 / pdf2image (PDF handling)
  - Tesseract / PaddleOCR / EasyOCR (Text extraction)
  - pandas (Data extraction)
```

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Upload Section │ Generate Section │ History Section│ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │    DraftDetailModal    │    EditModal             │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Document Controller  │  Draft Controller │ Edit    │ │
│  │ - Upload            │  - Generate       │ Ctrl    │ │
│  │ - Process           │  - Retrieve       │         │ │
│  │ - Delete            │  - Update         │ - Record│ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Services Layer                                      │ │
│  │ - DocumentProcessor (OCR, text extraction)         │ │
│  │ - DraftGenerator (LLM prompt engineering)          │ │
│  │ - RetrievalService (semantic search, evidence)     │ │
│  │ - EditLearningService (pattern extraction)         │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Data Layer                                          │ │
│  │ - SQLite/PostgreSQL (Documents, Drafts, Edits)     │ │
│  │ - ChromaDB (Vector embeddings for retrieval)       │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

#### Generation Flow
```
1. User uploads document
   ↓
2. Backend processes:
   - OCR extraction
   - Text chunking (1000 char chunks, 200 overlap)
   - Vector embedding (ChromaDB)
   - Metadata extraction
   ↓
3. User selects draft type and generates
   ↓
4. Backend retrieves:
   - Top K similar chunks (K=5)
   - Learned patterns for this document (if any)
   ↓
5. LLM generates draft:
   - System prompt with professional role definition
   - Document context and retrieved evidence
   - Learned edit patterns
   ↓
6. Draft returned with:
   - Generated content
   - Grounding score
   - Completeness score
   - Supporting evidence with citations
```

#### Learning Flow
```
1. User edits draft in modal
2. Records edit with:
   - Original content
   - Edited content
   - Feedback category (grounding, clarity, etc.)
   - Reasoning for change
   ↓
3. Backend analyzes edit:
   - Identifies change patterns
   - Extracts improvement principles
   - Stores in edit history
   ↓
4. Next generation:
   - Retrieves edit patterns for this document
   - Includes in LLM prompt as "learned patterns"
   - Encourages similar improvements
```

---

## 📋 Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o              # Model to use
OPENAI_TEMPERATURE=0.0           # Low for deterministic output
OPENAI_MAX_TOKENS=2000          # Max completion length

# OCR Configuration
OCR_PROVIDER=tesseract           # Options: tesseract, paddle, easyocr
OCR_LANG=eng                     # Language
OCR_QUALITY_THRESHOLD=0.7        # Min quality score

# Database
DATABASE_URL=sqlite:///./data/db/legal_ai.db
CHROMA_DB_PATH=./data/vector_db

# Optional: LangSmith Tracing
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=legal-ai-system
```

### System Prompts

Each draft type uses a specialized system prompt to guide LLM output:

**Checklist Prompt Features:**
- Professional audit format
- Mandatory evidence references with section/page numbers
- Risk level assignment (Critical/High/Medium/Low)
- Responsible party specification
- Red flag indicators
- Verification criteria
- Timeline and deadline tracking
- Specific consequences for non-compliance

**Case Summary Prompt Features:**
- Structured case information section
- Complete procedural history timeline
- All material facts with citations
- Each legal claim with basis
- Specific relief requested
- Court-admissible format
- No speculation allowed

**Notice Summary Prompt Features:**
- Structured regulatory format
- Required action items with deadlines
- Compliance obligations
- Penalty/consequence specification
- Responsible party identification
- Appeal mechanism details

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL or SQLite
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app.models.database

# Run server
python run.sh
# OR manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Visits http://localhost:3000

# Build for production
npm run build
npm start
```

---

## 📊 Sample Usage Scenarios

See `samples/` directory for:
- Synthetic sample documents
- Expected output examples
- Simulated operator edits
- API request/response samples

### Quick Start Example

**1. Upload a Document**
```
Navigate to "Upload Document" section
Drag and drop a PDF or click to select
Wait for processing to complete (status changes to "COMPLETED")
```

**2. Generate a Draft**
```
Go to "Generate Draft" section
Select the uploaded document from dropdown
Choose draft type (e.g., "Case Summary")
Click "Generate Draft"
View results instantly in the section
```

**3. Review & Edit**
```
In the generated draft, click "View Full Details" to see all evidence
Click "Edit & Improve" to open the editing modal
Make changes in the right column
Add reasoning for changes
Click "Record Edit & Learn"
```

**4. Check History**
```
View all documents and drafts in "History & All Documents"
Use filter buttons to show documents or drafts only
Click "View Details" to open detail modal
Click "Edit" to modify a draft
Click "Delete" to remove items
```

---

## 🧪 Testing

### Run Tests
```bash
cd backend
pytest tests/ -v

# Coverage report
pytest tests/ --cov=app --cov-report=html
```

### Test Coverage
- Unit tests for document processing
- Integration tests for draft generation
- End-to-end tests for full workflows
- Evidence retrieval validation

---

## 🔍 Monitoring & Debugging

### Logging
```
Logs Location: ./data/logs/app.log

Log Levels:
- INFO: Normal operations
- WARNING: Potential issues (low OCR score, etc.)
- ERROR: Failed operations
- DEBUG: Detailed execution traces (when DEBUG=true)
```

### Common Issues

**Issue: Generated draft disappears after clicking buttons**
- **Cause**: Refresh mechanism was resetting component state
- **Fix**: Updated GenerateSection to preserve draft without refresh
- **Result**: Drafts now stay visible until you explicitly clear them

**Issue: Low OCR Quality Score**
- **Cause**: Document image quality or text density
- **Solution**: Try different OCR provider or upload clearer image

**Issue: Low Grounding Score**
- **Cause**: Poor evidence retrieval or context mismatch
- **Solution**: Increase `TOP_K_RESULTS` or lower `SIMILARITY_THRESHOLD`

---

## 📁 Project Structure

```
legal-ai-system/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   │   └── settings.py           # Configuration & system prompts
│   │   ├── controllers/              # API routes
│   │   │   ├── document_controller.py
│   │   │   ├── draft_controller.py
│   │   │   └── edit_controller.py
│   │   ├── services/                 # Business logic
│   │   │   ├── document_processor.py
│   │   │   ├── draft_generator.py
│   │   │   ├── retrieval_service.py
│   │   │   └── edit_learning_service.py
│   │   ├── models/
│   │   │   ├── entities.py           # SQLAlchemy models
│   │   │   ├── schemas.py            # Request/response models
│   │   │   └── database.py           # DB initialization
│   │   └── main.py                   # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   └── run.sh
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  # Main page
│   │   └── layout.tsx                # Layout
│   ├── components/
│   │   ├── DraftDetailModal.tsx      # Draft detail view
│   │   ├── EditModal.tsx              # Draft editing
│   │   ├── sections/                  # Page sections
│   │   │   ├── UploadSection.tsx
│   │   │   ├── GenerateSection.tsx
│   │   │   ├── EditSection.tsx
│   │   │   └── HistorySection.tsx
│   │   └── UI.tsx                     # Reusable components
│   ├── lib/
│   │   ├── api.ts                     # API client
│   │   ├── types.ts                   # TypeScript types
│   │   └── utils.ts                   # Utilities
│   └── hooks/
│       └── useDocuments.ts            # Custom hook
├── samples/                           # Sample documents & outputs
├── docs/                              # Additional documentation
├── README.md                          # This file
└── docker-compose.yml
```

---

## 📝 Key Features By Use Case

### For Paralegals
- Quickly extract key information from legal documents
- Generate standardized case summaries for filing
- Create compliance checklists from regulatory documents
- Track evidence sources for each claim

### For Compliance Teams
- Auto-generate compliance checklists from regulatory notices
- Capture specific deadlines and responsible parties
- Record compliance improvements through edits
- Maintain audit trail of all changes

### For Legal Operations
- Manage document processing workflows
- Monitor quality metrics (grounding, completeness scores)
- Extract patterns from operator edits
- Improve drafts over time through machine learning

---

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f app
```

---

**Last Updated:** May 2024
**Version:** 1.0.0