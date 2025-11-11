# Tools Module

This module provides repository analysis and generation tools for the agent.

## Repository Tools (`repository_tools.py`)

Comprehensive tools for analyzing codebases:

### 1. Directory Structure Analysis
```python
analyze_directory_structure(repo_path: str, max_depth: int = 3) -> Dict
```
- Recursively analyzes directory structure
- Returns nested dict with file/folder hierarchy
- Respects `.gitignore` patterns

### 2. Source File Reading
```python
read_source_files(repo_path: str, extensions: List[str]) -> List[Dict]
```
- Reads all source files matching extensions
- Returns list of {path, content, size, lines}
- Filters by file type (.py, .js, .md, etc.)

### 3. Dependency Extraction
```python
extract_dependencies(repo_path: str) -> Dict
```
- Parses `requirements.txt`, `package.json`, etc.
- Returns dict with package names and versions
- Identifies main dependencies vs dev dependencies

### 4. Architecture Mapping
```python
generate_architecture_map(repo_path: str) -> Dict
```
- Maps module structure and imports
- Identifies entry points and key modules
- Returns architecture overview

### 5. Code Symbol Extraction (AST-based)
```python
extract_code_symbols(file_path: str) -> Dict
```
- Uses LibCST for Python AST parsing
- Extracts:
  - Classes with methods and line numbers
  - Functions with signatures and line numbers
  - Test functions (pytest)
- Returns concrete code references for evidence-based analysis

### 6. Verification Commands
```python
run_verification_commands(repo_path: str) -> Dict
```
- Runs subprocess commands:
  - `pytest --collect-only`: Actual test count
  - `coverage run && coverage report`: Real coverage %
  - `find tests -name 'test_*.py'`: Test file count
- Returns real outputs (not mocked/estimated)

## RAG Tools (`rag_tools.py`)

Tools for RAG retrieval and context management:

### 1. Context Retrieval
```python
retrieve_context(query: str, vector_store, top_k: int = 5) -> List[Dict]
```
- Retrieves relevant chunks from ChromaDB
- Uses cosine similarity ranking
- Returns top-k most relevant contexts

### 2. Context Reranking
```python
rerank_context(query: str, contexts: List[Dict]) -> List[Dict]
```
- Reranks retrieved contexts by relevance
- Optional cross-encoder scoring
- Returns reordered contexts

## Generation Tools (`generation_tools.py`)

Tools for generating outputs:

### 1. Response Generation
```python
generate_response(prompt: str, llm_client, **kwargs) -> str
```
- Generates text using GPT-4o
- Handles retry logic and rate limiting
- Returns generated response

### 2. Template-Based Generation
```python
generate_from_template(template: str, context: Dict) -> str
```
- Uses Jinja2 templates for structured output
- Supports: repository analysis, LinkedIn posts, Q&A
- Returns formatted response

## Usage Examples

### Repository Analysis
```python
from src.tools.repository_tools import (
    analyze_directory_structure,
    extract_code_symbols,
    run_verification_commands
)

# Analyze structure
structure = analyze_directory_structure("./repo")

# Extract code symbols (evidence-based)
symbols = extract_code_symbols("./repo/src/main.py")
print(f"Found {len(symbols['classes'])} classes")
print(f"Found {len(symbols['functions'])} functions")

# Run verification commands
outputs = run_verification_commands("./repo")
print(f"Real test count: {outputs['pytest_collect']}")
print(f"Real coverage: {outputs['coverage_report']}")
```

### RAG Retrieval
```python
from src.tools.rag_tools import retrieve_context

# Retrieve relevant context
contexts = retrieve_context(
    query="How does the agent work?",
    vector_store=chroma_client,
    top_k=5
)

for ctx in contexts:
    print(f"Chunk: {ctx['text'][:100]}...")
    print(f"Score: {ctx['score']}")
```

## Testing

See `tests/test_tools/` for comprehensive tests:
- `test_repository_tools.py`: Repository analysis tests
- `test_rag_tools.py`: RAG retrieval tests
- `test_generation_tools.py`: Generation tests
