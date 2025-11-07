"""
Quick verification test for refactored generator.

This script tests that the refactored generator works correctly.
"""

import asyncio
import sys
from src.agent.state import create_initial_state
from src.agent.nodes.generator import generation_node, ContentGenerator
from src.agent.nodes.config import GeneratorConfig
from src.agent.nodes.llm_client import MockLLMClient


async def test_backward_compatibility():
    """Test that generation_node still works (backward compatibility)."""
    print("🔍 Testing backward compatibility...")

    state = create_initial_state("Test task", "test")
    state["reasoning_steps"] = ["Step 1", "Step 2"]

    result = await generation_node(state)

    assert result["final_output"] is not None, "No output generated"
    assert len(result["final_output"]) > 0, "Empty output"
    assert result["is_complete"] is True, "Task not marked complete"

    print("✅ Backward compatibility test PASSED")
    return True


async def test_content_generator_with_mock():
    """Test ContentGenerator with mock LLM client."""
    print("\n🔍 Testing ContentGenerator with mock LLM...")

    mock_llm = MockLLMClient(mock_response="Mock test response from LLM")
    config = GeneratorConfig()

    generator = ContentGenerator(
        config=config,
        llm_client=mock_llm
    )

    state = create_initial_state("Analyze repository", "analyze_repo")
    state["repo_structure"] = {"files": 10}

    output = await generator.generate(state, include_reflection=False)

    assert output is not None, "No output generated"
    assert len(output) > 0, "Empty output"
    assert "Mock test response" in output, "Mock response not used"

    print("✅ ContentGenerator with mock LLM test PASSED")
    return True


async def test_fallback_generator():
    """Test fallback generator when LLM is unavailable."""
    print("\n🔍 Testing fallback generator...")

    # Create generator without valid LLM credentials (will use fallback)
    config = GeneratorConfig()

    # Create generator that will use fallback
    generator = ContentGenerator(config=config, llm_client=None)

    state = create_initial_state("Analyze repository", "analyze_repo")
    state["repo_structure"] = {
        "children": [
            {"name": "file1.py", "type": "file"},
            {"name": "file2.py", "type": "file"}
        ]
    }
    state["dependencies"] = {
        "dependencies": [
            {"name": "pytest"},
            {"name": "langchain"}
        ]
    }

    output = await generator.generate(state, include_reflection=False)

    assert output is not None, "No fallback output generated"
    assert len(output) > 0, "Empty fallback output"
    assert "Repository" in output or "repository" in output.lower(), "Not a repository analysis"

    print("✅ Fallback generator test PASSED")
    return True


async def test_config_customization():
    """Test that config can be customized for different projects."""
    print("\n🔍 Testing config customization...")

    config = GeneratorConfig()
    config.update_project_metadata(
        project_name="Custom Project",
        organization="Custom Organization",
        key_technologies=["Tech1", "Tech2"],
        system_capabilities=["Capability1", "Capability2"]
    )

    assert config.project.project_name == "Custom Project"
    assert config.project.organization == "Custom Organization"
    assert "Tech1" in config.project.key_technologies

    mock_llm = MockLLMClient(mock_response="Custom project response")
    generator = ContentGenerator(config=config, llm_client=mock_llm)

    state = create_initial_state("Test", "general")
    output = await generator.generate(state)

    assert output is not None, "No output with custom config"

    print("✅ Config customization test PASSED")
    return True


async def test_all_task_types():
    """Test different task types."""
    print("\n🔍 Testing different task types...")

    mock_llm = MockLLMClient(mock_response="Task type test response")
    generator = ContentGenerator(llm_client=mock_llm)

    task_types = ["general", "analyze_repo", "linkedin_post", "explain"]

    for task_type in task_types:
        state = create_initial_state(f"Test {task_type}", task_type)
        output = await generator.generate(state)
        assert output is not None, f"No output for {task_type}"
        print(f"  ✓ {task_type} task type works")

    print("✅ All task types test PASSED")
    return True


async def main():
    """Run all tests."""
    print("="*70)
    print("🧪 REFACTORED GENERATOR VERIFICATION TESTS")
    print("="*70)

    tests = [
        test_backward_compatibility,
        test_content_generator_with_mock,
        test_fallback_generator,
        test_config_customization,
        test_all_task_types
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test FAILED: {test_func.__name__}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("="*70)

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Refactored generator is working correctly.")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
