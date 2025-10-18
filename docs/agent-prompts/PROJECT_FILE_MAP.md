# Project File Map & Structure

## 📋 Complete File Listing

This document provides a complete map of all files in the project, their purpose, and key details.

**Last Updated**: 2025-10-12
**Total Files**: ~40+ files across src/, tests/, docs/, and config

---

## Directory Structure

```
Simple RAG/
├── src/                      # Core application code
│   ├── __init__.py
│   ├── config.py             # Configuration & environment variables
│   ├── data_loader.py        # Multi-modal file processing
│   ├── text_processor.py     # Text chunking
│   ├── vector_store.py       # ChromaDB & embeddings
│   └── chatbot.py            # RAG pipeline orchestration
│
├── tests/                    # Test suite (pytest)
│   ├── __init__.py
│   ├── conftest.py           # Test configuration (CRITICAL)
│   ├── test_config.py        # Config tests
│   ├── test_data_loader.py   # Data loading tests
│   ├── test_text_processor.py # Chunking tests
│   ├── test_vector_store.py  # Vector DB tests
│   ├── test_e2e_rag_pipeline.py # End-to-end tests
│   └── fixtures/             # Test data (if any)
│
├── docs/                     # Documentation
│   ├── tasks/                # Original task specifications
│   │   ├── task0.md          # Docker setup
│   │   ├── task1.md          # Project structure
│   │   ├── task2.md          # Configuration
│   │   ├── task3.md          # PDF processing (vision-based)
│   │   ├── task4.md          # Audio/video transcription
│   │   ├── task5.md          # Directory loader
│   │   ├── task6.md          # Text chunking
│   │   ├── task7.md          # Vector database
│   │   ├── task8.md          # Embedding pipeline
│   │   ├── task9.md          # Context retrieval
│   │   ├── task10.md         # Prompt formatting
│   │   ├── task11.md         # Answer generation
│   │   ├── task12.md         # RAGChatbot class
│   │   ├── task13.md         # CLI interface
│   │   └── task14.md         # Documentation
│   └── agent-prompts/        # Handoff documentation (THIS DIRECTORY)
│       ├── REAL_WORLD_DEPLOYMENT_GUIDE.md  # Comprehensive deployment guide
│       ├── QUICK_TROUBLESHOOTING.md        # Fast issue resolution
│       ├── IMPLEMENTATION_NOTES.md         # Technical deep-dive
│       └── PROJECT_FILE_MAP.md             # This file
│
├── data/                     # Knowledge base files (NOT in git)
│   ├── knowledge.pdf         # Lecture PDF
│   ├── what-is-feedback-loop-in-rag.mp3  # Audio file
│   └── *.mp4                 # Video files (optional)
│
├── chroma_db/                # Vector database storage (NOT in git)
│   └── [ChromaDB files]      # Created automatically
│
├── main.py                   # CLI entry point
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker orchestration
├── .env.example              # Environment variable template
├── .env                      # Actual credentials (NOT in git)
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
├── README.md                 # User-facing documentation
├── IMPLEMENTATION_SUMMARY.md # Implementation overview
└── TEST_RESULTS.md           # Test execution results
```

---

## Core Application Files

### src/config.py
**Purpose**: Configuration management with environment variable validation
**Lines**: ~35
**Key Features**:
- Settings singleton pattern
- Fail-fast environment variable validation
- Default values for optional settings

**Dependencies**:
- `python-dotenv` - Load .env file
- `os` - Environment variables

**Critical Details**:
- Loaded at import time (line 31)
- Requires environment variables set before import
- Used by all other modules

**Key Variables**:
- `AZURE_OPENAI_API_KEY` - API authentication
- `AZURE_OPENAI_ENDPOINT` - API endpoint URL
- `OPENAI_API_VERSION` - API version
- `EMBEDDING_MODEL_NAME` - Embedding model deployment name
- `LLM_MODEL_NAME` - LLM model deployment name

**Testing**: `tests/test_config.py` (5 tests)

---

