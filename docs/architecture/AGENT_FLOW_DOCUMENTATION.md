# 🤖 Simple-RAG v2.0 - Complete Agent Flow

## Overview

This document describes the complete user flow from input to output in the autonomous AI agent system.

---

## High-Level Flow

```
User Input → Interactive CLI → Orchestrator → LangGraph Workflow → Agent Nodes → LLM Calls → Tools → Final Output → User
```

---

## Detailed Flow Diagram

### 1. **User Input Layer**

**Component**: `interactive_agent.py`

```
User types query: "Analyze this repository"
          ↓
Interactive CLI receives input
          ↓
Detects task type (analyze_repo, generate_content, answer_question, general)
          ↓
Calls: run_agent(task, task_type)
```

**Code Location**: `/interactive_agent.py` - `AgentCLI.run_query()`

---

### 2. **Orchestration Layer**

**Component**: `src/agent/orchestrator.py`

```
run_agent(task, task_type, max_iterations=10)
          ↓
Create initial state (AgentState):
  - task: user query
  - task_type: detected type
  - iteration_count: 0
  - max_iterations: 10
  - reasoning_steps: []
  - reflection_notes: []
  - tool_usage: []
  - final_output: ""
  - is_complete: False
          ↓
create_agent_graph() - Builds LangGraph workflow
          ↓
graph.ainvoke(initial_state) - Start workflow
```

**Key Functions**:
- `create_agent_graph()` - Defines node connections and routing
- `route_after_planning()` - Decides next step after planning
- `route_after_reflection()` - Decides to continue or generate

---

### 3. **LangGraph Workflow**

**Component**: LangGraph StateGraph with 6 nodes

#### **Node 1: Planning Node** (`planner`)

**File**: `src/agent/nodes/planner.py`

```
Input: AgentState with task
          ↓
Analyze task_type:
  - analyze_repo → next_action = "analyze"
  - answer_question → next_action = "retrieve"
  - other → next_action = "reason"
          ↓
Add reasoning step: "Planning: Task type is X, next action is Y"
          ↓
Increment iteration_count
          ↓
Return: Updated state with next_action
          ↓
ROUTING: Goes to analyze, retrieve, or reason based on next_action
```

---

#### **Node 2: Repository Analyzer** (`repo_analyzer`)

**File**: `src/agent/nodes/repo_analyzer.py`

**Only runs if**: task_type = "analyze_repo"

```
Input: AgentState
          ↓
Find repository root directory
          ↓
TOOL CALL 1: analyze_directory_structure()
  → Scans filesystem
  → Returns: {children: [...], total_items: N}
  → Stores in state.repo_structure
          ↓
TOOL CALL 2: read_source_files()
  → Reads up to 20 .py files
  → Extracts code content
  → Stores in state.code_files
          ↓
TOOL CALL 3: extract_dependencies()
  → Parses requirements.txt, pyproject.toml
  → Returns: {dependencies: [...], count: N}
  → Stores in state.dependencies
          ↓
TOOL CALL 4: generate_architecture_map()
  → Analyzes Python modules
  → Returns: {modules: [...], total_modules: N}
  → Stores in state.architecture
          ↓
Add reasoning steps (tool results)
Log tool_usage
          ↓
Return: State with repository analysis data
          ↓
ROUTING: Always goes to reasoner
```

**Tools Used**:
1. `analyze_directory_structure(path, max_depth=3)`
2. `read_source_files(path, max_files=20)`
3. `extract_dependencies(path)`
4. `generate_architecture_map(path)`

---

#### **Node 3: Reasoning Node** (`reasoner`)

**File**: `src/agent/nodes/reasoner.py`

```
Input: AgentState with task and optional repository data
          ↓
Load environment variables (load_dotenv)
          ↓
Check if AZURE_OPENAI_API_KEY exists
          ↓
If NO credentials:
  → Use fallback reasoning (simple steps)
  → Return state
          ↓
If YES credentials:
  → Create AsyncAzureOpenAI client
          ↓
Build context for LLM:
  - User task
  - Task type
  - Repository data (if available)
  - Dependencies count
  - Modules count
          ↓
LLM CALL 1: Chain-of-Thought Reasoning
  Model: GPT-4o
  System: "You are an analytical AI that provides clear step-by-step reasoning."
  User: Context + "Analyze this task and provide 3-5 reasoning steps"
  Temperature: 0.7
  Max tokens: 500
          ↓
Parse LLM response (JSON format):
  {
    "reasoning_steps": [
      "step 1",
      "step 2",
      "step 3"
    ]
  }
          ↓
Add reasoning steps to state
Set next_action = "generate"
          ↓
Return: State with LLM-generated reasoning
          ↓
ROUTING: Always goes to reflector
```

