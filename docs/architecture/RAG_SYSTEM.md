# RAG (Retrieval-Augmented Generation) System

## Overview

The RAG system enables the agent to query a **knowledge base** stored in ChromaDB to answer questions that require domain-specific information beyond the agent's training data.

## Problem It Solves

**Without RAG:**
```
User: "What is the difference between the v1.0 and v2.0 agent?"
Agent: "I don't have information about these versions" ❌
```

**With RAG:**
```
User: "What is the difference between the v1.0 and v2.0 agent?"
Agent retrieves documentation → "v2.0 adds self-reflection, LangGraph orchestration, and evidence-based analysis..." ✅
```

## Architecture

### 1. Vector Store (`vector_store.py`)

**ChromaDB Persistent Storage:**
```python
def get_vector_database_collection():
    """Initialize or get ChromaDB collection"""
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Use OpenAI embeddings
    embedding_function = OpenAIEmbeddingFunction(
        api_key=config.openai_api_key,
        model_name="text-embedding-ada-002"
    )
    
    collection = client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}  # Cosine similarity
    )
    
    return collection
```

**Storage Format:**
- **Documents**: Text chunks (paragraphs, sections)
- **Embeddings**: 1536-dimensional vectors (OpenAI ada-002)
- **Metadata**: `{"source": "file.md", "chunk_id": "file.md_0"}`
- **IDs**: Unique identifier per chunk

### 2. Data Ingestion

**Batch Ingestion Script** (`ingest_batch.py`):

```python
def ingest_documents(data_dir: str):
    """Ingest all markdown files from data directory"""
    collection = get_vector_database_collection()
    
    for md_file in Path(data_dir).glob("*.md"):
        content = md_file.read_text()
        
        # Split into chunks (by paragraph)
        chunks = content.split("\n\n")
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:  # Skip tiny chunks
                collection.add(
                    documents=[chunk],
                    metadatas=[{"source": md_file.name, "chunk_id": f"{md_file.name}_{i}"}],
                    ids=[f"{md_file.name}_{i}"]
                )
    
    print(f"✅ Ingested {collection.count()} chunks")
```

**Usage:**
```bash
# Ingest markdown files from data/ directory
python ingest_batch.py

# Output:
# Processing README_V2.md...
# Processing ARCHITECTURE.md...
# ✅ Ingested 127 chunks
```

### 3. RAG Retrieval Node (`retriever.py`)

**Triggered when:** Task type is `"answer_question"`

**Process:**

```python
async def retrieval_node(state: AgentState) -> AgentState:
    task = state["task"]
    
    # Query ChromaDB
    collection = get_vector_database_collection()
    
    if collection.count() == 0:
        # No data in knowledge base
        return state
    
    # Semantic search (top 5 results)
    results = collection.query(
        query_texts=[task],
        n_results=5
    )
    
    # Build retrieved context
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source"]
        chunks.append({
            "content": doc,
            "source": source,
            "similarity": results["distances"][0][i]  # Lower = more similar
        })
    
    # Store in state
    new_state["retrieved_context"] = chunks
    new_state["reasoning_steps"] += [
        f"Retrieval: Found {len(chunks)} relevant chunks from knowledge base"
    ]
    
    return new_state
```

**Example Retrieved Context:**
```python
[
    {
        "content": "v2.0 introduces self-reflection where the agent critiques its own reasoning...",
        "source": "README_V2.md",
        "similarity": 0.23
    },
    {
        "content": "LangGraph orchestrates nodes: planner → retriever → reasoner → reflector...",
        "source": "ARCHITECTURE.md",
        "similarity": 0.31
    }
]
```

### 4. Generator Integration

**Context Building** (in `generator.py`):

```python
# Add retrieved context to LLM prompt
if retrieved_context:
    context += "\n🔍 RETRIEVED KNOWLEDGE BASE CONTEXT:\n"
    context += "="*60 + "\n"
    
    for i, chunk in enumerate(retrieved_context, 1):
        source = chunk.get("source", "unknown")
        content = chunk.get("content", "")
        
        context += f"\n**Source {i}: {source}**\n"
        context += f"{content}\n"
        context += f"(Similarity: {chunk.get('similarity', 'N/A')})\n\n"
    
    context += "="*60 + "\n"
    context += "Use the above retrieved context to answer the question.\n\n"
```

