# 🎬 Capstone Demo Script: Simple-RAG v2.0
## AI-Agentic System with Reasoning & Self-Reflection

**Target Duration**: ~5 minutes
**For**: Ciklum AI Academy Engineers Capstone Project
**Project**: Simple-RAG v2.0 - Autonomous AI Agent System

---

## 🎯 Opening Hook (0:00-0:30)

> "Hi everyone! I'm excited to present Simple-RAG v2.0, an autonomous AI agent system built for the Ciklum AI Academy Capstone Project."
>
> "This isn't just a chatbot - it's a **production-grade agentic system** with multi-step reasoning, self-reflection, and intelligent tool use. Let me show you what it can do."

**[SCREEN: Show terminal with interactive_agent.py ready to run]**

---

## 🚀 Part 1: Live Demo - Agent in Action (0:30-2:30)

### Demo Query 1: Simple Greeting (Showing Token Optimization)

> "Let's start simple. Watch how the agent handles a basic greeting."

**[TYPE: "Hi"]**

**[SCREEN SHOWS:]**
```
👤 You: Hi

🤖 Agent: Thinking...
  ⚡ Reasoning skipped for trivial query (saves ~1500 tokens)
  ⚡ Self-reflection skipped (simple query - saves ~2500 tokens)

Response:
Hello! How can I assist you today?
```

> "Notice the **token optimizations** - the agent detected this is a trivial query and skipped expensive LLM operations, saving **~4000 tokens or 87% of the cost**. This is intelligent resource management."

---

### Demo Query 2: Repository Analysis (Showing Reasoning & Reflection)

> "Now let's see the real power - autonomous repository analysis with reasoning and self-reflection."

**[TYPE: "What is this repo about?"]**

**[SCREEN SHOWS - HIGHLIGHT THESE SECTIONS AS THEY APPEAR:]**

```
🤖 Agent: Thinking...

🔍 Analyzing repository...
  ✓ Found 31 top-level items
  ✓ Analyzed 20 source files
  ✓ Extracted 169 code symbols (40 classes, 129 functions)
  ✓ Identified 26 dependencies
  ✓ Mapped 11 modules

🧠 Performing LLM-based reasoning...
  ✓ Generated 5 reasoning steps

🔍 Performing self-reflection...
  ✓ Self-assessment: good
  ✅ Action: Output quality is good, proceeding to evaluation
```

**[SCROLL TO REASONING SECTION]**

> "Here's the **Reasoning & Reflection** - a key Capstone requirement. The agent creates a multi-step plan:"

**[HIGHLIGHT:]**
```
📋 Reasoning Steps (Agent's Approach):
  1. Review the repository structure (31 items)
  2. Examine the 11 modules to determine their purpose
  3. Analyze the 26 dependencies
  4. Check for README and documentation
  5. Summarize findings based on structure and modules
```

**[SCROLL TO RESPONSE]**

> "And here's the output - **2,700 characters of detailed analysis with evidence citations**:"

**[HIGHLIGHT:]**
```
## Summary
- AI agent system utilizing LangGraph [evidence: src/agent/orchestrator.py:1-20]
- AgentCLI class [evidence: interactive_agent.py:L12]
- 79 test functions identified via AST parsing
- 24 test files for comprehensive coverage

## Repository Structure
[shows actual structure]

## Key Modules & Entry Points
- src/agent/orchestrator.py
  - AgentRunner class at line 45
  - run_agent() function at line 120
```

**[SCROLL TO EVALUATION]**

> "And finally, the agent **evaluates its own performance**:"

**[HIGHLIGHT:]**
```
📊 EVALUATION SCORES
Overall Score: 93.0/100
  • Task Completion: 100.0
  • Reasoning Quality: 100.0
  • Tool Effectiveness: 100.0
  • Output Quality: 90.0
```

> "**93 out of 100** - that's production-quality output with full self-awareness of its own performance."

---

### Demo Query 3: Code-Specific Question (Showing Cache & Efficiency)

> "Now let's ask a follow-up question and watch the intelligent caching system."

**[TYPE: "Where do we use langgraph?"]**

**[SCREEN SHOWS:]**
```
🤖 Agent: Thinking...

  📦 Using cached repository data from previous query
📦 Using fully cached repository analysis (skipping expensive operations)
  ✓ Repo structure: 31 items (cached)
  ✓ Code symbols: 40 classes, 129 functions (cached)
  ✓ Dependencies: 26 (cached)

Response:
`langgraph` is used in the following file:

1. **File: src/agent/orchestrator.py**
   - Line 8: `from langgraph.graph import StateGraph, END`
   - Used in the function `create_agent_graph()` at line 19

Relevant code excerpt:
```python
Line 8: from langgraph.graph import StateGraph, END
Line 19: def create_agent_graph() -> StateGraph:
```
```

