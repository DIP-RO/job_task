# Legal AI System Architecture
## System Overview
The Legal AI System is a full-stack application that automates legal document processing, draft generation, and collaborative editing. The architecture follows a modern microservices-inspired design with clear separation between frontend and backend, containerized for easy deployment.

## High-Level Architecture Diagram
```
┌─────────────────┐     ┌─────────────────────────────────────┐     ┌──────────────────┐
│   Frontend      │────▶│  Backend API Layer (FastAPI)        │────▶│  PostgreSQL/SQLite│
│  (Next.js 14)   │     │  - Controllers                      │     │  Database        │
│                 │     │  - Services                         │     │                  │
│  - Upload       │     │  - Workflows (LangGraph)            │     │  - Documents     │
│  - Generate     │     │  - AI/LLM Integration               │     │  - Drafts        │
│  - Edit         │     │  - OCR/Image Processing             │     │  - Edits         │
│  - History      │     │                                     │     │                  │
└─────────────────┘     └─────────────────────────────────────┘     └──────────────────┘
                              │         ▲
                              ▼         │
                        ┌───────────────────────┐
                        │  External Services    │
                        │  - OpenAI GPT-4o      │
                        │  - Tesseract OCR      │
                        │  - Redis (Caching)    │
                        └───────────────────────┘
```
![High-Level Architecture](https://i.imgur.com/7ZkQZ7L.png)  
*(Above: High-level component diagram showing data flow between all system parts)*

## Core Component Breakdown

### 1. Frontend Layer (Next.js 14)
**File Structure**: `/frontend/app/`, `/frontend/components/`
- **Single-Page Application**: All sections (Upload, Generate, All Drafts, Edit, History) rendered on one page
- **Key Components**:
  - `UploadSection.tsx`: Handles document upload, drag-and-drop, file validation
  - `GenerateSection.tsx`: Draft generation UI, type selection, learning patterns toggle
  - `AllDraftsSection.tsx**: NEW! Renders every draft from all documents in individual cards
  - `EditSection.tsx`: Draft editing, version control, feedback submission
  - `HistorySection.tsx`: Complete document/draft history with delete/view details
- **State Management**: React useState/useEffect with refreshKey pattern for forced re-renders
- **API Client**: Axios-based client in `/lib/api.ts` with error handling

### 2. Backend API Layer (FastAPI)
**File Structure**: `/backend/app/`
- **Controllers** (Route Handlers):
  - `document_controller.py`: CRUD for documents, upload processing, OCR triggering
  - `draft_controller.py`: Draft generation, retrieval, update, delete endpoints
  - `edit_controller.py`: Edit tracking, learning pattern extraction
- **Services**:
  - `draft_generator.py`: LLM integration (OpenAI), prompt engineering, draft structuring
  - `document_processor.py`: OCR (Tesseract), image enhancement, text extraction
  - `retrieval_service.py`: Vector search for relevant evidence passages
  - `edit_learning_service.py`: Learns from user edits to improve future drafts
- **Workflows**:
  - `document_workflow.py`: LangGraph orchestration for end-to-end document processing

### 3. Database Layer
**Schema Diagram**:
```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Documents     │       │     Drafts      │       │      Edits      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id              │◄──────┤ document_id     │◄──────┤ draft_id        │
│ filename        │       │ draft_type      │       │ original_content│
│ raw_text        │       │ draft_content   │       │ edited_content  │
│ processing_status│      │ version         │       │ feedback_category│
│ created_at      │       │ created_at      │       │ created_at      │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```
![Database Schema](https://i.imgur.com/5XQZ9yY.png)  
*(Above: Entity-Relationship diagram showing foreign key relationships and cascade deletions)*

## Data Flow Diagram
### Document Upload & Processing Flow
```
User Uploads File → Frontend sends POST /api/documents/upload
→ Backend saves file to disk → triggers document processing workflow
→ OCR extracts text → text stored in documents.raw_text
→ Document status updates to "completed" → Frontend polls for status
→ Document appears in Generate section's dropdown
```
![Upload Flow](https://i.imgur.com/9KdPZ7x.png)

### Draft Generation & Editing Flow
```
User selects document + draft type → Frontend sends POST /api/drafts/generate
→ Backend retrieves relevant evidence → calls OpenAI to generate draft
→ Draft saved to database → Frontend refreshes all sections
→ New draft appears in All Drafts + Edit section
→ User edits draft → sends PUT /api/drafts/{id} → draft version increments
→ Edit saved to edits table → learning service extracts patterns
```
![Draft Flow](https://i.imgur.com/3WqRf2L.png)

## Key Technical Decisions & Tradeoffs

### 1. Single-Page vs Multi-Page Frontend
**Decision**: Convert from tab-based navigation to single-page UI
**Tradeoffs**:
- ✅ Pros: All features accessible immediately, no routing complexity
- ❌ Cons: Larger initial bundle size, but mitigated by Next.js code splitting
- Why: User requested all content on one page to avoid context switching

### 2. Fallback Draft Content for LLM Failures
**Decision**: Add sample fallback draft when OpenAI API fails
**Tradeoffs**:
- ✅ Pros: Frontend never shows empty content, users can still edit
- ❌ Cons: Fallback content is generic, requires user input to refine
- Why: Prevent "0 characters" errors while maintaining core functionality

### 3. RefreshKey Pattern for State Sync
**Decision**: Use integer refreshKey to force component re-mounts
**Tradeoffs**:
- ✅ Pros: Simple cross-component state sync without complex state managers
- ❌ Cons: Unnecessary re-renders, but acceptable for small app scale
- Why: Avoided adding Redux/Zustand to keep dependencies minimal

### 4. Cascade Deletions for Related Records
**Decision**: Explicitly delete edits when draft is deleted, drafts when document is deleted
**Tradeoffs**:
- ✅ Pros: No orphaned records, database consistency
- ❌ Cons: Manual deletion code instead of ORM cascade (due to SQLite limitations)
- Why: Ensure complete cleanup of all related data

## Deployment Architecture
### Local Development
```
Frontend: localhost:3001 → Backend: localhost:8000 → Redis: localhost:6379 → SQLite: ./data/db/legal_ai.db
```
### Production (Dockerized)
```
┌─────────┐     ┌─────────┐     ┌────────────┐     ┌──────────┐
│ Nginx   │────▶│ FastAPI │────▶│ PostgreSQL │────▶│ Redis    │
│ (Reverse│     │ Backend │     │ Database   │     │ Caching  │
│ Proxy)  │     │         │     │            │     │          │
└─────────┘     └─────────┘     └────────────┘     └──────────┘
```
![Production Deployment](https://i.imgur.com/8XzYpLm.png)

## API Endpoint Architecture
All API endpoints follow REST conventions:
- `GET /api/documents` - List all documents
- `POST /api/documents/upload` - Upload new document
- `DELETE /api/documents/{id}` - Delete document + all drafts/edits
- `POST /api/drafts/generate` - Generate new draft
- `GET /api/drafts/document/{id}` - Get all drafts for a document
- `PUT /api/drafts/{id}` - Update existing draft
- `DELETE /api/drafts/{id}` - Delete draft + all edits
- `GET /api/edits/draft/{id}` - Get all edits for a draft

## Scalability Considerations
1. **Horizontal Scaling**: Backend API is stateless, can be deployed to multiple instances
2. **Database Sharding**: Split documents/drafts across multiple database shards by upload date
3. **Caching Layer**: Redis caches frequent LLM requests to reduce OpenAI API costs
4. **Async Processing**: Celery workers for long-running OCR/LLM tasks to avoid blocking API