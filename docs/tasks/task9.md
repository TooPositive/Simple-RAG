Excellent. The knowledge base is now fully indexed and ready for querying. We are now moving from the data preparation phase to the active RAG (Retrieval-Augmented Generation) phase. The first step is **Retrieval**.

-----

### **Spec Task `RAG-1`: Query Embedding and Context Retrieval**

#### **🎯 Objective**

To implement a function that takes a user's question, converts it into a vector embedding, and queries the ChromaDB to find the most semantically similar text chunks from our knowledge base. This is the "R" in RAG.

#### **🔑 Key Components & Rationale**

  * **`src/chatbot.py`:** A new module for the core RAG logic. This separates the interactive part of the application from the data processing pipeline.
  * **Symmetric Embedding:** It's crucial to use the **exact same embedding model** for the query as we used for the documents. This ensures that the user's question and the stored chunks exist in the same "vector space," making the similarity search meaningful.
  * **ChromaDB `query` method:** This is the core function for performing a similarity search. Given a query vector, it efficiently calculates the distance to all stored vectors and returns the nearest neighbors.
  * **Controlled Test Environment:** The test for this function is critical. We will manually create a miniature vector database with known, simple vectors. Then, we will mock the embedding API to produce a query vector that we know is closest to one of our stored documents. This allows us to precisely test the retrieval logic without any ambiguity.

#### **✅ Acceptance Criteria**

1.  A new file `src/chatbot.py` is created.
2.  It contains a function `retrieve_relevant_context(query: str, collection: Collection, n_results: int = 3) -> list[str]`.
3.  A new test file `tests/test_chatbot.py` is created.
4.  The test `test_retrieval` manually adds a few documents with known, simple vectors to a temporary ChromaDB collection.
5.  The test **mocks** the embedding client to return a predictable query vector.
6.  The test asserts that the function returns the correct text content of the document whose stored vector is closest to the mocked query vector.

#### **📝 Detailed Steps**

1.  **Implement the Retrieval Function:**

      * Create the file `src/chatbot.py` and add the following Python code:

    <!-- end list -->

    ```python
    # src/chatbot.py
    from openai import AzureOpenAI
    from chromadb.types import Collection
    from typing import List
    from src.config import settings

    def retrieve_relevant_context(
        query: str, collection: Collection, n_results: int = 3
    ) -> List[str]:
        """
        Embeds a query and retrieves the most relevant document chunks from the vector DB.

        Args:
            query: The user's question.
            collection: The ChromaDB collection to query.
            n_results: The number of relevant chunks to retrieve.

        Returns:
            A list of the most relevant document chunk strings.
        """
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.openai_api_version,
        )

        try:
            # Generate the embedding for the user's query
            response = client.embeddings.create(
                input=[query],
                model=settings.embedding_model_name
            )
            query_embedding = response.data[0].embedding

            # Query the database to find the most similar chunks
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents"]
            )
            
            # The result is a list of lists, we need the first list of documents
            return results["documents"][0] if results["documents"] else []
        
        except Exception as e:
            print(f"An error occurred during context retrieval: {e}")
            return []

    ```

2.  **Implement the Unit Test (TDD):**

      * Create the file `tests/test_chatbot.py` and add the following test code:

    <!-- end list -->

    ```python
    # tests/test_chatbot.py
    from unittest.mock import MagicMock
    from src.chatbot import retrieve_relevant_context
    from src.vector_store import get_vector_database_collection

    def test_retrieval(mocker, tmp_path):
        """
        Tests the context retrieval function to ensure it returns the correct document
        based on a mocked query vector.
        """
        # 1. Setup: Create a temporary DB and manually add documents with simple vectors
        db_test_path = str(tmp_path / "test_db")
        collection = get_vector_database_collection(db_path=db_test_path)
        
        # Add documents with known, simple embeddings for predictable testing
        collection.add(
            embeddings=[[0.1, 0.9], [0.8, 0.2]], # Vector 1 is "far", Vector 2 is "close"
            documents=["This is about cats.", "This is about dogs."],
            metadatas=[{"source": "cat.txt"}, {"source": "dog.txt"}],
            ids=["cat1", "dog1"]
        )

        # 2. Mocking: Mock the embedding API to return a vector close to the "dogs" document
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.7, 0.3] # This vector is closer to [0.8, 0.2]
        
        mock_api_response = MagicMock()
        mock_api_response.data = [mock_embedding]

        mock_client_instance = MagicMock()
        mock_client_instance.embeddings.create.return_value = mock_api_response
        mocker.patch("src.chatbot.AzureOpenAI", return_value=mock_client_instance)
        
        # 3. Call the function under test
        user_query = "Tell me about canines."
        retrieved_docs = retrieve_relevant_context(
            query=user_query, 
            collection=collection, 
            n_results=1
        )

        # 4. Assertions
        # Check that the embedding client was called with the user query
        mock_client_instance.embeddings.create.assert_called_once_with(
            input=[user_query],
            model="text-embedding-ada-002"
        )
        
        # Check that the retrieved document is the one we expected ("dogs")
        assert len(retrieved_docs) == 1
        assert retrieved_docs[0] == "This is about dogs."

    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This confirms that your retrieval function correctly uses a query to find and return the most relevant information from the vector store.