> "Notice how the agent **reused all the repository analysis** from the previous query instead of re-running expensive operations. This saved over **5,000 tokens and several seconds of processing time**."
>
> "And the answer is **accurate** - it found the exact file and line numbers where LangGraph is used, with code excerpts."

---

### Demo Query 4: Content Generation (Showing Practical Application)

> "Finally, let's show a practical use case - generating a LinkedIn post."

**[TYPE: "Write me a linkedin post about this repo and mention that Mr Tomato inspired me to do it"]**

**[SCREEN SHOWS:]**
```
🤖 Agent: Thinking...

  📦 Using cached repository data from previous query
  ⚡ Self-reflection skipped (simple query - saves ~2500 tokens)

Response:
🚀 Exciting news from my journey at Ciklum AI Academy! I'm thrilled to
introduce Simple-RAG v2.0, a major evolution from a basic system to an
advanced agentic AI 🤖.

Key technical features include a modular architecture with 11 modules,
4 dedicated to the agent system, and 26 robust dependencies such as
azure-ai-formrecognizer, openai, and langchain.

A special shoutout to Mr. Tomato, whose inspiration fueled my creativity
and drive throughout this project.

#AI #MachineLearning #AgentSystem #CiklumAI #SimpleRAGv2
```

> "Professional LinkedIn post generated in seconds, using **cached repository data** for accuracy, and including the personalization I requested about Mr. Tomato."

---

## 🏗️ Part 2: Architecture Deep Dive (2:30-4:30)

> "Now let me show you the architecture that makes this all possible."

**[SCREEN: Show architecture.mmd diagram]**

### System Overview

> "Simple-RAG v2.0 is built on **LangGraph**, which orchestrates a state-based workflow with specialized nodes. Let me walk you through the key components."

**[REFERENCE: architecture.mmd - show the main graph]**

> "The system follows this flow:"
>
> 1. **Planning Node** - Analyzes the user query and determines what type of task it is
> 2. **Reasoning Node** - Performs chain-of-thought reasoning to break down the approach
> 3. **Analysis Node** - Runs repository analysis tools to gather data
> 4. **Retrieval Node** - Queries the RAG system for relevant context
> 5. **Generation Node** - Creates the final response using LLM
> 6. **Reflection Node** - Self-evaluates the output quality
> 7. **Evaluation Node** - Scores the response on multiple dimensions

---

### Component 1: Data Preparation & Contextualization

**[REFERENCE: architecture.mmd - data preparation section]**

> "For **Data Preparation**, we have multiple specialized tools:"

**[SCREEN: Show code snippet from src/tools/]**

```python
Repository Analysis Tools:
- structure_analyzer.py    # Analyzes repo structure
- dependency_extractor.py  # Extracts requirements
- code_analyzer.py         # Uses AST to extract symbols
- test_collector.py        # Counts and categorizes tests
```

> "These tools autonomously inspect the codebase, extracting **31 top-level items, 40 classes, 129 functions, and 26 dependencies** - all without manual configuration."

---

### Component 2: RAG Pipeline Design

**[REFERENCE: architecture.mmd - RAG pipeline section]**

> "The **RAG Pipeline** uses ChromaDB as the vector store with Azure OpenAI embeddings."

**[SCREEN: Show src/chatbot.py - RAGChatbot class]**

```python
Key Components:
- DocumentProcessor: Handles PDF, MD, TXT, code files
- ChromaDB: Vector database for semantic search
- text-embedding-3-small: Azure OpenAI embeddings
- Hybrid retrieval: Combines semantic + keyword search
```

> "The system chunks documents intelligently, creates embeddings, and retrieves relevant context using **semantic similarity search**."

---

### Component 3: Reasoning & Reflection ⭐ (CAPSTONE REQUIREMENT)

**[REFERENCE: architecture.mmd - reasoning flow]**

> "This is the **core Capstone requirement** - Reasoning and Self-Reflection."

**[SCREEN: Show src/agent/nodes/reasoner.py and reflector.py]**

```python
# Reasoning Node (reasoner.py)
- Multi-step chain-of-thought reasoning
- Analyzes available context
- Plans information gathering strategy
- Generates 5-step reasoning process

# Reflection Node (reflector.py)
- Self-evaluates output quality
- Identifies gaps or weaknesses
- Decides: continue, retry, or end
- Provides critique and improvement suggestions
```