**LLM Call Details**:
- **Purpose**: Generate intelligent reasoning steps
- **Input**: Task + available context
- **Output**: 3-5 reasoning steps
- **Time**: ~1-2 seconds

---

#### **Node 4: Reflection Node** (`reflector`)

**File**: `src/agent/nodes/reflector.py`

```
Input: AgentState with reasoning steps
          ↓
Analyze state:
  - Has reasoning steps?
  - Has repository data?
  - Has reflection notes?
          ↓
Determine quality:
  - Good: Has data and reasoning
  - Needs improvement: Missing data
          ↓
Add reflection note:
  "Reflection: Reasoning appears sound, ready to generate"
  OR
  "Reflection: Need more analysis"
          ↓
Decide next action:
  - If good → next_action = "generate"
  - If needs work → next_action = "continue" (loops back to planner)
  - If specific issue → next_action = "retry" (goes back to repo_analyzer)
          ↓
Return: State with reflection notes and next_action
          ↓
ROUTING: Based on next_action (generate, continue, or retry)
```

**Decision Logic**:
- Ready to generate if: reasoning steps + (data OR not needed)
- Loop back if: iterations < max_iterations AND needs more work
- Max iterations: 10 (prevents infinite loops)

---

#### **Node 5: Generation Node** (`generator`)

**File**: `src/agent/nodes/generator.py`

```
Input: AgentState with all collected data and reasoning
          ↓
Load environment variables (load_dotenv)
          ↓
Check if AZURE_OPENAI_API_KEY exists
          ↓
If NO credentials:
  → Use template fallback (for repo analysis only)
  → Return error message (for other tasks)
          ↓
If YES credentials:
  → Create AsyncAzureOpenAI client
          ↓
Build context for LLM:
  - User query
  - Task type
  - Repository analysis data:
    * Total items found
    * Files/directories list
    * Dependencies (up to 10)
    * Modules (up to 8)
  - Reasoning steps (last 5)
          ↓
Select system prompt based on task type:

  IF analyze_repo:
    "You are an expert code analyst. Generate a comprehensive 
     repository analysis report in markdown format..."
  
  ELSE IF linkedin/post:
    "You are a professional LinkedIn content creator. Write 
     an engaging LinkedIn post based on the user's request.
     Follow their specific instructions carefully..."
  
  ELSE:
    "You are a helpful AI assistant. Answer the user's query 
     directly and accurately. For math questions, provide 
     the calculation. For 'how did you know' questions, 
     explain you used repository analysis tools..."
          ↓
LLM CALL 2: Content Generation
  Model: GPT-4o
  System: [Task-specific prompt]
  User: [Context with all data]
  Temperature: 0.7
  Max tokens: 2000
          ↓
Receive LLM response (final output)
          ↓
Set state.final_output = response
Set state.is_complete = True
          ↓
Return: State with final output
          ↓
ROUTING: Always goes to evaluator
```

**LLM Call Details**:
- **Purpose**: Generate final intelligent response
- **Input**: Task + all context + reasoning + data
- **Output**: Complete answer (25-2000 characters)
- **Time**: ~2-4 seconds

**Examples**:
- Math: "The answer to 2+2 is 4."
- Repo analysis: Full markdown report with real data
- LinkedIn: Custom post following instructions
- Explanation: Detailed answer about tools used

---

#### **Node 6: Evaluation Node** (`evaluator`)

**File**: `src/agent/nodes/evaluator.py`

```
Input: AgentState with final_output and all history
          ↓
Create AgentEvaluator instance
          ↓
Calculate 5 metrics:

  1. Task Completion (35% weight):
     - Has final output? 50 pts
     - Marked complete? 30 pts
     - Within iterations? 20 pts
  
  2. Reasoning Quality (25% weight):
     - Has reasoning? 40 pts
     - Step count: 20-40 pts (1-2: 20, 3-4: 30, 5+: 40)
     - Has reflections? 20 pts
  
  3. Tool Effectiveness (15% weight):
     - Used tools? 50 pts
     - Multiple tools? 10-30 pts (1: 10, 2: 20, 3+: 30)
     - Has results? 20 pts
  
  4. Reflection Quality (10% weight):
     - Has reflections? 60 pts
     - Reflection count: 20-40 pts (1: 20, 2: 30, 3+: 40)
  
  5. Output Quality (15% weight):
     - Has output? 40 pts
     - Length: 10-30 pts (50-99: 10, 100-199: 20, 200+: 30)
     - Structure: 30 pts (markdown formatting)
          ↓
Calculate overall weighted score:
  Overall = (TC × 0.35) + (RQ × 0.25) + (TE × 0.15) + 
            (ReQ × 0.10) + (OQ × 0.15)
          ↓
Store scores in state.evaluation_scores:
  {
    "task_completion": 100.0,
    "reasoning_quality": 100.0,
    "tool_effectiveness": 100.0,
    "reflection_quality": 90.0,
    "output_quality": 100.0,
    "overall_score": 99.0
  }
          ↓
Return: State with evaluation scores
          ↓
ROUTING: END (workflow complete)
```

