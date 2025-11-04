#!/bin/bash
# Test the full agent with auto-input

source .venv/bin/activate

echo "Testing: What are embeddings?"
echo "What are embeddings?" | python interactive_agent.py --verbose

echo ""
echo "========================================="
echo "Test complete! Check output above."