> "The agent **thinks through its approach** before acting, then **reflects on the quality** of its output. This is true autonomous behavior."

**[HIGHLIGHT: Show the refactored architecture]**

> "And here's what makes this production-quality: I **refactored the entire generator module** from **931 lines down to 170 lines** - an **81% reduction** - by applying SOLID principles and creating 8 modular components."

**[SCREEN: Show src/agent/nodes/ directory]**

```
Refactored Components:
✓ config.py              - Centralized configuration
✓ llm_client.py         - LLM wrapper with retry logic
✓ prompt_templates.py   - Template system
✓ context_builder.py    - Context construction
✓ task_detector.py      - Task classification
✓ fallback_generator.py - Graceful degradation
✓ generator.py          - Main orchestrator (81% smaller)
✓ reflector.py          - Self-reflection system
```

> "Each component has a **single responsibility**, uses **dependency injection** for testing, and can be **reused across projects**."

---

### Component 4: Tool-Calling Mechanisms

**[REFERENCE: architecture.mmd - tools section]**

> "The agent has access to **multiple tools** it can call autonomously based on reasoning:"

**[SCREEN: Show tool implementations]**

```python
Available Tools:
- analyze_repository()     # Inspects codebase structure
- extract_code_symbols()   # Uses AST parsing
- collect_tests()          # Runs pytest --collect-only
- get_coverage_report()    # Analyzes test coverage
- search_code()            # Grep for specific patterns
- retrieve_from_rag()      # Semantic search in docs
```

> "The agent **decides which tools to use** based on its reasoning, then combines the results into a coherent response."

---

### Component 5: Evaluation System

**[REFERENCE: architecture.mmd - evaluation section]**

> "Finally, the **Evaluation System** provides multi-dimensional scoring:"

**[SCREEN: Show src/evaluation/evaluator.py]**

```python
Evaluation Dimensions:
- Task Completion (0-100)      # Did it answer the question?
- Reasoning Quality (0-100)    # Was the approach logical?
- Tool Effectiveness (0-100)   # Did it use tools well?
- Reflection Quality (0-100)   # How good was self-critique?
- Output Quality (0-100)       # Final response quality

Specialized Evaluators:
- RepoAnalysisEvaluator    # For repository analysis tasks
- LinkedInPostEvaluator    # For content generation
- CodeQuestionEvaluator    # For code-specific questions
```

> "This gives us **objective metrics** to measure agent performance. We saw scores ranging from **67 to 93 out of 100** depending on task complexity."

---

### Token Optimization Features

> "One more technical highlight - **intelligent token optimization**:"

**[SCREEN: Show src/agent/nodes/planner.py - skip logic]**

```python
Token Optimizations:
1. Skip reasoning for trivial queries     (saves ~1500 tokens)
2. Skip reflection for simple tasks       (saves ~2500 tokens)
3. Cache repository data across queries   (saves ~5000 tokens)
4. Detect task type and set max_iterations accordingly

Results:
- Simple queries: 87% token savings
- Follow-up questions: 85% token savings
- Overall efficiency: 54-87% cost reduction
```

> "This makes the system **cost-effective** for production use while maintaining high quality."

---

## 🎯 Part 3: Capstone Requirements Fulfillment (4:30-5:00)

> "Let me summarize how this project fulfills all Capstone requirements:"

**[SCREEN: Show checklist]**

```
✅ Data Preparation & Contextualization
   → Repository analysis tools, code extraction, AST parsing

✅ RAG Pipeline Design
   → ChromaDB + Azure embeddings + hybrid retrieval

✅ Reasoning & Reflection ⭐
   → Multi-step chain-of-thought + self-evaluation system

✅ Tool-Calling Mechanisms
   → 6+ autonomous tools for repo analysis and code search

✅ Evaluation System
   → Multi-dimensional scoring (67-93/100 range)

✅ Production Quality
   → 81% code reduction, SOLID principles, 33/33 tests passing
```

---

## 🎬 Closing (5:00-5:30)

> "Simple-RAG v2.0 demonstrates **production-grade agentic AI** with:"
>
> - **Autonomous reasoning** and self-reflection
> - **Intelligent tool use** for repository analysis
> - **Cost optimization** with 54-87% token savings
> - **High-quality outputs** scoring up to 93/100
> - **Clean, modular architecture** following SOLID principles
>
> "Thank you to the **Ciklum AI Academy** for this incredible learning journey, and to **Mr. Tomato** for the inspiration and guidance!"
>
> "The complete code, architecture diagrams, and documentation are available in my GitHub repository. I'm excited to hear your feedback!"

