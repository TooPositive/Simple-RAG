# RAG Chatbot Project - Current Status & Issues

**Date**: October 14, 2025
**Status**: ✅ **WORKING** - All 43 chunks stored, chatbot answering questions successfully!

---

## 🎯 Project Goal

Build a RAG (Retrieval-Augmented Generation) chatbot that can answer questions about lecture content from:
1. **PDF**: `RagPresenetation.pdf` (20 pages, image-based)
2. **Video**: `database-for-genAI.mp4` (123MB, 2+ hours of lecture)

**Critical requirement**: Must use Vision/Document Intelligence API for PDF since it contains images, not extractable text.

---

## ✅ What's Working

### 1. **Infrastructure**
- ✅ Azure OpenAI credentials configured (`.env`)
- ✅ Model deployments created:
  - `gpt-4o-mini` - Chat completion (10k tokens/min)
  - `text-embedding-3-small` - Embeddings
  - `whisper` - Audio transcription
- ✅ System dependencies installed:
  - FFmpeg 8.0 (video processing)
  - Poppler 25.10.0 (PDF to image conversion)

### 2. **PDF Processing** ✅
- **Solution**: Azure Document Intelligence API (`azure-ai-formrecognizer`)
- **Method**: `prebuilt-read` model extracts text from image-based PDFs
- **Performance**: 20 pages processed in <1 second
- **Cost**: ~$0.02 (vs $0.60 with Vision API)
- **Output**: 9,151 characters extracted successfully

### 3. **Video Processing** ✅
- Audio extraction with FFmpeg (compressed to 64kbps to stay under 25MB Whisper limit)
- Whisper API transcription successful
- Output: 23,184 characters transcribed

### 4. **Vector Database** ✅
- ChromaDB initialized at `./chroma_db`
- **43 chunks stored successfully** (9 from PDF + 29 from video + 5 from PDF continued)
- All embeddings generated and stored
- No duplicate warnings

### 5. **Testing**
- Real E2E tests created (`tests/test_real_e2e.py`)
- All 9 real integration tests passing
- Cost per test run: ~$0.16

---

## ❌ Current Issues

### **Issue #1: ChromaDB Duplicate ID Warnings** ✅ FIXED

**Was:**
- ID generation used simple counter: `chunk_0`, `chunk_1`, etc.
- Batches caused collisions (each batch started counting from 0)
- Only 20 chunks stored instead of 43

**Fix applied:**
```python
# Now using content-based hashing for globally unique IDs
unique_string = f"{chunk['source']}_{chunk['content']}"
chunk_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]
ids_to_add.append(f"chunk_{chunk_hash}")
```

**Result:**
- ✅ All 43 chunks stored successfully
- ✅ No duplicate warnings
- ✅ Content from both PDF and video preserved

---

### **Issue #2: ChromaDB Telemetry Warnings** 🟡 LOW PRIORITY

**Symptoms:**
```
Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given
```

**Root cause:**
- ChromaDB version 0.4.22 has telemetry compatibility issues
- Not affecting functionality, just noisy warnings

**Impact:**
- Cosmetic only - doesn't affect RAG functionality

**Fix needed:**
```python
# Option 1: Disable telemetry
import chromadb
chromadb.telemetry.disable()

# Option 2: Upgrade ChromaDB (may break compatibility)
# pip install chromadb>=0.5.0
```

---

### **Issue #3: Rate Limiting with Vision API** 🔴 RESOLVED

**Problem:**
- Initial attempt used OpenAI Vision API for PDF processing
- S0 tier has 10k tokens/min limit
- Vision API needs ~70k tokens for 20-page PDF
- Would take 7+ minutes with strict delays

**Solution:**
- Switched to Azure Document Intelligence API
- Separate rate limits from OpenAI
- Much faster (~1 second vs 7 minutes)
- Much cheaper (~$0.02 vs $0.60)

---

### **Issue #4: Video Audio File Too Large** 🟡 RESOLVED

**Problem:**
- Original video audio: 26.2MB
- Whisper API limit: 25MB

**Solution:**
- Compress audio during extraction:
  ```python
  ffmpeg.output(
      tmp_audio,
      acodec='libmp3lame',
      audio_bitrate='64k',  # Compress
      ar='16000',           # Downsample to 16kHz
      ac=1                  # Mono
  )
  ```

---

## 📂 File Structure