### src/data_loader.py
**Purpose**: Multi-modal document loading (PDF, audio, video)
**Lines**: ~150
**Key Functions**:
- `load_text_from_pdf()` - Vision-based PDF processing
- `transcribe_audio_file()` - Whisper audio transcription
- `load_video_and_transcribe()` - FFmpeg video processing
- `load_from_directory()` - Batch file loader

**Dependencies**:
- `pdf2image` - PDF to image conversion (requires Poppler)
- `PIL` - Image processing
- `base64` - Image encoding
- `ffmpeg-python` - Video processing (requires FFmpeg)
- `openai` - Azure OpenAI client

**System Dependencies**:
- Poppler (for pdf2image)
- FFmpeg (for video processing)

**Critical Details**:
- Lines 29-70: PDF vision processing (memory-intensive)
- Lines 73-91: Audio transcription (25MB limit)
- Lines 94-120: Video processing (temp file handling)
- Lines 123-150: Directory scanning and routing

**Testing**: `tests/test_data_loader.py` (8 tests, all mocked)

**Known Issues**:
- No progress indicators
- Memory issues with large PDFs
- Hardcoded Whisper model name (line 88)
- Temp file cleanup issues
- No partial failure handling

---

### src/text_processor.py
**Purpose**: Semantic text chunking with overlap
**Lines**: ~40
**Key Functions**:
- `chunk_text()` - Split documents into chunks

**Dependencies**:
- `langchain-text-splitters` - RecursiveCharacterTextSplitter

**Critical Details**:
- Lines 23-27: Chunker configuration (1000 chars, 200 overlap)
- Lines 32-38: Metadata preservation during chunking
- Character-based, not token-based

**Testing**: `tests/test_text_processor.py` (6 tests)

**Known Issues**:
- Fixed chunk size (not configurable)
- May split mid-sentence
- No deduplication

---

### src/vector_store.py
**Purpose**: ChromaDB integration and embedding generation
**Lines**: ~60
**Key Functions**:
- `get_vector_database_collection()` - Initialize/get ChromaDB collection
- `embed_and_store_chunks()` - Generate embeddings and store

**Dependencies**:
- `chromadb` - Vector database
- `numpy` - Must be < 2.0.0 for compatibility
- `openai` - Azure OpenAI client

**Critical Details**:
- Lines 24-32: ChromaDB persistent client
- Lines 35-59: Batch embedding generation
- Hardcoded collection name: "rag_collection"

**Testing**: `tests/test_vector_store.py` (5 tests, partially mocked)

**Known Issues**:
- No batch size limits (fails at 2048+ chunks)
- No retry logic
- No progress indicators
- No duplicate checking

---

### src/chatbot.py
**Purpose**: Complete RAG pipeline orchestration
**Lines**: ~120
**Key Functions**:
- `retrieve_relevant_context()` - Query embedding & vector search
- `format_prompt()` - Prompt engineering with context
- `generate_llm_answer()` - LLM answer generation

**Key Class**:
- `RAGChatbot` - High-level orchestrator

**Dependencies**:
- `openai` - Azure OpenAI client
- All other src modules

**Critical Details**:
- Lines 26-44: Context retrieval (top-3 chunks)
- Lines 47-62: Prompt template
- Lines 65-88: LLM generation (temp 0.7, max 500 tokens)
- Lines 91-121: RAGChatbot with auto-ingestion

**Testing**: `tests/test_e2e_rag_pipeline.py` (6 E2E tests)

**Known Issues**:
- No caching
- No streaming
- Basic prompt engineering
- No source attribution
- Temperature too high (0.7)

---

### main.py
**Purpose**: Interactive CLI entry point
**Lines**: ~97
**Key Functions**:
- `main()` - CLI loop

**Dependencies**:
- `src.chatbot.RAGChatbot`

**Critical Details**:
- Lines 44: Initialize chatbot (auto-ingest if empty)
- Lines 62-93: Interactive query loop
- Handles Ctrl+C gracefully
- Accepts 'quit', 'exit', 'q' to exit

**Testing**: Not directly tested (manual QA required)

---

## Test Files

