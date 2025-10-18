Of course. All the individual components are now built and tested. The next step is to assemble them into a single, cohesive class that orchestrates the entire RAG pipeline from a user's question to a final answer.

-----

### **Spec Task `APP-1`: Full RAG Pipeline Orchestrator**

#### **🎯 Objective**

To create a high-level `RAGChatbot` class that encapsulates the entire RAG workflow. This class will handle the one-time data ingestion and provide a simple `ask` method, making the chatbot easy to use in any application.

#### **🔑 Key Components & Rationale**

  * **`RAGChatbot` Class:** Using a class allows us to manage state, such as the connection to the vector database, cleanly. The `__init__` method is the perfect place to set up the database and perform the initial data loading and indexing, which only needs to happen once.
  * **Data Ingestion Logic:** The class will check if the vector database is empty. If it is, it will automatically run the full data pipeline: load files, chunk the text, and store the embeddings. This makes the chatbot self-sufficient on its first run.
  * **`ask` Method:** This public method provides a simple interface to the complex RAG process. A user of this class only needs to call `chatbot.ask("their question")` without needing to know about retrieval, prompting, or generation.
  * **Integration Testing:** We will write a test that verifies the `ask` method calls the underlying functions in the correct sequence. This test focuses on the *orchestration* rather than the logic of the individual functions, which are already covered by unit tests.

#### **✅ Acceptance Criteria**

1.  A new class `RAGChatbot` is created in `src/chatbot.py`.
2.  The `__init__` method initializes the vector database and runs the full data ingestion pipeline if the database is empty.
3.  A public method `ask(query: str) -> str` is implemented.
4.  The `ask` method correctly calls `retrieve_relevant_context`, `format_prompt`, and `generate_llm_answer` in order.
5.  A new integration test, `test_rag_chatbot_pipeline`, is added to `tests/test_chatbot.py`.
6.  The test mocks the underlying RAG functions to assert that the orchestration logic of the `ask` method is correct.

#### **📝 Detailed Steps**

1.  **Implement the RAGChatbot Class:**

      * Add the following class to the end of your `src/chatbot.py` file. It will need imports from your other modules.

    <!-- end list -->

    ```python
    # src/chatbot.py (add to the end of the file)
    from src.data_loader import load_from_directory
    from src.text_processor import chunk_text
    from src.vector_store import get_vector_database_collection, embed_and_store_chunks

    class RAGChatbot:
        """
        Orchestrates the entire RAG pipeline.
        """
        def __init__(self, data_dir: str = "./data", db_dir: str = "./chroma_db"):
            print("Initializing RAG Chatbot...")
            self.collection = get_vector_database_collection(db_path=db_dir)

            # If the database is empty, run the full ingestion pipeline
            if self.collection.count() == 0:
                print("Vector database is empty. Running data ingestion pipeline...")
                # 1. Load data
                documents = load_from_directory(data_dir)
                # 2. Chunk text
                chunks = chunk_text(documents)
                # 3. Embed and store
                embed_and_store_chunks(chunks, self.collection)
                print("Data ingestion complete.")
            else:
                print(f"Loaded existing database with {self.collection.count()} documents.")

        def ask(self, query: str) -> str:
            """
            Asks the chatbot a question and gets a RAG-powered answer.
            """
            # 1. Retrieve context
            context = retrieve_relevant_context(query, self.collection)
            if not context:
                return "I couldn't find any relevant information to answer your question."
            
            # 2. Format prompt
            prompt = format_prompt(query, context)
            
            # 3. Generate answer
            answer = generate_llm_answer(prompt)
            
            return answer
    ```

2.  **Implement the Integration Test (TDD):**

      * Append the following test to `tests/test_chatbot.py`.

    <!-- end list -->

    ```python
    # tests/test_chatbot.py (append to existing file)
    from src.chatbot import RAGChatbot

    # ... (keep existing imports and tests)

    def test_rag_chatbot_pipeline(mocker):
        """
        Integration test for the RAGChatbot 'ask' method. Mocks the underlying
        RAG functions to test the orchestration.
        """
        # 1. Mock all external dependencies of the RAGChatbot class
        mocker.patch("src.chatbot.get_vector_database_collection")
        mocker.patch("src.chatbot.load_from_directory")
        mocker.patch("src.chatbot.chunk_text")
        mocker.patch("src.chatbot.embed_and_store_chunks")

        # Mock the functions used by the 'ask' method
        mock_retriever = mocker.patch(
            "src.chatbot.retrieve_relevant_context",
            return_value=["This is the retrieved context."]
        )
        mock_formatter = mocker.patch(
            "src.chatbot.format_prompt",
            return_value="Formatted prompt."
        )
        mock_generator = mocker.patch(
            "src.chatbot.generate_llm_answer",
            return_value="Final generated answer."
        )

        # 2. Initialize the chatbot and call the 'ask' method
        chatbot = RAGChatbot()
        user_query = "What is this test about?"
        response = chatbot.ask(user_query)

        # 3. Assertions
        # Check that the pipeline functions were called in the correct order with the correct data
        mock_retriever.assert_called_once_with(user_query, chatbot.collection)
        mock_formatter.assert_called_once_with(user_query, ["This is the retrieved context."])
        mock_generator.assert_called_once_with("Formatted prompt.")
        
        # Check that the final response is what we expect from the end of the pipeline
        assert response == "Final generated answer."

    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This confirms that your `RAGChatbot` class correctly wires together all the individual components into a working pipeline.