**Prompt Instruction:**
```
You have access to retrieved knowledge base content.
Use this information to provide an accurate, evidence-based answer.
Cite the source document when referencing retrieved information.
```

## Data Flow

```
1. User Question: "What is v2.0?"
   ↓
2. Task Detection: Classified as "answer_question"
   ↓
3. Planner Node: next_action = "retrieve"
   ↓
4. Retrieval Node:
   - Query ChromaDB with question
   - Get top 5 semantically similar chunks
   - Store in state["retrieved_context"]
   ↓
5. Reasoner Node:
   - Analyze question + retrieved context
   - Generate reasoning steps
   ↓
6. Reflector Node:
   - Check if retrieved context was used
   - Critique if answer doesn't cite sources
   ↓
7. Generator Node:
   - Build prompt with retrieved chunks
   - Generate answer citing sources
   ↓
8. Output:
   "v2.0 introduces self-reflection and LangGraph orchestration [Source: README_V2.md]..."
```

## ChromaDB Details

### Embedding Model
- **Model**: `text-embedding-ada-002` (OpenAI)
- **Dimensions**: 1536
- **Cost**: ~$0.0001 per 1K tokens

### Similarity Metric
- **Metric**: Cosine similarity
- **Range**: 0.0 (identical) to 2.0 (opposite)
- **Typical threshold**: < 0.5 for relevant matches

### Index Type
- **Type**: HNSW (Hierarchical Navigable Small World)
- **Trade-off**: Fast approximate search vs exact search
- **Good for**: Large knowledge bases (10K+ documents)

### Storage Location
```
./chroma_db/
├── chroma.sqlite3  # Metadata storage
└── [uuid]/          # Vector storage
```

### Collection Metadata
```python
{
    "name": "knowledge_base",
    "hnsw:space": "cosine",
    "hnsw:construction_ef": 200,  # Build quality
    "hnsw:search_ef": 100         # Query quality
}
```

## Ingestion Strategies

### Strategy 1: Paragraph-based (Current)
```python
# Split by double newline
chunks = content.split("\n\n")
```
**Pros:** Natural semantic boundaries  
**Cons:** Chunks can be uneven size

### Strategy 2: Fixed-size with Overlap
```python
def chunk_with_overlap(text, size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap  # Overlap for context
    return chunks
```
**Pros:** Consistent size, context preservation  
**Cons:** Can split mid-sentence

### Strategy 3: Semantic Chunking
```python
# Use sentence boundaries
sentences = text.split(". ")
chunks = []
current_chunk = ""
for sent in sentences:
    if len(current_chunk) + len(sent) < 500:
        current_chunk += sent + ". "
    else:
        chunks.append(current_chunk)
        current_chunk = sent + ". "
```
**Pros:** Never splits sentences  
**Cons:** More complex logic

## Query Optimization

### Reranking (Advanced)
```python
# Get more results, then rerank
results = collection.query(query_texts=[task], n_results=20)

# Rerank by custom score
reranked = sorted(
    results["documents"][0],
    key=lambda doc: calculate_relevance(task, doc),
    reverse=True
)[:5]  # Top 5 after reranking
```

### Query Expansion
```python
# Expand query with synonyms
expanded_query = f"{task} {get_synonyms(task)}"
results = collection.query(query_texts=[expanded_query], ...)
```

### Metadata Filtering
```python
# Filter by source
results = collection.query(
    query_texts=[task],
    n_results=5,
    where={"source": {"$eq": "README_V2.md"}}  # Only from README
)
```

## Evaluation

### Retrieval Quality Metrics

**Scored in `metrics.py`:**
```python
def _evaluate_tool_effectiveness(state: AgentState) -> float:
    score = 0.0
    retrieved_context = state.get("retrieved_context")
    
    if retrieved_context:
        # Retrieved something
        score += 30.0
        
        # Check if context is relevant
        final_output = state.get("final_output", "")
        used_count = sum(
            1 for chunk in retrieved_context
            if chunk["source"] in final_output  # Source cited
        )
        
        if used_count >= 3:
            score += 20.0  # Good usage
        elif used_count >= 1:
            score += 10.0  # Some usage
    
    return score
```