### tests/conftest.py
**Purpose**: Test configuration and fixtures
**Lines**: ~15
**CRITICAL**: Sets environment variables at module level

**Why Critical**:
- Settings singleton loaded at import time
- Must set env vars BEFORE any test imports
- Without this, all tests fail

**Critical Details**:
```python
# Lines 1-8: Environment variables set at module level
os.environ["AZURE_OPENAI_API_KEY"] = "test_key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.endpoint.com/"
os.environ["OPENAI_API_VERSION"] = "2023-12-01-preview"
os.environ["EMBEDDING_MODEL_NAME"] = "text-embedding-ada-002"
os.environ["LLM_MODEL_NAME"] = "gpt-4o"
```

**Do NOT delete or modify** without understanding implications.

---

### tests/test_config.py
**Tests**: 5
**Coverage**: Configuration loading and validation
**Key Tests**:
- `test_settings_load_successfully` - Basic loading
- `test_settings_missing_api_key_raises_error` - Validation
- `test_settings_custom_model_names` - Defaults

---

### tests/test_data_loader.py
**Tests**: 8
**Coverage**: Multi-modal file processing
**Mocking**: Heavy (pdf2image, ffmpeg, Azure OpenAI)
**Key Tests**:
- `test_load_pdf_multimodal_successfully` - PDF vision
- `test_transcribe_audio_file_mocked` - Whisper
- `test_load_from_directory_handles_mp4` - Video processing

---

### tests/test_text_processor.py
**Tests**: 6
**Coverage**: Text chunking logic
**Mocking**: None (pure logic)
**Key Tests**:
- `test_chunking_basic` - Basic splitting
- `test_chunking_overlap` - Overlap verification
- `test_chunking_empty_document` - Edge cases

---

### tests/test_vector_store.py
**Tests**: 5
**Coverage**: Embeddings and ChromaDB
**Mocking**: Partial (Azure OpenAI mocked, ChromaDB real)
**Key Tests**:
- `test_db_initialization` - ChromaDB setup
- `test_embedding_and_storing` - Complete pipeline

---

### tests/test_e2e_rag_pipeline.py
**Tests**: 6 (1 skipped)
**Coverage**: End-to-end workflows
**Mocking**: Heavy (all APIs mocked)
**Key Tests**:
- `test_e2e_full_rag_workflow` - Complete RAG pipeline
- `test_e2e_error_handling_graceful_degradation` - Error handling
- `test_e2e_performance_with_large_dataset` - Scalability (50 chunks)
- `test_e2e_multi_format_processing_components` - PDF+Audio+Video

**Skipped Test**: `test_e2e_full_data_ingestion_pipeline_components`
- Reason: ChromaDB PersistentClient initialization issues with tmp_path
- All components tested separately

---

## Configuration Files

### requirements.txt
**Purpose**: Python dependencies
**Lines**: ~20
**Critical Dependencies**:
```
openai==1.6.1                    # Azure OpenAI SDK
chromadb==0.4.22                 # Vector database
numpy<2.0.0                      # CRITICAL: Pinned for ChromaDB
pdf2image==1.16.3                # PDF processing
ffmpeg-python==0.2.0             # Video processing
langchain-text-splitters==0.0.1  # Text chunking
python-dotenv==1.0.0             # Environment variables
pytest==7.4.3                    # Testing
pytest-mock==3.12.0              # Mocking
```

**Critical Note**: `numpy<2.0.0` is REQUIRED for ChromaDB compatibility.

---

### Dockerfile
**Purpose**: Container image definition
**Base**: `python:3.11-slim`
**System Packages**: `ffmpeg`, `poppler-utils`
**Working Dir**: `/app`
**Entry Point**: `python main.py`

**Critical Lines**:
- Line 14: `RUN apt-get install -y ffmpeg poppler-utils`
- Line 20: `COPY . .`
- Line 22: `CMD ["python", "main.py"]`

---

### docker-compose.yml
**Purpose**: Docker orchestration
**Service**: `chatbot`
**Volumes**:
- `./data:/app/data` - Knowledge base files
- `./chroma_db:/app/chroma_db` - Database persistence
**Environment**: Loaded from `.env` file
**Interactive**: `stdin_open: true`, `tty: true`

