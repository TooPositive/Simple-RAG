Great, we have retrieved the relevant context. Now, we need to package this context along with the user's original question into a clear set of instructions for the Large Language Model. This is the prompt engineering step.

-----

### **Spec Task `RAG-2`: Prompt Formatting**

#### **🎯 Objective**

To implement a pure function that takes the user's query and the list of retrieved context strings and combines them into a single, well-structured prompt. This prompt will instruct the LLM on how to generate an answer based *only* on the provided information.

#### **🔑 Key Components & Rationale**

  * **Prompt Template:** A carefully crafted string template is the core of this task. It sets the rules for the LLM. By explicitly telling the model to "Answer... based ONLY on the provided context" and to state when the information isn't present, we significantly reduce the risk of the model hallucinating or using its general knowledge.
  * **Clear Delimiters:** Using separators like `---CONTEXT---` makes the prompt easily parsable for the LLM, clearly distinguishing instructions from the data it needs to work with.
  * **Pure Function:** This function will have no side effects (like API calls). It will always produce the same output for the same input, making it extremely easy and fast to test.

#### **✅ Acceptance Criteria**

1.  A new function `format_prompt(query: str, context: list[str]) -> str` is added to `src/chatbot.py`.
2.  The function combines the query and context into a single string using a predefined template.
3.  A new test, `test_prompt_formatting`, is added to `tests/test_chatbot.py`.
4.  The test calls the function with sample data and asserts that the resulting string contains all the expected components in the correct structure.

#### **📝 Detailed Steps**

1.  **Implement the Prompt Formatting Function:**

      * Append the following function to your `src/chatbot.py` file.

    <!-- end list -->

    ```python
    # src/chatbot.py (append to existing file)

    # ... (keep existing imports and functions)

    def format_prompt(query: str, context: List[str]) -> str:
        """
        Formats the user query and retrieved context into a single prompt for the LLM.

        Args:
            query: The user's question.
            context: A list of relevant context strings retrieved from the database.

        Returns:
            A formatted prompt string.
        """
        # Join the context strings into a single block
        context_str = "\n\n---\n\n".join(context)
        
        # The prompt template
        prompt = f"""
    ```

You are a helpful AI assistant for the 'Databases for GenAI' lecture.
Answer the following question based ONLY on the provided context.
If the answer is not in the context, reply with "I don't have enough information in the provided context to answer this question."
Do not use any prior knowledge.

\---CONTEXT---
{context\_str}
\---END CONTEXT---

QUESTION: {query}
ANSWER:
"""
return prompt

````
```
````

2.  **Implement the Unit Test (TDD):**

      * Append the following test to your `tests/test_chatbot.py` file.

    <!-- end list -->

    ```python
    # tests/test_chatbot.py (append to existing file)
    from src.chatbot import format_prompt

    # ... (keep existing imports and test_retrieval)

    def test_prompt_formatting():
        """
        Tests that the prompt is formatted correctly with the query and context.
        """
        # 1. Setup: Define a sample query and context
        query = "What is RAG?"
        context = [
            "Retrieval-Augmented Generation (RAG) is a technique.",
            "It combines retrieval with a generative model."
        ]

        # 2. Call the function under test
        prompt = format_prompt(query, context)

        # 3. Assertions
        assert isinstance(prompt, str)
        
        # Check that the core instructions are present
        assert "based ONLY on the provided context" in prompt
        
        # Check that the query is in the prompt
        assert f"QUESTION: {query}" in prompt
        
        # Check that all context items are present
        assert "Retrieval-Augmented Generation (RAG) is a technique." in prompt
        assert "It combines retrieval with a generative model." in prompt
        
        # Check that the delimiters are present
        assert "---CONTEXT---" in prompt
        assert "---END CONTEXT---" in prompt
    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This verifies that your application can correctly construct the final prompt that will be sent to the LLM.