### Manual Quality Check
```bash
# Test retrieval
python -c "
from src.vector_store import get_vector_database_collection
collection = get_vector_database_collection()

results = collection.query(
    query_texts=['What is self-reflection?'],
    n_results=5
)

for doc in results['documents'][0]:
    print(doc[:200])
    print('---')
"
```

## Example Queries & Results

### Query 1: "What is the difference between v1.0 and v2.0?"

**Retrieved Chunks:**
1. "v2.0 introduces LangGraph for state management and orchestration..." (README_V2.md, similarity: 0.18)
2. "Key enhancements: self-reflection, BEFORE/AFTER demonstration..." (README_V2.md, similarity: 0.24)
3. "v1.0 uses simple sequential processing without reflection..." (README.md, similarity: 0.31)

**Generated Answer:**
```
The main differences are:

1. **Orchestration**: v2.0 uses LangGraph for state management [Source: README_V2.md], while v1.0 uses sequential processing [Source: README.md]

2. **Self-Reflection**: v2.0 introduces critical self-assessment where the agent critiques its own reasoning [Source: README_V2.md]

3. **Output Demonstration**: v2.0 shows BEFORE/AFTER comparison when improvement is needed [Source: README_V2.md]
```

### Query 2: "How does self-reflection work?"

**Retrieved Chunks:**
1. "The reflector node performs critical self-assessment with temperature=0.3..." (ARCHITECTURE.md, similarity: 0.15)
2. "Reflection outputs assessment: 'good' or 'needs_improvement'..." (SELF_REFLECTION.md, similarity: 0.19)

**Generated Answer:**
```
Self-reflection works through a dedicated reflector node that critically evaluates the agent's reasoning [Source: ARCHITECTURE.md]. It uses a lower temperature (0.3) for consistent critique and outputs an assessment of either 'good' or 'needs_improvement' [Source: SELF_REFLECTION.md].
```

## Best Practices

### 1. Curate Knowledge Base
✅ Include: Architecture docs, READMEs, design decisions  
❌ Avoid: Code files, logs, temporary files

### 2. Update Regularly
```bash
# Re-ingest after doc changes
python ingest_batch.py
```

### 3. Monitor Usage
```python
# Track retrieval in logs
print(f"📊 Retrieved {len(chunks)} chunks")
print(f"   Sources: {[c['source'] for c in chunks]}")
```

### 4. Handle Empty Knowledge Base
```python
if collection.count() == 0:
    print("⚠️ No knowledge base data - retrieval skipped")
    return state  # Skip retrieval gracefully
```

## Troubleshooting

### Issue: "No results retrieved"
**Cause:** Query doesn't match any documents semantically  
**Solution:** Add more diverse content to knowledge base

### Issue: "Retrieval but not used in answer"
**Cause:** Generator doesn't incorporate retrieved context  
**Solution:** Check prompt includes "Use retrieved context above"

### Issue: "ChromaDB not found"
**Cause:** Knowledge base not ingested  
**Solution:**
```bash
python ingest_batch.py
```

### Issue: "Irrelevant chunks retrieved"
**Cause:** Embeddings not capturing semantic meaning  
**Solution:** Use better chunking strategy or query expansion

## Future Enhancements

1. **Hybrid Search**: Combine semantic + keyword search
2. **Reranking**: Use cross-encoder for better relevance
3. **Multi-turn Memory**: Track conversation context
4. **Source Attribution**: Highlight exact passages used
5. **Confidence Scores**: Indicate retrieval certainty

## Related Documentation

- [Vector Store Implementation](./VECTOR_STORE.md) - ChromaDB setup
- [Retrieval Node](./RETRIEVAL_NODE.md) - Query implementation
- [Generator Integration](./GENERATOR_NODE.md) - Context usage
- [Evaluation Metrics](./EVALUATION_METRICS.md) - RAG scoring