**Critical Details**:
- Volumes ensure data persists across container restarts
- `.env` file must exist in project root

---

### .env.example
**Purpose**: Template for environment variables
**Must Copy**: `cp .env.example .env`
**Required Variables**:
```env
AZURE_OPENAI_API_KEY="your_api_key_here"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
OPENAI_API_VERSION="2023-12-01-preview"
EMBEDDING_MODEL_NAME="text-embedding-ada-002"
LLM_MODEL_NAME="gpt-4o"
```

**User Action Required**: Update with actual credentials

---

### .gitignore
**Purpose**: Git ignore rules
**Key Ignores**:
- `.env` - Credentials
- `chroma_db/` - Database files
- `data/` - Knowledge base files
- `__pycache__/` - Python cache
- `.venv/` - Virtual environment
- `*.pyc` - Compiled Python

---

### .dockerignore
**Purpose**: Docker build ignore rules
**Key Ignores**:
- `.env` - Not included in image (mounted at runtime)
- `chroma_db/` - Not included in image (mounted at runtime)
- `data/` - Not included in image (mounted at runtime)
- `.git/` - Not needed in image
- Tests and documentation

---

## Documentation Files

### README.md
**Purpose**: User-facing documentation
**Sections**:
- Features overview
- Architecture diagram
- Prerequisites
- Quick start guide (Docker & local)
- Testing instructions
- Configuration reference
- Troubleshooting
- Usage examples

**Target Audience**: End users, developers setting up locally

---

### IMPLEMENTATION_SUMMARY.md
**Purpose**: Technical implementation overview
**Sections**:
- All tasks completed (0-14)
- Architecture breakdown
- Key technical decisions
- Testing strategy
- Deliverables checklist

**Target Audience**: Technical reviewers, project managers

---

### TEST_RESULTS.md
**Purpose**: Comprehensive test documentation
**Sections**:
- Test suite summary (29 passed, 1 skipped)
- Coverage breakdown by category
- What tests prove
- Testing achievements
- What's NOT tested (by design)

**Target Audience**: QA, technical reviewers

---

### docs/agent-prompts/REAL_WORLD_DEPLOYMENT_GUIDE.md
**Purpose**: Comprehensive deployment guide for real components
**Sections**:
- Complete implementation overview
- Critical assumptions & mocking
- Expected issues by component
- Azure OpenAI setup & verification
- File processing issues
- Troubleshooting checklist
- Performance considerations
- Cost estimates

**Target Audience**: Next agent/developer deploying with real APIs

---

### docs/agent-prompts/QUICK_TROUBLESHOOTING.md
**Purpose**: Fast issue resolution guide
**Sections**:
- Top 10 most common issues with fast fixes
- Testing sequence
- Emergency fallbacks
- Quick diagnostics

**Target Audience**: Developer troubleshooting during deployment

---

### docs/agent-prompts/IMPLEMENTATION_NOTES.md
**Purpose**: Technical deep-dive and design decisions
**Sections**:
- Module-by-module breakdown
- API integration patterns
- Mocking strategy
- Error handling gaps
- Performance bottlenecks
- Code patterns & anti-patterns
- Testing gaps
- Future improvements

**Target Audience**: Developer maintaining/extending codebase

---

### docs/agent-prompts/PROJECT_FILE_MAP.md
**Purpose**: Complete file listing and structure
**This File**: You are reading it!

---

## Data Files (Not in Git)

### data/knowledge.pdf
**Type**: PDF document
**Purpose**: Lecture content for RAG knowledge base
**Processing**: Vision-based (GPT-4o)
**Status**: User must provide

---

### data/what-is-feedback-loop-in-rag.mp3
**Type**: Audio file
**Purpose**: Lecture audio content
**Processing**: Whisper transcription
**Status**: User must provide

---

### data/*.mp4
**Type**: Video files
**Purpose**: Additional lecture content (optional)
**Processing**: FFmpeg audio extraction + Whisper
**Status**: Optional, user provides if available

