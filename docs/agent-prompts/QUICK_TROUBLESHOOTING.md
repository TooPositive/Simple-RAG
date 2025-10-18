# Quick Troubleshooting Guide

## 🚨 Most Common Issues & Fast Fixes

This is a condensed troubleshooting guide for the most likely failures when running with real components.

---

## Issue 1: "Incorrect API key provided"

**Error**:
```
AuthenticationError: Incorrect API key provided
```

**Quick Fix**:
```bash
# 1. Check .env exists
ls -la .env

# 2. Check key is set (should show first 10 chars)
cat .env | grep AZURE_OPENAI_API_KEY

# 3. Test key directly
curl "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2023-12-01-preview" \
  -H "api-key: $(grep AZURE_OPENAI_API_KEY .env | cut -d '=' -f2 | tr -d '"')"
```

**Common Causes**:
- `.env` file not in project root
- Extra quotes around API key in `.env`
- Spaces in API key value
- Using wrong key (need Azure OpenAI, not OpenAI)

---

## Issue 2: "The API deployment does not exist"

**Error**:
```
NotFoundError: The API deployment for this resource does not exist
```

**Quick Fix**:
```bash
# 1. List your actual deployments
curl "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2023-12-01-preview" \
  -H "api-key: $AZURE_OPENAI_API_KEY" | jq '.data[].id'

# 2. Update .env with EXACT names
# Edit these lines in .env:
EMBEDDING_MODEL_NAME="<exact-deployment-name-from-above>"
LLM_MODEL_NAME="<exact-deployment-name-from-above>"
```

**Also check**: `src/data_loader.py:88` has hardcoded `model="whisper"` - update if your Whisper deployment has different name.

---

## Issue 3: FFmpeg not found

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Quick Fix**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# Verify
ffmpeg -version
```

---

## Issue 4: Poppler not found

**Error**:
```
PDFInfoNotInstalledError: Unable to get page count
```

**Quick Fix**:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y poppler-utils

# Verify
pdfinfo -v
```

---

## Issue 5: NumPy 2.0 error

**Error**:
```
AttributeError: np.float_ was removed in the NumPy 2.0 release
```

**Quick Fix**:
```bash
pip install 'numpy<2.0.0'
pip show numpy  # Should show 1.x.x
```

---

## Issue 6: "I couldn't find any relevant information"

**Symptom**: Chatbot always says no information found

**Quick Debug**:
```python
# Check database has data
from src.vector_store import get_vector_database_collection
collection = get_vector_database_collection()
print(f"Database has {collection.count()} chunks")

# If count is 0, database is empty - need to run ingestion
```

**Quick Fix**:
```bash
# Delete existing empty database
rm -rf ./chroma_db

# Run main.py - it will re-ingest data
python main.py
```

---

## Issue 7: Vision API not working

**Error**:
```
InvalidRequestError: Vision is not supported in this deployment
```

**Quick Fix (Option 1 - Use different model)**:
Update `.env`:
```env
LLM_MODEL_NAME="gpt-4o"  # or "gpt-4-vision-preview"
```

**Quick Fix (Option 2 - Switch to text extraction)**:
Edit `src/data_loader.py`, replace `load_text_from_pdf` function:
```python
import pypdf

def load_text_from_pdf(file_path: Union[str, Path]) -> str:
    """Extract text from PDF using pypdf (fallback method)"""
    reader = pypdf.PdfReader(str(file_path))
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            pages_text.append(text)
    return "\n\n".join(pages_text)
```

---

## Issue 8: Memory error with large PDF

**Error**:
```
MemoryError: Unable to allocate array
```

