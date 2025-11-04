#!/usr/bin/env python3
"""
Interactive CLI for Simple-RAG v2.0 Agent
Live conversation interface for demos and testing
"""

import asyncio
import sys
from src.agent.orchestrator import run_agent


class AgentCLI:
    """Interactive command-line interface for the agent."""
    
    def __init__(self):
        self.conversation_history = []
        self.session_count = 0
        self.last_task_type = None
        self.repo_context_active = False
        self.last_repo_data = None
    
    def print_header(self):
        """Print welcome header."""
        print("\n" + "="*70)
        print("🤖 Simple-RAG v2.0 - Interactive Agent CLI")
        print("   Autonomous AI Agent with Self-Reflection")
        print("="*70)
        print("\n💡 Tips:")
        print("   - Ask the agent to analyze this repository")
        print("   - Request explanations of the codebase")
        print("   - Generate content or LinkedIn posts")
        print("   - Ask about specific components")
        print("\n📝 Commands:")
        print("   - Type 'exit' or 'quit' to end session")
        print("   - Type 'clear' to clear screen")
        print("   - Type 'history' to see conversation history")
        print("   - Type 'stats' to see session statistics")
        print("="*70 + "\n")
    
    def print_separator(self):
        """Print a visual separator."""
        print("\n" + "-"*70 + "\n")
    
    async def run_query(self, query: str, task_type: str = "general"):
        """Run a single query through the agent."""
        print("\n🤖 Agent: Thinking...\n")
        
        try:
            # Pass cached repo data for all repo-related queries
            # This prevents re-running expensive analysis
            previous_data = None
            if self.last_repo_data and task_type in ["analyze_repo", "generate_content", "general"]:
                # Pass cache for ANY query that might benefit from repo context
                previous_data = self.last_repo_data
            
            result = await run_agent(
                task=query, 
                task_type=task_type,
                previous_repo_data=previous_data
            )
            
            # Update context tracking
            if task_type == "analyze_repo":
                self.repo_context_active = True
                self.last_repo_data = {
                    'repo_structure': result.get('repo_structure'),
                    'dependencies': result.get('dependencies'),
                    'architecture': result.get('architecture'),
                    'code_files': result.get('code_files'),
                    'code_symbols': result.get('code_symbols'),
                    'verification_outputs': result.get('verification_outputs')
                }
            
            self.last_task_type = task_type
            
            # Store in history
            self.conversation_history.append({
                'query': query,
                'result': result,
                'session': self.session_count,
                'task_type': task_type
            })
            self.session_count += 1
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def display_result(self, result: dict, verbose: bool = False):
        """Display agent result in a clean format."""
        if not result:
            return
        
        # Show the final output
        print("\n" + "="*70)
        print("✅ AGENT RESPONSE")
        print("="*70)
        print(result['final_output'])
        
        # Enhanced Reasoning & Reflection section showing agent's thinking process
        if result.get('reasoning_steps') or result.get('reflection_notes'):
            print("\n" + "="*70)
            print("🧠 AGENT REASONING & SELF-REFLECTION PROCESS")
            print("="*70)
            print("\nThis demonstrates the Capstone 'Reasoning & Reflection' requirement:")
            print("The agent thinks through its approach, then reflects on its output.\n")
            
            # Show reasoning steps (what the agent planned to do)
            all_reasoning = [s for s in result.get('reasoning_steps', []) if s.startswith('Reasoning:')]
            unique_reasoning = list(dict.fromkeys(all_reasoning))  # Deduplicate
            
            if unique_reasoning:
                print("📋 Reasoning Steps (Agent's Approach):")
                for i, step in enumerate(unique_reasoning[-5:], 1):  # Show last 5
                    # Clean up the step text
                    step_text = step.replace('Reasoning: ', '').strip()
                    print(f"  {i}. {step_text}")
            
            # Show reflection decisions (agent critiquing its own output)
            reflection_notes = result.get('reflection_notes', [])
            reflection_decisions = [n for n in reflection_notes if 'Reflection Decision:' in n or 'Self-Critique:' in n]
            unique_reflections = list(dict.fromkeys(reflection_decisions))  # Deduplicate
            
            if unique_reflections:
                print("\n🔍 Self-Reflection Decisions (Agent Evaluating Its Own Output):")
                for i, note in enumerate(unique_reflections, 1):
                    # Extract the key parts
                    note_text = note.replace('Reflection Decision: ', '').replace('Self-Critique: ', '').strip()
                    print(f"  {i}. {note_text}")
            
            # Show what action the agent decided to take
            next_action = result.get('next_action', 'end')
            reflection_assessment = result.get('reflection_assessment', 'good')
            
            if reflection_assessment and reflection_assessment != 'good':
                print(f"\n💡 Agent Decision: {reflection_assessment} → {next_action}")
                print("   (This shows the agent can self-correct and request improvements!)")
            else:
                print(f"\n✅ Agent Decision: Output quality is good, proceeding to evaluation")
            
            if verbose:
                # In verbose mode, show ALL steps (but deduplicate consecutive duplicates)
                print("\n" + "-"*70)
                print("Full Reasoning History:")
                
                # Deduplicate consecutive identical steps (LangGraph may cause duplicates)
                deduped_steps = []
                prev_step = None
                for step in result['reasoning_steps']:
                    if step != prev_step:
                        deduped_steps.append(step)
                        prev_step = step
                
                for i, step in enumerate(deduped_steps, 1):
                    print(f"{i}. {step}")
                
                # Show count of duplicates removed if any
                removed_count = len(result['reasoning_steps']) - len(deduped_steps)
                if removed_count > 0:
                    print(f"\n💡 Note: Removed {removed_count} consecutive duplicate steps for clarity")
        
        print("\n" + "="*70)
        print("📊 EVALUATION SCORES")
        print("="*70)
        scores = result['evaluation_scores']
        print(f"Overall Score: {scores['overall_score']:.1f}/100")
        print(f"  • Task Completion: {scores['task_completion']:.1f}")
        print(f"  • Reasoning Quality: {scores['reasoning_quality']:.1f}")
        print(f"  • Tool Effectiveness: {scores['tool_effectiveness']:.1f}")
        print(f"  • Reflection Quality: {scores['reflection_quality']:.1f}")
        print(f"  • Output Quality: {scores['output_quality']:.1f}")
        
        # Show evaluation explanations if available
        if result.get('evaluation_explanations'):
            print("\n" + "-"*70)
            print("📋 WHY THESE SCORES?")
            print("-"*70)
            
            explanations = result['evaluation_explanations']
            
            # Show explanations for high-scoring metrics (helps understand quality)
            if scores.get('output_quality', 0) >= 90:
                print("\n✨ Output Quality ({}/ 100):".format(scores['output_quality']))
                for line in explanations.get('output_quality', [])[:15]:  # Limit lines
                    print(f"  {line}")
            
            if scores.get('reflection_quality', 0) >= 80:
                print("\n✨ Reflection Quality ({}/100):".format(scores['reflection_quality']))
                for line in explanations.get('reflection_quality', []):
                    print(f"  {line}")
            
            if scores.get('tool_effectiveness', 0) >= 90:
                print("\n✨ Tool Effectiveness ({}/100):".format(scores['tool_effectiveness']))
                for line in explanations.get('tool_effectiveness', []):
                    print(f"  {line}")
        
        print("="*70 + "\n")
    
    def show_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("📝 No conversation history yet.\n")
            return
        
        print("\n" + "="*70)
        print("📜 CONVERSATION HISTORY")
        print("="*70)
        for i, entry in enumerate(self.conversation_history, 1):
            score = entry['result']['evaluation_scores']['overall_score']
            print(f"\n{i}. Query: {entry['query'][:60]}...")
            print(f"   Score: {score:.1f}/100")
        print("="*70 + "\n")
    
    def show_stats(self):
        """Display session statistics."""
        if not self.conversation_history:
            print("📊 No statistics yet.\n")
            return
        
        scores = [e['result']['evaluation_scores']['overall_score'] 
                  for e in self.conversation_history]
        avg_score = sum(scores) / len(scores)
        
        print("\n" + "="*70)
        print("📊 SESSION STATISTICS")
        print("="*70)
        print(f"Total Queries: {len(self.conversation_history)}")
        print(f"Average Score: {avg_score:.1f}/100")
        print(f"Highest Score: {max(scores):.1f}/100")
        print(f"Lowest Score: {min(scores):.1f}/100")
        print("="*70 + "\n")
    
    async def interactive_loop(self, verbose: bool = False):
        """Main interactive loop."""
        self.print_header()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye! Thanks for using Simple-RAG v2.0!\n")
                    break
                
                elif user_input.lower() == 'clear':
                    print("\033[2J\033[H")  # Clear screen
                    self.print_header()
                    continue
                
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                
                elif user_input.lower() == 'help':
                    self.print_header()
                    continue
                
                # Determine task type from query
                task_type = self._detect_task_type(user_input)
                
                # Run query
                result = await self.run_query(user_input, task_type)
                
                # Display result
                if result:
                    self.display_result(result, verbose=verbose)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using Simple-RAG v2.0!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Thanks for using Simple-RAG v2.0!\n")
                break
    
    def _detect_task_type(self, query: str) -> str:
        """Detect task type from query with context awareness."""
        query_lower = query.lower()
        
        # PRIORITY 1: LinkedIn/content generation (check FIRST before context!)
        # This prevents repo context from overriding explicit content generation requests
        linkedin_keywords = ['linkedin', 'post', 'write', 'generate', 'create']
        if any(keyword in query_lower for keyword in linkedin_keywords):
            # Clear repo context if generating content ABOUT the repo
            if 'about' in query_lower or 'this' in query_lower:
                print("  💡 LinkedIn post about repository - will use cached data")
            return "generate_content"
        
        # PRIORITY 2: Check for explicit repository-related queries
        # Include code-specific questions that MUST analyze the codebase
        repo_keywords = [
            # General repo analysis
            'analyze', 'repository', 'repo', 'codebase', 'structure', 'files', 
            'what is this', 'about this', 'this project', 'this code',
            # Code-specific questions (CRITICAL - must trigger repo analysis!)
            'where', 'which file', 'which class', 'which function', 'how is', 'show me',
            'find', 'locate', 'used in', 'in which', 'implemented in', 'imported',
            'defined in', 'code for', 'source of', 'implementation'
        ]
        if any(keyword in query_lower for keyword in repo_keywords):
            return "analyze_repo"
        
        # PRIORITY 3: Check if this is a follow-up question about the repository
        # Look for context clues that suggest continuing repository discussion
        repo_followup_keywords = ['classes', 'functions', 'modules', 'components', 'architecture',
                                 'how they connect', 'dependencies', 'imports', 'structure',
                                 'main files', 'key files', 'implementation', 'design']
        
        if self.repo_context_active and any(keyword in query_lower for keyword in repo_followup_keywords):
            print("  💡 Detected follow-up question about repository (context-aware)")
            return "analyze_repo"
        
        # PRIORITY 4: Check for demonstrative pronouns that might refer to previous context
        if self.repo_context_active and any(word in query_lower for word in ['it', 'them', 'these', 'those', 'mention', 'list', 'show']):
            # If we just talked about the repo and user says "mention X" or "list Y", likely about repo
            if any(word in query_lower for word in ['mention', 'list', 'show', 'tell me', 'what are']):
                print("  💡 Detected contextual follow-up (using previous repository context)")
                return "analyze_repo"
        
        # PRIORITY 5: AI/ML/Embeddings questions (RAG retrieval)
        # These questions should query the ChromaDB knowledge base
        ai_keywords = [
            'embedding', 'embeddings', 'vector', 'vectors', 
            'ai', 'artificial intelligence', 'machine learning', 'ml', 
            'llm', 'large language model', 'gpt', 'openai',
            'rag', 'retrieval', 'semantic search', 
            'neural network', 'transformer', 'attention',
            'fine-tuning', 'prompt engineering', 'tokenization',
            'chromadb', 'vector database', 'similarity'
        ]
        if any(keyword in query_lower for keyword in ai_keywords):
            return "answer_question"
        
        # PRIORITY 6: Explanations about the agent itself
        if any(word in query_lower for word in ['how do you', 'how did you', 'your evaluation', 'your framework', 'who are you']):
            return "answer_question"
        
        # PRIORITY 7: Math and simple questions
        return "general"


async def main():
    """Main entry point."""
    # Parse arguments
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    # Create and run CLI
    cli = AgentCLI()
    await cli.interactive_loop(verbose=verbose)


if __name__ == "__main__":
    print("\n🚀 Starting Simple-RAG v2.0 Interactive Agent...\n")
    asyncio.run(main())