---

## Database Files (Not in Git)

### chroma_db/
**Type**: Directory
**Purpose**: ChromaDB persistent storage
**Contents**: SQLite database files, metadata
**Status**: Created automatically on first run
**Location**: Project root (mounted in Docker)

**Important**:
- Delete this directory to re-ingest data
- Contains all embeddings and metadata
- Should persist across runs

---

## File Statistics

| Category | Files | Lines of Code | Status |
|----------|-------|---------------|--------|
| Core Application | 5 | ~405 | ✅ Complete |
| Tests | 6 | ~800 | ✅ Complete |
| Documentation | 7 | ~2500 | ✅ Complete |
| Configuration | 5 | ~100 | ✅ Complete |
| **Total** | **23** | **~3805** | **✅ Complete** |

---

## Dependency Graph

```
main.py
  └─ src/chatbot.py
       ├─ src/data_loader.py
       │    ├─ src/config.py
       │    ├─ pdf2image (system: Poppler)
       │    ├─ ffmpeg-python (system: FFmpeg)
       │    └─ openai (Azure OpenAI)
       │
       ├─ src/text_processor.py
       │    └─ langchain-text-splitters
       │
       ├─ src/vector_store.py
       │    ├─ src/config.py
       │    ├─ chromadb (requires numpy<2.0)
       │    └─ openai (Azure OpenAI)
       │
       └─ src/config.py
            └─ python-dotenv
```

---

## Critical File Relationships

### Configuration Flow
```
.env → python-dotenv → src/config.py → All other modules
```

### Data Ingestion Flow
```
data/ → src/data_loader.py → src/text_processor.py → src/vector_store.py → chroma_db/
```

### Query Flow
```
User input → src/chatbot.py (ask)
  → retrieve_relevant_context (query chroma_db/)
  → format_prompt
  → generate_llm_answer
  → Answer output
```

### Testing Flow
```
tests/conftest.py (set env vars)
  → pytest discovers tests
  → tests/test_*.py (mock APIs)
  → src/* (tested with mocks)
```

---

## Files Modified vs Created

### Created from Scratch (All)
- All src/ files
- All tests/ files
- All documentation files
- All configuration files

**Total Lines Written**: ~3800+

---

## Next Steps Checklist

### For Real-World Deployment:

**Phase 1: Setup**
- [ ] Copy `.env.example` to `.env`
- [ ] Add real Azure OpenAI credentials to `.env`
- [ ] Verify deployment names match `.env` values
- [ ] Install system dependencies (FFmpeg, Poppler)
- [ ] Install Python dependencies (`pip install -r requirements.txt`)

**Phase 2: Testing**
- [ ] Run component tests (see QUICK_TROUBLESHOOTING.md)
- [ ] Test with real PDF file
- [ ] Test with real audio file
- [ ] Test with real video file (optional)
- [ ] Run full ingestion test
- [ ] Run RAG pipeline test

**Phase 3: Deployment**
- [ ] Build Docker image
- [ ] Test Docker container
- [ ] Run main.py locally or in container
- [ ] Verify all features work
- [ ] Generate qa_log.txt with test questions

---

## Summary

**Project Structure**: Clean, modular, well-documented
**Code Quality**: Production-ready with caveats (see IMPLEMENTATION_NOTES.md)
**Testing**: Comprehensive unit & E2E tests (all mocked)
**Documentation**: Extensive (README, guides, troubleshooting)
**Deployment**: Docker-first, one-command setup

**Ready for**: Real-world integration testing
**Not Ready for**: Production deployment (needs real API testing)

**Estimated Lines of Code**: ~3,800
**Estimated Time to Build**: 6-8 hours
**Estimated Time to Deploy**: 2-4 hours (with troubleshooting)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-12
**Maintained By**: Development team

For questions about specific files, see the corresponding sections in:
- IMPLEMENTATION_NOTES.md (technical details)
- REAL_WORLD_DEPLOYMENT_GUIDE.md (deployment info)
- QUICK_TROUBLESHOOTING.md (common issues)
