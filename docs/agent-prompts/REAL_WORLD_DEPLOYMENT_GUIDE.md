# Real-World Deployment Guide & Known Issues

## 🎯 Purpose of This Document

This document serves as a comprehensive handoff for running the RAG chatbot with **REAL COMPONENTS** (not mocked). All testing was done with mocked APIs, so expect significant issues when connecting to actual Azure OpenAI services, processing real files, and running the complete pipeline.

**Written by**: Initial implementation agent
**Date**: 2025-10-12
**Status**: All 30 tests passing with MOCKED components
**Next Step**: Real-world integration and debugging

---

## 📋 Table of Contents

1. [Complete Implementation Overview](#complete-implementation-overview)
2. [Critical Assumptions & Mocking](#critical-assumptions--mocking)
3. [Expected Issues by Component](#expected-issues-by-component)
4. [Azure OpenAI Setup & Verification](#azure-openai-setup--verification)
5. [File Processing Issues](#file-processing-issues)
6. [System Dependencies](#system-dependencies)
7. [Testing Strategy for Real Components](#testing-strategy-for-real-components)
8. [Troubleshooting Checklist](#troubleshooting-checklist)
9. [Performance Considerations](#performance-considerations)
10. [Cost Estimates](#cost-estimates)

---

## 1. Complete Implementation Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                        │
│                  User Interface Entry Point                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    src/chatbot.py                           │
│              RAGChatbot Class (Orchestrator)                │
│  Methods: __init__(), ask()                                 │
│  Functions: retrieve_relevant_context(),                    │
│             format_prompt(), generate_llm_answer()          │
└─────┬───────────────────┬──────────────────┬────────────────┘
      │                   │                  │
      ▼                   ▼                  ▼
┌─────────────┐  ┌─────────────────┐  ┌──────────────┐
│data_loader  │  │text_processor   │  │vector_store  │
│  .py        │  │    .py          │  │    .py       │
└─────────────┘  └─────────────────┘  └──────────────┘
      │                   │                  │
      │                   │                  │
      ▼                   ▼                  ▼
┌─────────────┐  ┌─────────────────┐  ┌──────────────┐
│ External    │  │ LangChain       │  │ ChromaDB     │
│ Files       │  │ Text Splitter   │  │ + Azure      │
│ PDF/MP3/MP4 │  │                 │  │ OpenAI API   │
└─────────────┘  └─────────────────┘  └──────────────┘
```

### What Was Built

**Core Modules** (all in `src/`):
1. **config.py** - Settings singleton with environment variable validation
2. **data_loader.py** - Multi-modal file processing (PDF→Image→VLM, Audio, Video)
3. **text_processor.py** - Semantic chunking with LangChain
4. **vector_store.py** - ChromaDB integration + Azure OpenAI embeddings
5. **chatbot.py** - Complete RAG pipeline orchestration

**Entry Point**:
- **main.py** - Interactive CLI interface

**Configuration**:
- **.env** - Azure OpenAI credentials (MUST be created by user)
- **requirements.txt** - All Python dependencies with version pins
- **Dockerfile** - Container with ffmpeg + poppler-utils
- **docker-compose.yml** - One-command deployment

**Testing** (all in `tests/`):
- **conftest.py** - Test configuration with environment setup
- **test_config.py** - 5 tests for settings validation
- **test_data_loader.py** - 8 tests for multi-modal processing
- **test_text_processor.py** - 6 tests for chunking logic
- **test_vector_store.py** - 5 tests for embeddings + ChromaDB
- **test_e2e_rag_pipeline.py** - 6 E2E tests for complete workflows

### Key Technical Decisions

1. **Vision-Based PDF Processing**
   - **Why**: Handles scanned docs, charts, complex layouts better than text extraction
   - **Implementation**: PDF → pdf2image → base64 encode → GPT-4o Vision API
   - **Risk**: Higher API costs, slower processing, requires GPT-4o with vision

2. **Video Support via FFmpeg**
   - **Why**: User had MP4 files in data directory
   - **Implementation**: MP4 → FFmpeg extract audio → temp WAV → Whisper transcribe
   - **Risk**: FFmpeg subprocess errors, temp file cleanup, codec issues

3. **ChromaDB for Vector Storage**
   - **Why**: Simple, local, no external services
   - **Implementation**: PersistentClient with local disk storage
   - **Risk**: Scalability limits, version compatibility (requires numpy<2.0)

4. **Heavy Mocking in Tests**
   - **Why**: Fast tests, no API costs, no network dependencies
   - **Implementation**: pytest-mock for ALL external calls
   - **Risk**: Tests pass but real integration might fail completely

5. **NumPy Version Pinning**
   - **Why**: ChromaDB 0.4.22 incompatible with NumPy 2.0+
   - **Implementation**: requirements.txt has `numpy<2.0.0`
   - **Risk**: Future dependency conflicts with other packages

---

## 2. Critical Assumptions & Mocking

### What Was MOCKED in Tests (Will Break with Real Components)

#### Azure OpenAI API Calls
**Location**: All test files
**Mocked**:
```python
# Embedding generation
mock_client.embeddings.create.return_value = MagicMock(
    data=[MagicMock(embedding=[0.1] * 1536)]  # Fake 1536-dim vector
)

# LLM chat completions
mock_client.chat.completions.create.return_value = MagicMock(
    choices=[MagicMock(message=MagicMock(content="Fake answer"))]
)

# Vision API (PDF processing)
mock_client.chat.completions.create.return_value = MagicMock(
    choices=[MagicMock(message=MagicMock(content="Fake PDF description"))]
)

# Whisper transcription
mock_client.audio.transcriptions.create.return_value = MagicMock(
    text="Fake transcription"
)
```

**Real Implementation**: `src/data_loader.py`, `src/vector_store.py`, `src/chatbot.py`
**Expected Issues**:
- Authentication failures (wrong API key/endpoint)
- Model deployment names don't match (gpt-4o vs gpt-4-vision-preview)
- Rate limiting (429 errors)
- API version incompatibilities
- Vision API not available in deployment region
- Whisper model not deployed or wrong name

#### PDF Processing (pdf2image)
**Location**: `tests/test_data_loader.py`
**Mocked**:
```python
mocker.patch("src.data_loader.convert_from_path", return_value=[mock_image])
```

**Real Implementation**: `src/data_loader.py:29-70`
**Expected Issues**:
- Poppler not installed or wrong version
- PDF file corrupted or unsupported format
- Image conversion fails for large PDFs (memory issues)
- PIL/Pillow compatibility issues
- Temporary file path problems on different OS

#### FFmpeg (Video Processing)
**Location**: `tests/test_data_loader.py`
**Mocked**:
```python
mock_ffmpeg_input = MagicMock()
mock_ffmpeg_output = MagicMock()
mock_ffmpeg_output.run = MagicMock()
mock_ffmpeg_input.output = MagicMock(return_value=mock_ffmpeg_output)
mocker.patch("src.data_loader.ffmpeg.input", return_value=mock_ffmpeg_input)
```

**Real Implementation**: `src/data_loader.py:94-120`
**Expected Issues**:
- FFmpeg not installed or not in PATH
- Codec issues with MP4 file (h264, AAC, etc.)
- Subprocess errors not caught properly
- Temporary file cleanup failures
- Permissions issues writing to /tmp
- Audio extraction fails for video-only files

#### ChromaDB
**Location**: All vector store tests
**Mocked**: Not fully mocked, but uses tmp_path
**Real Implementation**: `src/vector_store.py`
**Expected Issues**:
- Persistent storage directory permissions
- SQLite version incompatibility
- Tenant initialization failures (seen in E2E test)
- Collection already exists errors
- Embedding dimension mismatches
- NumPy version conflicts

---

## 3. Expected Issues by Component

### 3.1 Azure OpenAI Configuration Issues

#### Issue: Wrong API Key/Endpoint
**Symptom**:
```
AuthenticationError: Incorrect API key provided
```
**Location**: Any API call in `src/data_loader.py`, `src/vector_store.py`, `src/chatbot.py`
**Fix**:
1. Verify `.env` file exists in project root
2. Check `AZURE_OPENAI_API_KEY` is correct (no quotes, no spaces)
3. Check `AZURE_OPENAI_ENDPOINT` format: `https://<resource-name>.openai.azure.com/`
4. Test with: `curl -H "api-key: $AZURE_OPENAI_API_KEY" $AZURE_OPENAI_ENDPOINT`

#### Issue: Model Deployment Name Mismatch
**Symptom**:
```
NotFoundError: The API deployment for this resource does not exist
```
**Location**:
- `src/config.py:23-24` (model names)
- `src/data_loader.py:37` (Vision API)
- `src/data_loader.py:88` (Whisper)
- `src/vector_store.py:49` (Embeddings)
- `src/chatbot.py:39` (Embeddings)
- `src/chatbot.py:74` (Chat completions)

**Fix**:
1. Go to Azure Portal → Your OpenAI resource → Model deployments
2. Copy EXACT deployment names (case-sensitive)
3. Update `.env`:
   ```
   EMBEDDING_MODEL_NAME="your-exact-embedding-deployment-name"
   LLM_MODEL_NAME="your-exact-gpt4-deployment-name"
   ```
4. For Whisper, it's hardcoded in `src/data_loader.py:88`: `model="whisper"`
   - Update this line if your deployment name differs

#### Issue: API Version Incompatibility
**Symptom**:
```
InvalidRequestError: Unrecognized request argument supplied: vision
```
**Location**: `src/config.py:22`
**Current Value**: `2023-12-01-preview`
**Fix**:
1. Check Azure OpenAI API versions documentation
2. For vision support, need 2023-12-01-preview or later
3. Update `OPENAI_API_VERSION` in `.env`

#### Issue: Vision API Not Supported
**Symptom**:
```
InvalidRequestError: Vision is not supported in this deployment
```
**Location**: `src/data_loader.py:37-63` (PDF processing)
**Cause**: GPT-4o deployment doesn't have vision enabled OR using wrong model
**Fix**:
1. Verify deployment uses `gpt-4` with vision OR `gpt-4o` model
2. Check deployment region supports vision (not all do)
3. Alternative: Fall back to text extraction with pypdf:
   ```python
   # In src/data_loader.py, replace load_text_from_pdf with:
   import pypdf
   def load_text_from_pdf(file_path):
       reader = pypdf.PdfReader(str(file_path))
       return "\n\n".join([page.extract_text() for page in reader.pages])
   ```

#### Issue: Rate Limiting
**Symptom**:
```
RateLimitError: Rate limit reached for requests
```
**Location**: Any API call, especially in `src/vector_store.py:44-52` (batch embedding)
**Fix**:
1. Add retry logic with exponential backoff:
   ```python
   from openai import RateLimitError
   import time

   max_retries = 3
   for attempt in range(max_retries):
       try:
           response = client.embeddings.create(...)
           break
       except RateLimitError:
           if attempt < max_retries - 1:
               time.sleep(2 ** attempt)  # 1s, 2s, 4s
           else:
               raise
   ```
2. Reduce batch size in `src/vector_store.py:40-52` (currently processes all chunks at once)
3. Add delays between API calls

### 3.2 PDF Processing Issues

#### Issue: Poppler Not Found
**Symptom**:
```
PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?
```
**Location**: `src/data_loader.py:32` (convert_from_path)
**Fix**:

**macOS**:
```bash
brew install poppler
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**Docker**: Already in Dockerfile line 14
**Verify**:
```bash
pdfinfo -v  # Should show poppler version
```

#### Issue: PDF Conversion Memory Error
**Symptom**:
```
MemoryError: Unable to allocate array
```
**Location**: `src/data_loader.py:32` (large PDFs)
**Fix**:
1. Process PDFs page-by-page instead of all at once:
   ```python
   from pdf2image import convert_from_path
   from pdf2image.exceptions import PDFPageCountError

   def load_text_from_pdf(file_path):
       # Get page count first
       from pdf2image import pdfinfo_from_path
       info = pdfinfo_from_path(file_path)
       page_count = info["Pages"]

       all_descriptions = []
       for page_num in range(1, page_count + 1):
           images = convert_from_path(file_path, first_page=page_num, last_page=page_num)
           # Process single page
           description = process_page_with_vision(images[0])
           all_descriptions.append(description)

       return "\n\n".join(all_descriptions)
   ```

2. Reduce DPI (currently using default 200):
   ```python
   images = convert_from_path(str(file_path), dpi=150)  # Lower quality, less memory
   ```

#### Issue: PIL Image Format Error
**Symptom**:
```
OSError: cannot identify image file
```
**Location**: `src/data_loader.py:44-47` (image.save)
**Fix**:
1. Ensure PIL/Pillow is latest version: `pip install --upgrade Pillow`
2. Add explicit format conversion:
   ```python
   if image.mode not in ('RGB', 'L'):
       image = image.convert('RGB')
   image.save(buffered, format="PNG")
   ```

### 3.3 Audio/Video Processing Issues

#### Issue: FFmpeg Not Found
**Symptom**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```
**Location**: `src/data_loader.py:102` (ffmpeg.input)
**Fix**:

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Docker**: Already in Dockerfile line 14
**Verify**:
```bash
ffmpeg -version  # Should show ffmpeg version
```

#### Issue: FFmpeg Subprocess Error
**Symptom**:
```
ffmpeg.Error: [Output truncated]
```
**Location**: `src/data_loader.py:110` (ffmpeg run)
**Fix**:
1. Add proper error handling and logging:
   ```python
   try:
       (
           ffmpeg
           .input(str(video_file_path))
           .output(temp_audio_file, format="wav", acodec="pcm_s16le", ar="16000", ac=1)
           .overwrite_output()
           .run(capture_stdout=True, capture_stderr=True)
       )
   except ffmpeg.Error as e:
       print(f"FFmpeg stdout: {e.stdout.decode()}")
       print(f"FFmpeg stderr: {e.stderr.decode()}")
       raise RuntimeError(f"Failed to extract audio from {video_file_path}: {e.stderr.decode()}")
   ```

2. Check video file is valid:
   ```bash
   ffprobe video.mp4  # Should show video info
   ```

3. Try different audio codec if failing:
   ```python
   .output(temp_audio_file, format="wav", acodec="libmp3lame")  # Instead of pcm_s16le
   ```

#### Issue: Temp File Cleanup Fails
**Symptom**: Temp files accumulating in `/tmp` or `%TEMP%`
**Location**: `src/data_loader.py:116` (os.remove)
**Fix**:
1. Use context manager for guaranteed cleanup:
   ```python
   import tempfile
   import os

   with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
       temp_audio_path = temp_audio.name

   try:
       ffmpeg.input(...).output(temp_audio_path, ...).run()
       transcription = transcribe_audio_file(temp_audio_path)
       return transcription
   finally:
       if os.path.exists(temp_audio_path):
           os.remove(temp_audio_path)
   ```

#### Issue: Whisper Model Not Deployed
**Symptom**:
```
NotFoundError: The API deployment 'whisper' does not exist
```
**Location**: `src/data_loader.py:88`
**Fix**:
1. Check Azure Portal for actual Whisper deployment name
2. If different, update hardcoded value:
   ```python
   # src/data_loader.py line 88
   transcription = client.audio.transcriptions.create(
       model="your-actual-whisper-deployment-name",  # Change this
       file=audio_file
   )
   ```
3. Alternative: Add Whisper model name to .env and settings

#### Issue: Audio File Too Large
**Symptom**:
```
InvalidRequestError: File size exceeds the maximum limit
```
**Location**: `src/data_loader.py:88` (Whisper API)
**Cause**: Whisper API has 25MB limit
**Fix**:
1. Add file size check before transcription:
   ```python
   import os

   max_size = 25 * 1024 * 1024  # 25 MB
   file_size = os.path.getsize(audio_file_path)

   if file_size > max_size:
       raise ValueError(f"Audio file {audio_file_path} is {file_size/1024/1024:.1f}MB, exceeds 25MB limit")
   ```

2. For large files, split audio into chunks:
   ```python
   # Use pydub to split audio
   from pydub import AudioSegment
   from pydub.utils import make_chunks

   audio = AudioSegment.from_file(audio_file_path)
   chunk_length_ms = 10 * 60 * 1000  # 10 minutes
   chunks = make_chunks(audio, chunk_length_ms)

   transcriptions = []
   for i, chunk in enumerate(chunks):
       chunk_path = f"/tmp/chunk_{i}.wav"
       chunk.export(chunk_path, format="wav")
       transcription = transcribe_audio_file(chunk_path)
       transcriptions.append(transcription)
       os.remove(chunk_path)

   return " ".join(transcriptions)
   ```

### 3.4 ChromaDB Issues

#### Issue: ChromaDB Import Error
**Symptom**:
```
AttributeError: np.float_ was removed in the NumPy 2.0 release
```
**Location**: Import time when loading `chromadb`
**Fix**: Already fixed in requirements.txt with `numpy<2.0.0`
**Verify**:
```bash
pip install 'numpy<2.0.0'
pip show numpy  # Should show version 1.x.x
```

#### Issue: Database Directory Permissions
**Symptom**:
```
PermissionError: [Errno 13] Permission denied: './chroma_db'
```
**Location**: `src/vector_store.py:27` (PersistentClient)
**Fix**:
1. Create directory with proper permissions:
   ```bash
   mkdir -p ./chroma_db
   chmod 755 ./chroma_db
   ```

2. In Docker, ensure volume mount permissions:
   ```yaml
   # docker-compose.yml
   volumes:
     - ./chroma_db:/app/chroma_db:rw  # Add :rw for read-write
   ```

#### Issue: Collection Already Exists
**Symptom**:
```
UniqueConstraintError: Collection with name 'rag_collection' already exists
```
**Location**: `src/vector_store.py:28` (get_or_create_collection)
**Cause**: Database not properly cleaned between runs
**Fix**: Already using `get_or_create_collection()` which should handle this, but if still failing:
```python
# In src/vector_store.py
try:
    collection = client.get_collection(name="rag_collection")
except Exception:
    collection = client.create_collection(name="rag_collection")
```

#### Issue: Embedding Dimension Mismatch
**Symptom**:
```
ValueError: Embedding dimension 768 does not match collection dimension 1536
```
**Location**: `src/vector_store.py:52` (collection.add)
**Cause**: Using different embedding model than expected
**Fix**:
1. Verify embedding model is text-embedding-ada-002 (produces 1536 dims)
2. If using different model, delete existing database:
   ```bash
   rm -rf ./chroma_db
   ```
3. Or create new collection with correct dimensions

#### Issue: SQLite Version Too Old
**Symptom**:
```
sqlite3.OperationalError: near "RETURNING": syntax error
```
**Location**: ChromaDB internal operations
**Cause**: ChromaDB requires SQLite 3.35+ (for RETURNING clause)
**Fix**:

**Check version**:
```python
import sqlite3
print(sqlite3.sqlite_version)  # Should be >= 3.35.0
```

**macOS**: Upgrade Python to 3.11+ which bundles newer SQLite
**Ubuntu**:
```bash
sudo add-apt-repository ppa:sergey-dryabzhinsky/sqlite3
sudo apt update
sudo apt install sqlite3
```

**Docker**: Python 3.11-slim already has SQLite 3.40+

### 3.5 RAG Pipeline Issues

#### Issue: Empty Context Retrieved
**Symptom**: Chatbot says "I couldn't find any relevant information"
**Location**: `src/chatbot.py:58-63`
**Causes**:
1. Database is empty (no documents ingested)
2. Query embedding fails
3. Vector search returns no results
4. Similarity threshold too high

**Debug**:
```python
# Add to src/chatbot.py after line 33
print(f"Database contains {self.collection.count()} chunks")

# Add to src/chatbot.py after line 36
print(f"Query: {query}")
print(f"Context retrieved: {len(context)} chunks")
if context:
    print(f"First chunk: {context[0][:100]}...")
```

**Fix**:
1. Verify data ingestion:
   ```python
   collection = get_vector_database_collection()
   print(f"Total chunks: {collection.count()}")
   print(f"Sample: {collection.get(limit=1)}")
   ```

2. Test query embedding separately:
   ```python
   from src.chatbot import retrieve_relevant_context
   context = retrieve_relevant_context("test query", collection, n_results=3)
   print(context)
   ```

3. Lower similarity threshold or increase n_results:
   ```python
   # In src/chatbot.py line 58
   context = retrieve_relevant_context(query, self.collection, n_results=5)  # Increase from 3
   ```

#### Issue: LLM Generates Incorrect Answers
**Symptom**: Answers are not based on context, or are hallucinated
**Location**: `src/chatbot.py:74-89` (generate_llm_answer)
**Causes**:
1. Prompt formatting issues
2. Context not included properly
3. LLM temperature too high
4. Retrieved context not relevant

**Debug**:
```python
# Add logging before LLM call in src/chatbot.py
print(f"Prompt sent to LLM:\n{prompt}")
print(f"Temperature: {temperature}")
```

**Fix**:
1. Verify prompt format includes context:
   ```python
   # In src/chatbot.py, check format_prompt output
   prompt = format_prompt(query, context)
   assert "---CONTEXT---" in prompt
   assert query in prompt
   ```

2. Lower temperature for more deterministic answers:
   ```python
   # src/chatbot.py line 80
   temperature=0.3,  # Change from 0.7
   ```

3. Strengthen system instructions:
   ```python
   # In src/chatbot.py format_prompt function
   system_instructions = """
   You are a helpful assistant. Answer ONLY using the provided context.
   If the context doesn't contain the answer, say "I don't have enough information."
   DO NOT use external knowledge. DO NOT hallucinate.
   """
   ```

#### Issue: Slow Response Time
**Symptom**: Each query takes 10+ seconds
**Location**: Entire pipeline
**Causes**:
1. Embedding generation is slow (API call)
2. Vector search is slow (large database)
3. LLM generation is slow (API call)

**Debug - Add timing**:
```python
import time

# In src/chatbot.py ask method
start = time.time()
context = retrieve_relevant_context(query, self.collection)
print(f"Retrieval: {time.time() - start:.2f}s")

start = time.time()
prompt = format_prompt(query, context)
print(f"Formatting: {time.time() - start:.2f}s")

start = time.time()
answer = generate_llm_answer(prompt)
print(f"Generation: {time.time() - start:.2f}s")
```

**Fix**:
1. Cache embeddings for common queries
2. Reduce n_results (fewer chunks = faster)
3. Use streaming for LLM responses:
   ```python
   # In src/chatbot.py
   response = client.chat.completions.create(
       ...,
       stream=True
   )
   for chunk in response:
       if chunk.choices[0].delta.content:
           print(chunk.choices[0].delta.content, end="")
   ```

---

## 4. Azure OpenAI Setup & Verification

### Step-by-Step Azure Setup

#### 1. Create Azure OpenAI Resource
```bash
# Azure Portal: https://portal.azure.com
# 1. Create Resource → Azure OpenAI
# 2. Choose region (East US, West Europe support all features)
# 3. Pricing tier: Standard S0
# 4. Wait for deployment (5-10 mins)
```

#### 2. Deploy Required Models

**Navigate to**: Azure OpenAI Studio → Deployments → Create new deployment

**Required deployments**:

| Model | Deployment Name | Version | Purpose |
|-------|----------------|---------|---------|
| gpt-4o | gpt-4o | Latest | LLM + Vision for PDF |
| text-embedding-ada-002 | text-embedding-ada-002 | 2 | Vector embeddings |
| whisper | whisper | 001 | Audio transcription |

**Notes**:
- Deployment names MUST match what's in your `.env` file
- GPT-4o deployment must have vision capability enabled
- Check regional availability - not all regions support all models

#### 3. Get Credentials

**From Azure Portal**:
1. Go to your Azure OpenAI resource
2. Keys and Endpoint → Show Keys
3. Copy:
   - KEY 1 (primary key)
   - Endpoint URL (format: `https://<resource-name>.openai.azure.com/`)

**Create `.env` file**:
```bash
cd "/Users/bb/Programming/Simple RAG"
cp .env.example .env
```

**Edit `.env`**:
```env
AZURE_OPENAI_API_KEY="<paste-key-1-here>"
AZURE_OPENAI_ENDPOINT="https://<your-resource-name>.openai.azure.com/"
OPENAI_API_VERSION="2023-12-01-preview"
EMBEDDING_MODEL_NAME="text-embedding-ada-002"
LLM_MODEL_NAME="gpt-4o"
```

#### 4. Verify Setup

**Test authentication**:
```bash
curl "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2023-12-01-preview" \
  -H "api-key: $AZURE_OPENAI_API_KEY"
```

Expected response: JSON list of your deployments

**Test embedding model**:
```python
# test_azure_setup.py
from dotenv import load_dotenv
import os
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Test embeddings
response = client.embeddings.create(
    input="test",
    model=os.getenv("EMBEDDING_MODEL_NAME")
)
print(f"✅ Embeddings work! Dimension: {len(response.data[0].embedding)}")

# Test chat completions
response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL_NAME"),
    messages=[{"role": "user", "content": "Say 'hello'"}]
)
print(f"✅ Chat completions work! Response: {response.choices[0].message.content}")

# Test Whisper (need an audio file)
# with open("test.mp3", "rb") as audio_file:
#     response = client.audio.transcriptions.create(
#         model="whisper",
#         file=audio_file
#     )
#     print(f"✅ Whisper works! Transcription: {response.text}")
```

Run:
```bash
python test_azure_setup.py
```

---

## 5. File Processing Issues

### Preparing Knowledge Base Files

#### PDF Files
**Location**: `./data/knowledge.pdf`
**Requirements**:
- PDF version 1.4 or higher
- Not password-protected
- Reasonable size (< 100 pages for testing)

**Test PDF processing**:
```python
# test_pdf.py
from src.data_loader import load_text_from_pdf

try:
    text = load_text_from_pdf("./data/knowledge.pdf")
    print(f"✅ PDF processed successfully")
    print(f"Extracted {len(text)} characters")
    print(f"First 200 chars: {text[:200]}")
except Exception as e:
    print(f"❌ PDF processing failed: {e}")
```

**Common PDF issues**:
1. **Scanned PDFs**: Vision API should handle, but may produce lower quality text
2. **Large PDFs**: May hit memory limits, see [3.2 PDF Processing Issues](#32-pdf-processing-issues)
3. **Complex layouts**: Vision API handles better than text extraction
4. **Non-Latin text**: Depends on model language support

#### Audio Files
**Location**: `./data/*.mp3` (or .wav, .m4a)
**Requirements**:
- Format: MP3, WAV, M4A (Whisper supported formats)
- Size: < 25 MB (Whisper API limit)
- Sample rate: 16kHz recommended (auto-converted)
- Mono preferred (auto-converted)

**Test audio processing**:
```python
# test_audio.py
from src.data_loader import transcribe_audio_file

try:
    text = transcribe_audio_file("./data/what-is-feedback-loop-in-rag.mp3")
    print(f"✅ Audio transcribed successfully")
    print(f"Transcription length: {len(text)} characters")
    print(f"First 200 chars: {text[:200]}")
except Exception as e:
    print(f"❌ Audio transcription failed: {e}")
```

**Common audio issues**:
1. **File too large**: Split into chunks (see [3.3](#33-audiovideo-processing-issues))
2. **Unsupported format**: Convert to WAV first with ffmpeg
3. **Poor audio quality**: Whisper is robust but may produce errors
4. **Background noise**: May affect transcription quality

#### Video Files (MP4)
**Location**: `./data/*.mp4`
**Requirements**:
- Format: MP4 container
- Video codec: H.264 (most common)
- Audio codec: AAC or MP3
- Size: No hard limit, but large files take time

**Test video processing**:
```python
# test_video.py
from src.data_loader import load_from_directory

try:
    docs = load_from_directory("./data")
    video_docs = [d for d in docs if d["source"].endswith(".mp4")]
    print(f"✅ Found {len(video_docs)} video files")
    for doc in video_docs:
        print(f"Video: {doc['source']}")
        print(f"Transcription length: {len(doc['content'])} chars")
        print(f"Preview: {doc['content'][:200]}")
except Exception as e:
    print(f"❌ Video processing failed: {e}")
```

**Common video issues**:
1. **FFmpeg not installed**: See [3.3](#33-audiovideo-processing-issues)
2. **No audio track**: FFmpeg will fail
3. **Codec not supported**: Try re-encoding with ffmpeg
4. **Large file size**: Extraction is fast, transcription may hit 25MB limit

---

## 6. System Dependencies

### Required System Packages

#### FFmpeg
**Purpose**: Extract audio from MP4 video files
**Used in**: `src/data_loader.py:102-110`

**Install**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# Verify
ffmpeg -version
```

**Docker**: Already installed in Dockerfile line 14

#### Poppler Utils
**Purpose**: Convert PDF pages to images (for vision processing)
**Used in**: `src/data_loader.py:32` (via pdf2image)

**Install**:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install poppler-utils

# Verify
pdfinfo -v
pdftoppm -v
```

**Docker**: Already installed in Dockerfile line 14

### Python Dependencies

**Location**: `requirements.txt`

**Critical dependencies**:
```
openai==1.6.1              # Azure OpenAI SDK
chromadb==0.4.22           # Vector database
numpy<2.0.0                # Required for ChromaDB compatibility
pdf2image==1.16.3          # PDF to image conversion
ffmpeg-python==0.2.0       # FFmpeg Python wrapper
langchain-text-splitters==0.0.1  # Semantic chunking
python-dotenv==1.0.0       # Environment variables
```

**Install all**:
```bash
pip install -r requirements.txt
```

**Common dependency issues**:
1. **NumPy 2.0 conflict**: Already fixed with `numpy<2.0.0`
2. **OpenAI SDK version**: Must be >= 1.0 for Azure support
3. **ChromaDB build errors**: May need build tools (gcc, g++)

---

## 7. Testing Strategy for Real Components

### Phase 1: Component-Level Testing

#### Test 1: Configuration Loading
```bash
# Should load without errors
python -c "from src.config import settings; print(settings.azure_openai_api_key[:10] + '...')"
```

Expected: First 10 chars of your API key

#### Test 2: Azure OpenAI Connection
```python
# test_azure_connection.py
from src.config import settings
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version=settings.openai_api_version,
    azure_endpoint=settings.azure_openai_endpoint
)

# Test embedding
response = client.embeddings.create(
    input="hello world",
    model=settings.embedding_model_name
)
print(f"✅ Embedding dimension: {len(response.data[0].embedding)}")

# Test chat
response = client.chat.completions.create(
    model=settings.llm_model_name,
    messages=[{"role": "user", "content": "Say 'test successful'"}],
    temperature=0.7
)
print(f"✅ LLM response: {response.choices[0].message.content}")
```

#### Test 3: PDF Processing
```python
# test_real_pdf.py
from src.data_loader import load_text_from_pdf
import sys

pdf_path = "./data/knowledge.pdf"
print(f"Processing {pdf_path}...")

try:
    text = load_text_from_pdf(pdf_path)
    print(f"✅ Successfully processed PDF")
    print(f"Length: {len(text)} characters")
    print(f"First 500 chars:\n{text[:500]}")
    print(f"\nLast 500 chars:\n{text[-500:]}")
except Exception as e:
    print(f"❌ Failed to process PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

#### Test 4: Audio Processing
```python
# test_real_audio.py
from src.data_loader import transcribe_audio_file
import sys

audio_path = "./data/what-is-feedback-loop-in-rag.mp3"
print(f"Transcribing {audio_path}...")

try:
    text = transcribe_audio_file(audio_path)
    print(f"✅ Successfully transcribed audio")
    print(f"Length: {len(text)} characters")
    print(f"Transcription:\n{text}")
except Exception as e:
    print(f"❌ Failed to transcribe audio: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

#### Test 5: Video Processing
```python
# test_real_video.py
from src.data_loader import load_from_directory
import sys

data_dir = "./data"
print(f"Processing all files in {data_dir}...")

try:
    docs = load_from_directory(data_dir)
    print(f"✅ Successfully loaded {len(docs)} documents")

    for doc in docs:
        print(f"\n--- {doc['source']} ---")
        print(f"Length: {len(doc['content'])} characters")
        print(f"Preview: {doc['content'][:200]}...")

except Exception as e:
    print(f"❌ Failed to process files: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

### Phase 2: Integration Testing

#### Test 6: Full Ingestion Pipeline
```python
# test_ingestion.py
from src.data_loader import load_from_directory
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks
import sys

print("=" * 70)
print("FULL INGESTION PIPELINE TEST")
print("=" * 70)

try:
    # Step 1: Load documents
    print("\n1. Loading documents from ./data...")
    documents = load_from_directory("./data")
    print(f"✅ Loaded {len(documents)} documents")
    for doc in documents:
        print(f"   - {doc['source']}: {len(doc['content'])} chars")

    # Step 2: Chunk text
    print("\n2. Chunking text...")
    chunks = chunk_text(documents, chunk_size=1000, chunk_overlap=200)
    print(f"✅ Created {len(chunks)} chunks")

    # Step 3: Create database
    print("\n3. Initializing vector database...")
    collection = get_vector_database_collection(db_path="./chroma_db")
    print(f"✅ Database initialized, current count: {collection.count()}")

    # Step 4: Embed and store
    print("\n4. Generating embeddings and storing...")
    embed_and_store_chunks(chunks, collection)
    print(f"✅ Stored {collection.count()} chunks in database")

    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Ingestion failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

#### Test 7: Full RAG Pipeline
```python
# test_rag.py
from src.chatbot import RAGChatbot
import sys

print("=" * 70)
print("FULL RAG PIPELINE TEST")
print("=" * 70)

try:
    # Initialize chatbot
    print("\nInitializing RAG chatbot...")
    chatbot = RAGChatbot(data_dir="./data", db_dir="./chroma_db")
    print(f"✅ Chatbot initialized with {chatbot.collection.count()} chunks")

    # Test queries
    test_queries = [
        "What are the production 'Do's' for RAG?",
        "What is the difference between standard retrieval and the ColPali approach?",
        "Why is hybrid search better than vector-only search?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'-' * 70}")
        print(f"Query {i}: {query}")
        print(f"{'-' * 70}")

        answer = chatbot.ask(query)
        print(f"Answer: {answer}")

    print("\n" + "=" * 70)
    print("RAG PIPELINE TEST COMPLETE")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ RAG pipeline failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

### Phase 3: Full System Testing

#### Test 8: Run Main CLI
```bash
# Clear existing database for fresh test
rm -rf ./chroma_db

# Run main chatbot
python main.py
```

**Test checklist**:
- [ ] Chatbot initializes without errors
- [ ] Data ingestion completes (first run only)
- [ ] CLI prompts for input
- [ ] Can ask questions and get answers
- [ ] Answers are relevant to knowledge base
- [ ] Can type 'quit' to exit gracefully
- [ ] Ctrl+C exits gracefully

#### Test 9: Docker Deployment
```bash
# Build Docker image
docker-compose build

# Should complete without errors
# Check for:
# - [+] Building X.Xs
# - Successfully tagged simple-rag-chatbot:latest

# Run container
docker-compose up

# Should see:
# - chatbot_1  | RAG CHATBOT FOR 'DATABASES FOR GENAI'
# - chatbot_1  | How to use:
```

**Test checklist**:
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] Volume mounts work (./data and ./chroma_db accessible)
- [ ] Environment variables loaded from .env
- [ ] FFmpeg and Poppler available in container
- [ ] Can interact with chatbot via terminal
- [ ] Data persists in ./chroma_db after container stops

---

## 8. Troubleshooting Checklist

### Pre-Flight Checklist

Before running with real components, verify:

```bash
# 1. Python version
python --version  # Should be 3.11+

# 2. System dependencies
ffmpeg -version   # Should show ffmpeg version
pdfinfo -v        # Should show poppler version

# 3. Python dependencies
pip list | grep openai      # Should show openai==1.6.1 or compatible
pip list | grep chromadb    # Should show chromadb==0.4.22
pip list | grep numpy       # Should show numpy 1.x.x (NOT 2.0+)

# 4. Environment file
cat .env | grep -v "^#"     # Should show all required variables set

# 5. Data files
ls -lh ./data               # Should show PDF, MP3/MP4 files

# 6. Database directory (if exists)
ls -lh ./chroma_db          # Should show chromadb directory structure
```

### Common Error Patterns

| Error Pattern | Likely Cause | First Action |
|---------------|--------------|--------------|
| `AuthenticationError` | Wrong API key/endpoint | Check `.env` file |
| `NotFoundError: deployment` | Wrong model name | Check Azure deployments |
| `RateLimitError` | Too many requests | Add retry logic |
| `FileNotFoundError: ffmpeg` | FFmpeg not installed | Install FFmpeg |
| `PDFInfoNotInstalledError` | Poppler not installed | Install Poppler |
| `MemoryError` | PDF too large | Process page-by-page |
| `np.float_ removed` | NumPy 2.0 issue | Install `numpy<2.0.0` |
| `Permission denied: chroma_db` | Directory permissions | `chmod 755 ./chroma_db` |
| `Collection already exists` | Stale database | Delete `./chroma_db` |
| `I couldn't find...` | Empty database | Check ingestion |

### Debugging Commands

**Enable verbose logging**:
```python
# Add to top of main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check database contents**:
```python
from src.vector_store import get_vector_database_collection

collection = get_vector_database_collection()
print(f"Total chunks: {collection.count()}")

# Get sample data
sample = collection.get(limit=5, include=["documents", "metadatas"])
for i, (doc, meta) in enumerate(zip(sample["documents"], sample["metadatas"])):
    print(f"\nChunk {i}:")
    print(f"Source: {meta['source']}")
    print(f"Content: {doc[:200]}...")
```

**Test retrieval**:
```python
from src.chatbot import retrieve_relevant_context
from src.vector_store import get_vector_database_collection

collection = get_vector_database_collection()
context = retrieve_relevant_context("test query", collection, n_results=3)

print(f"Retrieved {len(context)} chunks")
for i, chunk in enumerate(context):
    print(f"\nChunk {i}: {chunk[:200]}...")
```

**Check API connectivity**:
```bash
# Test endpoint reachability
curl -I "$AZURE_OPENAI_ENDPOINT"

# Test authentication
curl "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=$OPENAI_API_VERSION" \
  -H "api-key: $AZURE_OPENAI_API_KEY"
```

---

## 9. Performance Considerations

### Expected Performance Metrics

#### Data Ingestion (First Run)

For reference knowledge base:
- 1 PDF (100 pages): ~2-5 minutes (vision processing)
- 1 MP3 (30 minutes audio): ~1-2 minutes (Whisper transcription)
- 1 MP4 (30 minutes video): ~1-2 minutes (audio extraction + transcription)

**Bottlenecks**:
1. PDF vision processing: ~1-3 seconds per page (API call)
2. Audio/video transcription: ~1-2 minutes per 30 minutes of audio
3. Embedding generation: ~1-5 seconds per batch (depends on batch size)
4. ChromaDB storage: Very fast (< 1 second)

**Optimization tips**:
1. Process PDFs page-by-page to show progress
2. Split large audio files into chunks for parallel processing
3. Batch embeddings (currently processes all at once)
4. Cache processed files to avoid re-processing

#### Query Response Time

Expected: 2-5 seconds per query

**Breakdown**:
- Query embedding: ~0.5-1 second (API call)
- Vector search: ~0.1-0.5 seconds (depends on database size)
- Prompt formatting: < 0.1 seconds
- LLM generation: ~1-3 seconds (API call, depends on answer length)

**Optimization tips**:
1. Reduce n_results (fewer chunks = faster retrieval)
2. Use streaming for LLM responses (perceived performance)
3. Cache common queries
4. Use smaller LLM model (gpt-3.5-turbo instead of gpt-4o)

### Scaling Considerations

#### Small Knowledge Base (< 100 documents)
- Current implementation works fine
- Database size: < 10 MB
- Query time: < 5 seconds

#### Medium Knowledge Base (100-1000 documents)
- May need batch processing for ingestion
- Database size: 10-100 MB
- Query time: 5-10 seconds
- Consider: Index optimization in ChromaDB

#### Large Knowledge Base (> 1000 documents)
- **Critical**: Current implementation may be too slow
- Database size: > 100 MB
- Query time: > 10 seconds
- **Recommendations**:
  1. Switch to Pinecone or Weaviate (optimized vector DBs)
  2. Implement incremental ingestion (don't re-process all files)
  3. Add caching layer for embeddings
  4. Use approximate nearest neighbor search (HNSW, IVF)
  5. Shard database across multiple collections

---

## 10. Cost Estimates

### Azure OpenAI Pricing (as of 2024)

**Note**: Prices vary by region and are subject to change. Check Azure pricing page.

#### Embedding Model (text-embedding-ada-002)
- **Cost**: ~$0.0001 per 1K tokens
- **Example**: 100 page PDF (50K words ≈ 65K tokens) ≈ $0.0065 for embedding

#### LLM (gpt-4o)
- **Cost**: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- **Example query**: 500 token context + 50 token query + 200 token answer ≈ $0.025

#### Vision API (gpt-4o with vision)
- **Cost**: ~$0.03 per image (high detail)
- **Example**: 100 page PDF ≈ $3.00 for vision processing

#### Whisper
- **Cost**: ~$0.006 per minute of audio
- **Example**: 30 minute audio ≈ $0.18

### Estimated Costs for Reference Knowledge Base

Assumptions:
- 1 PDF: 100 pages
- 1 Audio: 30 minutes
- 1 Video: 30 minutes (audio only)

**One-time ingestion cost**:
- PDF vision processing: 100 pages × $0.03 = $3.00
- Audio transcription: 30 min × $0.006 = $0.18
- Video transcription: 30 min × $0.006 = $0.18
- Embedding generation: 100K tokens × $0.0001 = $0.01
- **Total ingestion: ~$3.37**

**Per-query cost**:
- Query embedding: 10 tokens × $0.0001 ≈ $0.000001
- LLM generation: (500 input + 200 output) × $0.04 ≈ $0.028
- **Total per query: ~$0.03**

**Monthly cost estimates**:
- 100 queries/month: $3.00
- 1000 queries/month: $30.00
- 10,000 queries/month: $300.00

**Cost optimization tips**:
1. Use text extraction instead of vision for PDFs (saves ~$3 per 100 pages)
2. Cache embeddings (saves embedding API calls)
3. Use gpt-3.5-turbo instead of gpt-4o (5-10x cheaper for LLM)
4. Reduce context size (fewer chunks = lower input token cost)
5. Process files once, reuse database (ingestion is one-time cost)

---

## 11. Next Steps for Real-World Deployment

### Immediate Actions

1. **Verify Azure Setup**
   ```bash
   python test_azure_setup.py
   ```

2. **Test Individual Components**
   ```bash
   python test_real_pdf.py
   python test_real_audio.py
   python test_real_video.py
   ```

3. **Run Full Ingestion**
   ```bash
   python test_ingestion.py
   ```

4. **Test RAG Pipeline**
   ```bash
   python test_rag.py
   ```

5. **Run Main CLI**
   ```bash
   python main.py
   ```

### Expected Failure Points (High Priority)

1. **Azure OpenAI Model Names**: Very likely to fail
   - **Fix**: Update deployment names in `.env`
   - **Test**: `test_azure_connection.py`

2. **Vision API Issues**: High probability
   - **Fix**: Verify GPT-4o deployment has vision enabled
   - **Fallback**: Switch to pypdf text extraction

3. **FFmpeg Video Processing**: Medium probability
   - **Fix**: Check FFmpeg installed and video has audio track
   - **Test**: Run `ffmpeg -i ./data/video.mp4` manually

4. **Rate Limiting**: Medium probability with large files
   - **Fix**: Add retry logic with exponential backoff
   - **Location**: All API calls in src/

5. **Memory Issues with Large PDFs**: Low-medium probability
   - **Fix**: Process page-by-page instead of all at once
   - **Location**: `src/data_loader.py:32-70`

### Recommended Enhancements

1. **Add Progress Indicators**
   ```python
   from tqdm import tqdm

   # In src/data_loader.py
   for i, image in tqdm(enumerate(images), total=len(images), desc="Processing PDF"):
       # ... process page
   ```

2. **Add Retry Logic**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   def api_call_with_retry(...):
       # ... API call
   ```

3. **Add Caching**
   ```python
   import hashlib
   import pickle

   def get_cached_or_compute(file_path, compute_fn):
       cache_key = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
       cache_file = f".cache/{cache_key}.pkl"

       if os.path.exists(cache_file):
           return pickle.load(open(cache_file, 'rb'))

       result = compute_fn(file_path)
       pickle.dump(result, open(cache_file, 'wb'))
       return result
   ```

4. **Add Logging**
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('rag_chatbot.log'),
           logging.StreamHandler()
       ]
   )
   ```

5. **Add Error Recovery**
   ```python
   # In src/data_loader.py load_from_directory
   failed_files = []
   successful_docs = []

   for file in files:
       try:
           doc = process_file(file)
           successful_docs.append(doc)
       except Exception as e:
           failed_files.append((file, str(e)))
           logging.error(f"Failed to process {file}: {e}")

   if failed_files:
       print(f"Warning: {len(failed_files)} files failed to process")
       # Continue with successful docs
   ```

---

## 12. Summary & Final Checklist

### Implementation Status

✅ **Complete**:
- [x] Multi-modal data loading (PDF, audio, video)
- [x] Semantic text chunking
- [x] Vector embedding generation
- [x] ChromaDB storage
- [x] RAG retrieval pipeline
- [x] LLM answer generation
- [x] CLI interface
- [x] Docker deployment
- [x] Comprehensive testing (30 tests, all mocked)
- [x] Full documentation

⚠️ **Untested with Real Components**:
- [ ] Azure OpenAI API integration
- [ ] Real PDF vision processing
- [ ] Real audio transcription
- [ ] Real video processing
- [ ] Large file handling
- [ ] Error recovery
- [ ] Performance at scale

### Pre-Deployment Checklist

**Azure Setup**:
- [ ] Azure OpenAI resource created
- [ ] GPT-4o deployed (with vision)
- [ ] text-embedding-ada-002 deployed
- [ ] Whisper deployed
- [ ] Credentials copied to `.env`
- [ ] Deployment names match `.env` values

**System Dependencies**:
- [ ] Python 3.11+ installed
- [ ] FFmpeg installed and in PATH
- [ ] Poppler installed and in PATH
- [ ] Python dependencies installed
- [ ] NumPy version < 2.0.0

**Data Preparation**:
- [ ] PDF files in `./data/`
- [ ] Audio files in `./data/`
- [ ] Video files in `./data/` (optional)
- [ ] Files are valid and not corrupted

**Testing**:
- [ ] `test_azure_setup.py` passes
- [ ] `test_real_pdf.py` passes
- [ ] `test_real_audio.py` passes
- [ ] `test_real_video.py` passes (if applicable)
- [ ] `test_ingestion.py` passes
- [ ] `test_rag.py` passes
- [ ] `python main.py` runs successfully

**Deployment**:
- [ ] Docker image builds
- [ ] Docker container runs
- [ ] Volume mounts work
- [ ] Can interact with chatbot in container

### Known Limitations

1. **No streaming**: LLM responses are not streamed (all-or-nothing)
2. **No caching**: Every query hits the API (no embedding cache)
3. **No progress indicators**: Long operations appear frozen
4. **Limited error recovery**: Many operations fail completely on first error
5. **No incremental updates**: Must re-process all files if adding new ones
6. **Single-threaded**: No parallel processing of files
7. **Memory-intensive**: Loads entire PDF into memory for vision processing
8. **No query history**: CLI doesn't save conversation history
9. **No source attribution**: Answers don't cite which chunks were used
10. **Basic prompt**: Prompt engineering is minimal

### Contact & Support

**For issues encountered during real-world deployment**:
1. Check this document first (especially sections 3-8)
2. Review Azure OpenAI documentation
3. Check ChromaDB documentation
4. Review error logs in detail
5. Use debugging commands in section 8

**Good luck with the real-world deployment!** 🚀

---

**Document Version**: 1.0
**Last Updated**: 2025-10-12
**Next Review**: After first real-world test run