**Quick Fix**:
Edit `src/data_loader.py:32-70`, process page-by-page:
```python
def load_text_from_pdf(file_path: Union[str, Path]) -> str:
    from pdf2image import pdfinfo_from_path

    # Get page count
    info = pdfinfo_from_path(file_path)
    page_count = info["Pages"]

    all_descriptions = []

    # Process one page at a time
    for page_num in range(1, page_count + 1):
        print(f"Processing page {page_num}/{page_count}...")
        images = convert_from_path(file_path, first_page=page_num, last_page=page_num)

        # Process this single page
        buffered = BytesIO()
        images[0].save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        client = AzureOpenAI(...)
        response = client.chat.completions.create(...)
        all_descriptions.append(response.choices[0].message.content)

    return "\n\n".join(all_descriptions)
```

---

## Issue 9: Audio file too large (> 25MB)

**Error**:
```
InvalidRequestError: File size exceeds the maximum limit
```

**Quick Fix**:
Add check in `src/data_loader.py` before line 88:
```python
import os

file_size = os.path.getsize(audio_file_path)
max_size = 25 * 1024 * 1024  # 25MB

if file_size > max_size:
    print(f"Warning: {audio_file_path} is too large ({file_size/1024/1024:.1f}MB)")
    print("Consider splitting the audio file or using a different transcription method")
    raise ValueError(f"Audio file exceeds 25MB limit")
```

---

## Issue 10: Rate limiting

**Error**:
```
RateLimitError: Rate limit reached for requests
```

**Quick Fix**:
Wrap API calls with retry:
```python
from openai import RateLimitError
import time

def call_with_retry(api_call_fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api_call_fn()
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

# Use in src/vector_store.py:49
response = call_with_retry(
    lambda: client.embeddings.create(input=documents_to_add, model=settings.embedding_model_name)
)
```

---

## Testing Sequence

Run these in order to isolate issues:

```bash
# 1. Test config
python -c "from src.config import settings; print('✅ Config OK')"

# 2. Test Azure connection
python test_azure_setup.py

# 3. Test PDF processing
python test_real_pdf.py

# 4. Test audio processing
python test_real_audio.py

# 5. Test full ingestion
python test_ingestion.py

# 6. Test RAG pipeline
python test_rag.py

# 7. Run main chatbot
python main.py
```

If any step fails, fix it before moving to next step.

---

## Emergency Fallbacks

### If Vision API completely fails:
Use pypdf for text extraction (see Issue 7)

### If Whisper API fails:
Comment out audio/video processing in `src/data_loader.py:122-126`:
```python
# elif file_path.suffix.lower() in [".mp3", ".wav", ".m4a"]:
#     text = transcribe_audio_file(file_path)
#     documents.append({"source": file_path.name, "content": text})
```

### If embeddings fail:
Check you're using correct model name and deployment exists

### If LLM generation fails:
Try switching to gpt-3.5-turbo in `.env`:
```env
LLM_MODEL_NAME="gpt-35-turbo"  # Note: 35, not 3.5
```

### If ChromaDB fails:
Delete and recreate:
```bash
rm -rf ./chroma_db
python main.py  # Will recreate
```

---

## Quick Diagnostics

```bash
# Check all system dependencies
command -v python3 && python3 --version
command -v ffmpeg && ffmpeg -version | head -1
command -v pdfinfo && pdfinfo -v | head -1

# Check Python packages
pip list | grep -E "openai|chromadb|numpy|pdf2image"

# Check environment
cat .env | grep -v "^#" | grep "="

# Check data files
ls -lh ./data/

# Check database
ls -lh ./chroma_db/ 2>/dev/null || echo "Database not initialized"
```

---

## Getting Help

1. Check full guide: `REAL_WORLD_DEPLOYMENT_GUIDE.md`
2. Check error logs: Look for full stack trace
3. Enable debug logging: Add `import logging; logging.basicConfig(level=logging.DEBUG)` to top of main.py
4. Test components individually: Use test scripts
5. Check Azure Portal: Verify deployments exist

---

**Quick Reference Created**: 2025-10-12
**For Full Details**: See `REAL_WORLD_DEPLOYMENT_GUIDE.md`