**[SCREEN: Show final slide with links]**

```
🔗 Links:
- GitHub Repository: [your-link]
- Architecture Diagram: architecture.mmd
- Demo Video: [this video]
- LinkedIn Post: [generated by the agent]

Built with 💙 at Ciklum AI Academy
```

---

## 📝 Speaker Notes & Tips

### Timing Guide
- Part 1 (Demo): 2:00 minutes - **Focus on showing, not telling**
- Part 2 (Architecture): 2:00 minutes - **Reference diagrams heavily**
- Part 3 (Fulfillment): 0:30 minutes - **Quick recap**
- Closing: 0:30 minutes - **Strong finish**

### What to Emphasize
1. **The 93/100 score** - shows quality
2. **Token savings (87%)** - shows efficiency
3. **Reasoning & Reflection** - core Capstone requirement
4. **Production quality refactoring** - shows engineering maturity
5. **Cached queries** - shows intelligent design

### Screen Recording Tips
1. **Start with clean terminal** - no clutter
2. **Use larger font** - easy to read in video
3. **Pause after each agent response** - let viewers read
4. **Highlight key sections** - use mouse or annotations
5. **Keep mermaid diagrams ready** - quick transitions

### Common Questions to Prepare For
1. **Q: Why LangGraph instead of CrewAI?**
   - A: LangGraph gives fine-grained control over state flow and conditional routing, essential for self-reflection loops

2. **Q: How does caching work?**
   - A: Repository data is cached after first analysis and reused for follow-up queries within same session

3. **Q: What's the most challenging part?**
   - A: Balancing token efficiency with output quality, achieved through intelligent skip logic

4. **Q: How would you deploy this?**
   - A: Docker container with Azure OpenAI, could add FastAPI endpoint for API access

5. **Q: What would you add next?**
   - A: Memory persistence across sessions, multi-repo support, web interface

---

## 🎨 Visual Assets Checklist

**For Video Recording:**
- [ ] Clean terminal with large font (16-18pt)
- [ ] architecture.mmd rendered and ready to show
- [ ] Code editor with key files open in tabs
- [ ] Browser with GitHub repo page ready
- [ ] Screenshot of test results (33/33 passing)
- [ ] Screenshot of token savings comparison

**For Presentation Slides (Optional):**
- [ ] Title slide with project name
- [ ] Architecture diagram from mermaid
- [ ] Before/after refactoring comparison
- [ ] Token savings chart
- [ ] Evaluation scores visualization
- [ ] Capstone requirements checklist
- [ ] Thank you slide with links

---

## 🚀 Alternative Demo Flow (If Short on Time)

If you need to compress to ~3 minutes:

**Quick Demo (1:30)**:
- Show "What is this repo about?" query only (shows all features)
- Highlight reasoning, reflection, and 93/100 score

**Quick Architecture (1:00)**:
- Show architecture.mmd diagram
- Point out 5 components briefly
- Mention 81% code reduction

**Quick Closing (0:30)**:
- Capstone requirements checkboxes
- Thank you and links

---

## 📊 Key Metrics to Mention

**Code Quality:**
- 931 lines → 170 lines (81% reduction)
- 8 modular components created
- 33/33 tests passing
- 100% backward compatible

**Performance:**
- 54-87% token savings
- 93/100 quality score on repo analysis
- Sub-second response for cached queries

**Capabilities:**
- 169 code symbols extracted (40 classes, 129 functions)
- 26 dependencies analyzed
- 24 test files discovered
- 6+ autonomous tools

**Technical Stack:**
- Python 3.11
- LangGraph for orchestration
- Azure OpenAI (GPT-4o)
- ChromaDB for vector storage
- Pytest for testing

---

## 🎯 Success Indicators

**Your demo is successful if viewers understand:**
1. ✅ The agent thinks and reflects (not just responds)
2. ✅ It's production-quality (not just a prototype)
3. ✅ It's efficient (token optimization matters)
4. ✅ It's modular (can be reused/extended)
5. ✅ You fulfilled ALL Capstone requirements

**Bonus points if they:**
- Ask technical questions (shows engagement)
- Comment on code quality (shows you're thinking like an engineer)
- Want to see the GitHub repo (shows you created value)

---

## 🎬 Final Tips

1. **Practice the demo 2-3 times** - know exactly where to scroll
2. **Time yourself** - adjust pace to fit 5 minutes
3. **Have backup queries ready** - in case something fails
4. **Show confidence** - you built something impressive!
5. **Smile and enjoy** - you earned this moment! 🎉

Good luck with your Capstone presentation! 🚀
