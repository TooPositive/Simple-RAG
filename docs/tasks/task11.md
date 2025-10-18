Of course. The prompt is ready. The final piece of the core RAG pipeline is to send this prompt to a powerful Large Language Model (LLM) to generate the final, context-aware answer.

-----

### **Spec Task `RAG-3`: Answer Generation**

#### **🎯 Objective**

To implement a function that takes the fully formatted prompt, sends it to an Azure OpenAI Chat Completions model (like GPT-4), and cleanly extracts the generated answer text from the API response.

#### **🔑 Key Components & Rationale**

  * **`AzureOpenAI` Chat Client:** We will use the `client.chat.completions.create` method from the `openai` library. This is the standard way to interact with generative models like GPT-3.5-Turbo and GPT-4.
  * **Configuration-driven Model Selection:** The specific model to be used (e.g., `gpt-4`) will be pulled from our `src/config.py` settings file. This makes it easy to switch models later without changing the core code.
  * **Robust API Mocking:** As with previous API interactions, testing this function requires a precise mock. We will simulate the complex nested object that the Azure OpenAI API returns for a chat completion. This ensures our function can correctly navigate the response structure (`response.choices[0].message.content`) to find the answer, all without making a real network call.

#### **✅ Acceptance Criteria**

1.  A new function `generate_llm_answer(prompt: str) -> str` is added to `src/chatbot.py`.
2.  The function initializes the `AzureOpenAI` client using credentials from `src/config.py`.
3.  It sends the provided prompt to the chat completions endpoint.
4.  It correctly parses the API response and returns the generated text content as a string.
5.  A new test, `test_answer_generation`, is added to `tests/test_chatbot.py`.
6.  The test **mocks** the `client.chat.completions.create` method to return a simulated API response object.
7.  The test asserts that the function returns the exact string contained within the mock response's content field.

#### **📝 Detailed Steps**

1.  **Implement the Answer Generation Function:**

      * Append the following function to your `src/chatbot.py` file.

    <!-- end list -->

    ```python
    # src/chatbot.py (append to existing file)

    # ... (keep existing imports and functions)

    def generate_llm_answer(prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the generated answer.

        Args:
            prompt: The fully formatted prompt containing the user query and context.

        Returns:
            The text of the LLM's generated answer.
        """
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.openai_api_version,
        )

        try:
            response = client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7, # Adjust for more or less creative answers
            )
            # Extract the content from the response
            answer = response.choices[0].message.content
            return answer.strip() if answer else ""
        except Exception as e:
            print(f"An error occurred during LLM answer generation: {e}")
            return "Sorry, I encountered an error while generating an answer."

    ```

2.  **Implement the Unit Test (TDD):**

      * Append the following test to your `tests/test_chatbot.py` file.

    <!-- end list -->

    ```python
    # tests/test_chatbot.py (append to existing file)
    from src.chatbot import generate_llm_answer

    # ... (keep existing imports and tests)

    def test_answer_generation(mocker):
        """
        Tests that the LLM answer generation function correctly processes a
        mocked API response.
        """
        # 1. Setup: A sample prompt
        sample_prompt = "QUESTION: What is RAG? CONTEXT: ..."

        # 2. Mocking: Create a mock object that mimics the nested structure
        #    of the real OpenAI API response.
        mock_message = MagicMock()
        mock_message.content = "This is the mocked LLM answer."
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_api_response = MagicMock()
        mock_api_response.choices = [mock_choice]

        # Patch the client and its method call
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_api_response
        mocker.patch("src.chatbot.AzureOpenAI", return_value=mock_client_instance)

        # 3. Call the function under test
        answer = generate_llm_answer(sample_prompt)

        # 4. Assertions
        # Check that the API was called with the correct model and messages
        mock_client_instance.chat.completions.create.assert_called_once()
        call_args, call_kwargs = mock_client_instance.chat.completions.create.call_args
        assert call_kwargs["model"] == settings.llm_model_name
        assert call_kwargs["messages"][-1]["content"] == sample_prompt

        # Check that the function returned the correct text
        assert answer == "This is the mocked LLM answer."
    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This confirms that all individual components of your RAG pipeline—retrieval, prompt formatting, and generation—are fully implemented and correctly tested.