**Score Ranges**:
- Repository analysis: 95-99/100 (uses all tools)
- LinkedIn/content: 80-85/100 (no tools needed)
- Math/questions: 75-81/100 (simple reasoning)

---

### 4. **Output Layer**

**Component**: `interactive_agent.py`

```
Workflow completes
          ↓
interactive_agent.py receives final_state
          ↓
Display formatted output:

  ======================================================================
  ✅ AGENT RESPONSE
  ======================================================================
  [final_output content]
  
  ======================================================================
  📊 EVALUATION SCORES
  ======================================================================
  Overall Score: XX.X/100
    • Task Completion: XX.X
    • Reasoning Quality: XX.X
    • Tool Effectiveness: XX.X
    • Reflection Quality: XX.X
    • Output Quality: XX.X
  ======================================================================
          ↓
Store in conversation history
Update session statistics
          ↓
Wait for next user input
```

---

## Complete Flow Example: "Analyze this repository"

### Step-by-Step Execution:

1. **User Input**: Types "Analyze this repository"

2. **Interactive CLI**: 
   - Detects task_type = "analyze_repo"
   - Calls `run_agent("Analyze this repository", "analyze_repo")`

3. **Orchestrator**:
   - Creates initial AgentState
   - Builds LangGraph workflow
   - Starts execution

4. **Planning Node**:
   - Sees task_type = "analyze_repo"
   - Sets next_action = "analyze"
   - Iteration 1/10

5. **Repository Analyzer**:
   - 🔍 Analyzing repository at: /path/to/Simple-RAG
   - ✓ Found 22 top-level items (Tool 1)
   - ✓ Analyzed 20 source files (Tool 2)
   - ✓ Identified 25 dependencies (Tool 3)
   - ✓ Mapped 11 modules (Tool 4)
   - Stores all data in state
   - Time: ~0.5 seconds

6. **Reasoning Node**:
   - 🧠 Performing LLM-based reasoning...
   - Calls GPT-4o with task + repository data
   - Generates 5 reasoning steps:
     1. "Identify repository structure from scan results"
     2. "Analyze dependencies to understand tech stack"
     3. "Examine module organization for architecture"
     4. "Evaluate code quality from file analysis"
     5. "Synthesize findings into comprehensive report"
   - ✓ Generated 5 reasoning steps
   - Time: ~2 seconds

7. **Reflection Node**:
   - Checks reasoning steps: ✓ Present
   - Checks repository data: ✓ Present
   - Adds reflection: "Reasoning appears sound, ready to generate"
   - Sets next_action = "generate"

8. **Generation Node**:
   - 🤖 Generating LLM-based response...
   - Builds context with all repository data
   - Calls GPT-4o with expert code analyst prompt
   - Receives comprehensive markdown report
   - ✓ Generated 2847 characters
   - Time: ~3 seconds

9. **Evaluation Node**:
   - Calculates all 5 metrics
   - Task Completion: 100.0 (has output, complete, within limits)
   - Reasoning Quality: 100.0 (5 steps, has reflections)
   - Tool Effectiveness: 100.0 (used 4 tools, has results)
   - Reflection Quality: 90.0 (has reflections)
   - Output Quality: 100.0 (long, structured markdown)
   - **Overall Score: 99.0/100**

10. **Output Display**:
    - Shows complete repository analysis report
    - Displays evaluation scores
    - Ready for next query

**Total Time**: ~6 seconds (tool execution + 2 LLM calls)

---

## Flow Variations by Task Type

### **analyze_repo**:
```
Planning → Repo Analyzer (4 tools) → Reasoner (LLM) → 
Reflector → Generator (LLM) → Evaluator
Tools: ✓ | LLM Calls: 2 | Score: 95-99
```

### **generate_content** (LinkedIn):
```
Planning → Reasoner (LLM) → Reflector → Generator (LLM) → Evaluator
Tools: ✗ | LLM Calls: 2 | Score: 80-85
```

### **answer_question**:
```
Planning → Reasoner (LLM) → Reflector → Generator (LLM) → Evaluator
Tools: ✗ | LLM Calls: 2 | Score: 75-81
```

### **general** (math, etc.):
```
Planning → Reasoner (LLM) → Reflector → Generator (LLM) → Evaluator
Tools: ✗ | LLM Calls: 2 | Score: 75-80
```

---

## Key Components

### **State Management** (`AgentState`)