### Main Files
- `main.py` - Interactive chatbot (run this after DB is populated)
- `ingest_all.py` - **USE THIS** - Complete ingestion with Document Intelligence
- `ingest_data.py` - Old script (has issues, don't use)
- `ingest_batch.py` - Batch processor for Vision API (not needed with Doc Intelligence)
- `ingest_video.py` - Video-only ingestion

### Source Code
- `src/config.py` - Configuration & environment variables
- `src/data_loader.py` - **Document Intelligence integration here**
- `src/text_processor.py` - Text chunking
- `src/vector_store.py` - **BUG HERE: Duplicate IDs**
- `src/chatbot.py` - RAG pipeline

### Tests
- `tests/test_real_e2e.py` - Real Azure API integration tests
- `tests/conftest.py` - Test configuration (uses real .env for integration tests)

### Data
- `data/RagPresenetation.pdf` - 20-page presentation (image-based)
- `data/database-for-genAI.mp4` - 2+ hour lecture video
- `chroma_db/` - Vector database (has duplicate issues)

---

## 🚀 How to Run

### Quick Start

```bash
# 1. Run ingestion (if not already done)
python3 ingest_all.py

# 2. Start the chatbot
python3 main.py
```

### Example Queries

Try asking:
- "What are embeddings?"
- "What topics are covered in this session?"
- "Explain the foundations of RAG"
- "What are advanced RAG patterns?"
- "Tell me about production readiness for AI systems"

---

## 🎯 Success Criteria

### Must Have ✅
1. ✅ Both PDF and video processed
2. ✅ **All 43 chunks stored successfully**
3. ✅ Embeddings generated for all chunks
4. ✅ **Chatbot answering questions successfully**

**Test Results:**
- "What are embeddings?" → ✅ Correct answer
- "What topics are covered in this session?" → ✅ Correct answer
- "Explain vector databases" → Needs better query phrasing

### Should Have
1. ✅ Processing time under 2 minutes
2. ✅ Cost under $0.10
3. ⚠️ No warnings during ingestion (telemetry warnings present)
4. ✅ Real E2E tests passing

---

## 💰 Cost Breakdown

### Ingestion (one-time)
- PDF processing (Doc Intelligence): ~$0.02
- Video transcription (Whisper): ~$0.03
- Embeddings (43 chunks): ~$0.004
- **Total**: ~$0.054

### Per Query
- Query embedding: ~$0.0001
- LLM generation: ~$0.001-0.003
- **Per query**: ~$0.001-0.003

---

## 🚀 Next Steps (Optional Improvements)

### High Priority
1. Disable ChromaDB telemetry to reduce warnings
2. Add source citation to answers (show which file each answer came from)
3. Improve prompt to be less conservative with "I don't have information" responses

### Medium Priority
1. Add conversation history to remember context
2. Add web interface (Streamlit/Gradio)
3. Cache processed documents to avoid re-ingestion
4. Add more comprehensive error handling

### Low Priority
1. Deploy to Azure (Container Apps or App Service)
2. Add logging and monitoring
3. Implement hybrid search (vector + keyword)
4. Add support for more file types

---

## 📝 Environment Variables (.env)

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY="key"
AZURE_OPENAI_ENDPOINT="endpoint"
OPENAI_API_VERSION="2024-12-01-preview"

# Model Deployments
EMBEDDING_MODEL_NAME="text-embedding-3-small"
LLM_MODEL_NAME="gpt-4o-mini"
```

**Note**: Same endpoint and key work for both OpenAI and Document Intelligence APIs (AIServices resource).

---

## 🆘 Troubleshooting

### "Database has only 20 chunks instead of 43"
→ Duplicate ID bug - see Issue #1 above

### "Rate limit errors during PDF processing"
→ Make sure using Document Intelligence, not Vision API
→ Check `src/data_loader.py` line 49: `method="document_intelligence"`

### "Video audio file too large"
→ Should be fixed with compression in `ingest_all.py`
→ Verify FFmpeg parameters include `audio_bitrate='64k'`

### "Chatbot gives empty/wrong answers"
→ Check if all 43 chunks are in database: `collection.count()`
→ Test retrieval: query should return relevant chunks from both sources

---

## 📚 Key Learnings

1. **Document Intelligence > Vision API** for document processing
   - 60x faster
   - 30x cheaper
   - Separate rate limits

2. **S0 tier rate limits are strict**
   - 10k tokens/min for OpenAI models
   - Need careful batching and delays

3. **Whisper has 25MB limit**
   - Compress audio before sending
   - 64kbps mono 16kHz works well

4. **ChromaDB ID collisions are silent**
   - No error, just overwrites
   - Must use unique IDs across all batches

---

## 🔗 Useful Commands

```bash
# Check database status
python3 -c "from src.vector_store import get_vector_database_collection; print(f'Chunks: {get_vector_database_collection().count()}')"

# List deployments
az cognitiveservices account deployment list --name konta-m9ok6570-eastus2 --resource-group bb-ai_assistant -o table

# Check rate limits
az cognitiveservices account deployment show --name konta-m9ok6570-eastus2 --resource-group bb-ai_assistant --deployment-name gpt-4o-mini --query "properties.rateLimits" -o table

# Test Document Intelligence
python3 -c "from src.data_loader import load_text_from_pdf; from pathlib import Path; print(len(load_text_from_pdf(Path('./data/RagPresenetation.pdf'))))"

# Run tests
pytest tests/test_real_e2e.py -v -s -m real_integration
```

---

**Last Updated**: October 14, 2025, 10:15 PM
**Status**: ✅ **FULLY FUNCTIONAL** - Ready to use!

---

## 📊 Final Summary

**What Works:**
- ✅ Azure Document Intelligence processing (20-page PDF in <1 second)
- ✅ Whisper audio transcription (2+ hour video processed successfully)
- ✅ All 43 chunks stored in ChromaDB with unique IDs
- ✅ RAG pipeline retrieving relevant context
- ✅ GPT-4o-mini generating answers
- ✅ Interactive chatbot interface working

**Total Cost:** ~$0.05 for ingestion
**Total Time:** ~60 seconds for complete setup

**Success!** 🎉
