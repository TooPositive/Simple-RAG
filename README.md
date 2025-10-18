# RAG Chatbot for "Databases for GenAI" Lecture

A production-ready Retrieval-Augmented Generation (RAG) chatbot built from scratch using multi-modal processing techniques. This chatbot can ingest knowledge from PDFs, audio files, and video files, then answer questions about the content with high accuracy.

## 🌟 Features

- **Multi-Modal Document Processing**
  - **PDFs**: Converts pages to images and uses Vision Language Models (VLM) for extraction
  - **Audio**: Transcribes using Azure OpenAI Whisper
  - **Video (MP4)**: Extracts audio with FFmpeg, then transcribes

- **Advanced RAG Pipeline**
  - Semantic text chunking with overlap
  - Vector embeddings using Azure OpenAI
  - Persistent ChromaDB vector database
  - Context-aware answer generation

- **Production-Ready Architecture**
  - Fully Dockerized
  - Comprehensive test suite (pytest)
  - Secure configuration management
  - Extensive code documentation

## 🏗️ Architecture

```
User Question
     ↓
Embed Question (Azure OpenAI)
     ↓
Vector Search (ChromaDB)
     ↓
Retrieve Relevant Chunks
     ↓
Format Prompt with Context
     ↓
Generate Answer (GPT-4o)
     ↓
Return Answer
```

## 📋 Prerequisites

- **Docker** (recommended) OR Python 3.11+
- **Azure OpenAI** account with:
  - GPT-4o deployment (vision-enabled)
  - text-embedding-ada-002 deployment
  - Whisper deployment
- **Knowledge base files** in `./data` directory

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
cd "Simple RAG"
```

### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY="your_actual_api_key"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
OPENAI_API_VERSION="2023-12-01-preview"
EMBEDDING_MODEL_NAME="text-embedding-ada-002"
LLM_MODEL_NAME="gpt-4o"
```

### 3. Add Knowledge Base

Place your files in the `./data` directory:

```bash
# Supported formats:
# - PDF (.pdf)
# - Audio (.mp3, .wav, .m4a)
# - Video (.mp4)
```

### 4. Run with Docker

```bash
# Build the Docker image
docker-compose build

# Run the chatbot
docker-compose up
```

The chatbot will:
1. Process all files in `./data` (first run only)
2. Generate and store embeddings
3. Start an interactive CLI

## 💻 Local Development Setup

If you prefer to run without Docker:

### 1. Install System Dependencies

**macOS:**
```bash
brew install ffmpeg poppler
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg poppler-utils
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Chatbot

```bash
python main.py
```

## 🧪 Testing

### Run Tests

Run the comprehensive test suite:

```bash
# Run all tests
pytest -v

# Run only real integration tests (uses actual Azure APIs, costs ~$0.16)
pytest -v -m real_integration tests/test_real_e2e.py
```

### Verify Data Integrity

After ingestion, verify that all data was correctly processed and stored:

```bash
python3 verify_data_integrity.py
```

This verification script checks:
- ✅ Correct chunk count (43 chunks expected)
- ✅ Proper source attribution (all chunks have metadata)
- ✅ Chunk sizes within expected range (200-1200 characters)
- ✅ Data correspondence with original source files
- ✅ Overlap factors (1.0-1.3x expected)

**Sample Output:**
```
================================================================================
✅ ALL CHECKS PASSED - Data integrity verified!
================================================================================

✓ Total chunks: 43
✓ All chunks have source attribution: Yes
✓ Chunks within expected size range: Yes
✓ PDF data integrity verified (1.07x overlap)
✓ Video data integrity verified (1.24x overlap)
```

See `DATA_VERIFICATION_REPORT.md` for detailed results.

## 📁 Project Structure

```
Simple RAG/
├── src/
│   ├── config.py           # Configuration and environment variables
│   ├── data_loader.py      # Multi-modal document processing
│   ├── text_processor.py   # Text chunking
│   ├── vector_store.py     # ChromaDB and embeddings
│   └── chatbot.py          # RAG pipeline orchestration
├── tests/
│   ├── conftest.py         # Test configuration
│   ├── test_config.py
│   ├── test_data_loader.py
│   ├── test_text_processor.py
│   ├── test_vector_store.py
│   └── fixtures/           # Test data
├── data/                   # Your knowledge base files (not in git)
├── chroma_db/             # Vector database (not in git)
├── main.py                # CLI entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🎯 Usage Example

```
You: What are the production 'Do's' for RAG?

🤖 Thinking...

Bot: Based on the lecture content, the production 'Do's' for RAG include:

1. **Use hybrid search**: Combine vector search with keyword search for better
   retrieval accuracy.

2. **Implement proper chunking**: Break documents into semantically meaningful
   chunks with appropriate overlap to preserve context.

3. **Monitor and evaluate**: Track retrieval quality, answer relevance, and
   user satisfaction metrics.

4. **Handle edge cases**: Gracefully deal with questions outside the knowledge
   base scope.

[The answer continues with specific details from your knowledge base]
```

## 🔧 Configuration

All settings are managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | **Required** |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | **Required** |
| `OPENAI_API_VERSION` | API version | **Required** |
| `EMBEDDING_MODEL_NAME` | Embedding model deployment | `text-embedding-ada-002` |
| `LLM_MODEL_NAME` | LLM deployment (must support vision) | `gpt-4o` |

## 🐛 Troubleshooting

### "No documents found in data directory"
- Ensure files are in `./data`
- Check file formats (.pdf, .mp3, .wav, .m4a, .mp4)

### "Environment variable not set"
- Verify `.env` file exists in project root
- Check all required variables are set

### Docker issues
- Ensure Docker daemon is running
- Try `docker-compose down` then `docker-compose up --build`

### FFmpeg/Poppler errors
- Local development: Install system dependencies
- Docker: Already included in the image

## 📝 How It Works

### 1. Multi-Modal PDF Processing

Instead of traditional text extraction, we use a cutting-edge approach:

```
PDF → Convert pages to images → GPT-4o Vision → Text descriptions
```

This handles:
- Scanned documents
- Complex layouts
- Charts and diagrams
- Tables with mixed content

### 2. Audio/Video Transcription

```
Audio file → Whisper API → Text transcription
Video file → Extract audio (FFmpeg) → Whisper API → Text
```

### 3. RAG Pipeline

```
All sources → Chunk → Embed → Store in ChromaDB
User query → Embed → Search ChromaDB → Retrieve top k chunks
Retrieved chunks + Query → LLM → Contextual answer
```

## 🤝 Contributing

This is an educational project. Feel free to:
- Report issues
- Suggest improvements
- Fork and experiment

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built for the "Databases for GenAI" lecture assignment
- Uses Azure OpenAI, ChromaDB, LangChain, FFmpeg, and pdf2image
- Implements modern RAG best practices

## 📧 Contact

For questions about this implementation, please refer to the course materials or create an issue in the repository.

---

**Built with ❤️ using Claude Code**
