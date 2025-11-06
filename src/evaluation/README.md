# Evaluation Module

This module implements a transparent, 5-metric evaluation framework for assessing agent performance.

## Overview

The evaluation system provides:
- **5 weighted metrics** covering all aspects of agent performance
- **Transparent explanations** for each score
- **Evidence-based assessments** with concrete examples
- **Fallback logic** when evaluation fails

## Metrics Framework

### 1. **Task Completion (35%)**
*Did the agent accomplish the requested task?*

**Scoring Criteria:**
- 0-25: Task not completed, missing key elements
- 26-50: Partial completion, significant gaps
- 51-75: Mostly complete, minor issues
- 76-100: Fully complete, exceeds expectations

**Explanation includes:**
- What was requested vs what was delivered
- Missing elements (if any)
- Quality of deliverables

### 2. **Reasoning Quality (25%)**
*How thorough and logical was the chain-of-thought reasoning?*

**Scoring Criteria:**
- 0-25: Superficial or illogical reasoning
- 26-50: Basic reasoning, lacks depth
- 51-75: Solid reasoning with minor gaps
- 76-100: Deep, logical, comprehensive reasoning

**Explanation includes:**
- Number of reasoning steps taken
- Depth of analysis
- Logical coherence
- Evidence of critical thinking

### 3. **Tool Effectiveness (15%)**
*How well did the agent use available tools?*

**Scoring Criteria:**
- 0-25: Poor tool selection, misuse
- 26-50: Basic tool use, missed opportunities
- 51-75: Good tool selection and usage
- 76-100: Excellent, strategic tool usage

**Explanation includes:**
- Tools used and why
- Appropriateness of tool selection
- Missing tool opportunities
- Evidence gathering quality

### 4. **Reflection Quality (10%)**
*How effective was the self-critique and improvement process?*

**Scoring Criteria:**
- 0-25: No reflection or superficial
- 26-50: Basic reflection, limited insight
- 51-75: Good self-assessment, identifies issues
- 76-100: Deep self-critique, triggers improvements

**Explanation includes:**
- Self-assessment quality
- Issues identified
- Improvements made (BEFORE/AFTER comparison)
- Impact on final output

### 5. **Output Quality (15%)**
*How well-structured, clear, and useful was the final output?*

**Scoring Criteria:**
- 0-25: Poorly structured, unclear
- 26-50: Basic structure, lacks clarity
- 51-75: Well-structured, mostly clear
- 76-100: Excellent structure, highly clear

**Explanation includes:**
- Structure and organization
- Clarity and readability
- Completeness
- Usefulness for intended audience

## Weighted Scoring

```
Overall Score =
    (Task Completion × 0.35) +
    (Reasoning Quality × 0.25) +
    (Tool Effectiveness × 0.15) +
    (Reflection Quality × 0.10) +
    (Output Quality × 0.15)
```

## Implementation

### Main Functions

#### `evaluation_node(state: AgentState) -> AgentState`
Main evaluation node in LangGraph workflow:
- Computes all 5 metrics
- Generates transparent explanations
- Updates state with scores and explanations
- Always runs (cannot be skipped)

#### `compute_evaluation_metrics(state: AgentState) -> Dict[str, float]`
Computes numeric scores for all 5 metrics:
```python
scores = compute_evaluation_metrics(state)
# Returns: {
#   "task_completion": 85.0,
#   "reasoning_quality": 75.0,
#   "tool_effectiveness": 80.0,
#   "reflection_quality": 70.0,
#   "output_quality": 90.0,
#   "overall": 80.5
# }
```

#### `generate_evaluation_explanations(state: AgentState, scores: Dict) -> Dict[str, List[str]]`
Generates transparent explanations for each score:
```python
explanations = generate_evaluation_explanations(state, scores)
# Returns: {
#   "task_completion": [
#       "✅ Fully completed repository analysis (100%)",
#       "✅ Included all required sections",
#       "Recommendation: Add more examples"
#   ],
#   ...
# }
```

## Usage Example

```python
from src.agent.orchestrator import run_agent

# Run agent (evaluation happens automatically)
result = await run_agent(
    task="Analyze this repository",
    task_type="analyze_repo"
)

# Access evaluation results
scores = result["evaluation_scores"]
explanations = result["evaluation_explanations"]

print(f"Overall Score: {scores['overall']}/100")
print("\nTask Completion:")
for exp in explanations["task_completion"]:
    print(f"  {exp}")

print("\nReasoning Quality:")
for exp in explanations["reasoning_quality"]:
    print(f"  {exp}")
```

## Transparency Features

### 1. **Evidence-Based Scoring**
All scores backed by concrete evidence:
- Counts of reasoning steps, tool calls, reflection notes
- Presence/absence of required elements
- Concrete code references and metrics

### 2. **Detailed Explanations**
Each metric provides:
- ✅ What was done well
- ⚠️ What could be improved
- 💡 Specific recommendations
- 📊 Quantitative evidence (counts, percentages)

### 3. **BEFORE/AFTER Proof**
When reflection triggers improvements:
- Stores original output in `output_before_reflection`
- Generates improved output in `final_output`
- Evaluation can compare both to prove authentic self-correction

### 4. **Fallback Logic**
If evaluation fails (API error, rate limit):
- Uses template-based scoring
- Provides default explanations
- Ensures agent always completes

## Testing

See `tests/test_evaluation/` for comprehensive tests:
- `test_evaluator.py`: Evaluator node tests
- `test_metrics.py`: Individual metric tests
- `test_explanations.py`: Explanation generation tests

## Configuration

Metric weights can be adjusted in `src/evaluation/metrics.py`:
```python
METRIC_WEIGHTS = {
    "task_completion": 0.35,      # 35%
    "reasoning_quality": 0.25,    # 25%
    "tool_effectiveness": 0.15,   # 15%
    "reflection_quality": 0.10,   # 10%
    "output_quality": 0.15        # 15%
}
```