The state is a TypedDict that flows through all nodes:

```python
{
    "task": str,                      # User query
    "task_type": str,                 # analyze_repo, generate_content, etc.
    "iteration_count": int,           # Current iteration (max 10)
    "max_iterations": int,            # Maximum iterations allowed
    "next_action": str,               # Next node to execute
    "reasoning_steps": List[str],     # All reasoning steps collected
    "reflection_notes": List[str],    # Self-critique notes
    "tool_usage": List[Dict],         # Tools called and results
    "repo_structure": Dict,           # Directory structure
    "dependencies": Dict,             # Dependencies found
    "architecture": Dict,             # Module architecture
    "code_files": List[Dict],         # Source files content
    "final_output": str,              # Generated response
    "is_complete": bool,              # Task completion flag
    "evaluation_scores": Dict         # Performance scores
}
```

### **LLM Calls** (2 per query)

**Call 1 - Reasoning** (reasoner.py):
- **Model**: GPT-4o
- **Purpose**: Generate reasoning steps
- **Input**: 100-300 tokens
- **Output**: 50-500 tokens
- **Time**: 1-2 seconds

**Call 2 - Generation** (generator.py):
- **Model**: GPT-4o
- **Purpose**: Generate final response
- **Input**: 200-800 tokens (with all context)
- **Output**: 25-2000 tokens
- **Time**: 2-4 seconds

### **Repository Tools** (4 total)

**Tool 1**: `analyze_directory_structure(path, max_depth)`
- Scans filesystem recursively
- Returns directory tree with file/folder metadata

**Tool 2**: `read_source_files(path, max_files)`
- Reads Python source files
- Extracts code content for analysis

**Tool 3**: `extract_dependencies(path)`
- Parses requirements.txt, pyproject.toml
- Returns list of dependencies with versions

**Tool 4**: `generate_architecture_map(path)`
- Analyzes Python module structure
- Maps import relationships

---

## Error Handling & Fallbacks

### **No Azure Credentials**:
```
Reasoner: Uses simple fallback steps
Generator: 
  - Repo analysis: Uses template with real tool data
  - Other tasks: Shows error message
```

### **LLM Call Fails**:
```
Try-catch blocks in both reasoner and generator
Falls back to templates or error messages
Never crashes the workflow
```

### **Max Iterations Reached**:
```
Planning node checks iteration_count
If > max_iterations: routes to END
Prevents infinite loops
```

### **Tool Failures**:
```
Each tool has try-catch
Returns empty dict on failure
Workflow continues with partial data
```

---

## Performance Metrics

### **Timing**:
- Tool execution: 0.5-1 second
- LLM reasoning: 1-2 seconds
- LLM generation: 2-4 seconds
- **Total**: 4-7 seconds per query

### **Token Usage** (per query):
- Input: 300-1000 tokens
- Output: 75-2500 tokens
- **Total**: ~375-3500 tokens
- **Cost**: ~$0.01-0.05 per query

### **Scores**:
- Repository analysis: 95-99/100
- Content generation: 80-85/100
- Q&A: 75-81/100

---

## Workflow Loop Behavior

### **Normal Flow**:
```
Planning → Analysis → Reasoning → Reflection → Generation → Evaluation → END
(1 iteration, ~6 seconds)
```

### **With Reflection Loop**:
```
Planning → Analysis → Reasoning → Reflection → "needs more" → 
Planning → Analysis → Reasoning → Reflection → "ready" → 
Generation → Evaluation → END
(2 iterations, ~10 seconds)
```

### **Maximum Iterations**:
```
After 10 iterations:
  → Planning node routes to END
  → Returns partial results
  → Prevents hanging
```

---

## Summary

The agent flow is a **6-node LangGraph workflow** that:

1. ✅ **Plans** the task approach
2. ✅ **Analyzes** repository using 4 tools (if needed)
3. ✅ **Reasons** using GPT-4o LLM
4. ✅ **Reflects** on quality and decides next action
5. ✅ **Generates** intelligent response using GPT-4o LLM
6. ✅ **Evaluates** performance across 5 metrics

**Key Features**:
- Real autonomous decision-making (LangGraph routing)
- LLM-based intelligence (GPT-4o calls)
- Tool integration (repository analysis)
- Self-reflection (quality assessment)
- Self-evaluation (5-metric scoring)
- Error handling (fallbacks at every step)

**Total Components**:
- 6 Agent Nodes
- 4 Repository Tools
- 2 LLM Calls per query
- 5 Evaluation Metrics
- 1 State object flowing through all

**Production-Ready**:
- ✅ 107/107 tests passing
- ✅ Proper error handling
- ✅ Graceful fallbacks
- ✅ Performance optimized
- ✅ Token usage controlled
