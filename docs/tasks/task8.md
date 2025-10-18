Excellent. The vector database is set up and ready. Now we'll populate it. This task involves taking our text chunks, converting each one into a numerical vector using an embedding model, and then storing these vectors alongside their original text in ChromaDB.

-----

### **Spec Task `STORE-2`: Embedding and Storing Pipeline**

#### **🎯 Objective**

To implement a pipeline function that takes a list of text chunks, generates a vector embedding for each one using the Azure OpenAI service, and then ingests them into the ChromaDB collection, including the source metadata.

#### **🔑 Key Components & Rationale**

  * **Azure OpenAI Embedding Client:** We'll use the `openai` library to connect to your deployed embedding model on Azure (e.g., `text-embedding-ada-002`). This service converts text into high-dimensional vectors.
  * **Batch Processing:** To make the process efficient and respect API rate limits, the function should be designed to handle chunks in batches, though for this initial implementation, we can process them one by one for simplicity.
  * **Metadata Storage:** Storing the `source` of each chunk as metadata is crucial. When we retrieve a vector later, we also get its metadata, allowing us to trace the answer back to the original document.
  * **Mocking the Embedding Client:** This is the most important part of the test strategy. Generating embeddings requires a network call and costs money. By mocking the client, our test will verify the entire pipeline's logic (iteration, data formatting, database insertion) without ever contacting Azure. It becomes fast, free, and completely reliable.

#### **✅ Acceptance Criteria**

1.  A new function `embed_and_store_chunks(chunks: list[dict], collection: Collection)` is added to `src/vector_store.py`.
2.  The function initializes an `AzureOpenAI` client using the settings from `src/config.py`.
3.  For each chunk, it generates a vector embedding and stores the chunk's content, its source metadata, and a unique ID in the ChromaDB collection.
4.  A new test, `test_embedding_and_storing`, is added to `tests/test_vector_store.py`.
5.  The test **mocks** the `client.embeddings.create` method to return predictable, fake vector data.
6.  The test asserts that after the function runs, the items in the ChromaDB collection correctly match the input chunks and their metadata.

#### **📝 Detailed Steps**

1.  **Implement the Embedding and Storing Function:**

      * Append the following code to your `src/vector_store.py` file.

    <!-- end list -->

    ```python
    # src/vector_store.py (append to existing file)
    from openai import AzureOpenAI
    from src.config import settings
    from typing import List

    # ... (keep existing imports and get_vector_database_collection function)

    def embed_and_store_chunks(chunks: List[dict], collection: Collection):
        """
        Generates embeddings for a list of text chunks and stores them in ChromaDB.

        Args:
            chunks: A list of chunk dictionaries, each with 'source' and 'content'.
            collection: The ChromaDB collection to store the embeddings in.
        """
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.openai_api_version,
        )

        documents_to_add = []
        metadatas_to_add = []
        ids_to_add = []

        for i, chunk in enumerate(chunks):
            documents_to_add.append(chunk["content"])
            metadatas_to_add.append({"source": chunk["source"]})
            ids_to_add.append(f"chunk_{i}") # Chroma requires a unique ID for each item

        # Note: In a production scenario, you would batch the API calls.
        # For this project, we'll embed the whole list at once if it's not too large.
        try:
            response = client.embeddings.create(
                input=documents_to_add,
                model=settings.embedding_model_name
            )
            embeddings = [item.embedding for item in response.data]

            collection.add(
                embeddings=embeddings,
                documents=documents_to_add,
                metadatas=metadatas_to_add,
                ids=ids_to_add
            )
            print(f"Successfully embedded and stored {len(chunks)} chunks.")
        except Exception as e:
            print(f"An error occurred during embedding or storing: {e}")

    ```

2.  **Implement the Mocked Unit Test (TDD):**

      * Append the following test to your `tests/test_vector_store.py` file.

    <!-- end list -->

    ```python
    # tests/test_vector_store.py (append to existing file)
    from unittest.mock import MagicMock
    from src.vector_store import embed_and_store_chunks

    # ... (keep existing test_db_initialization)

    def test_embedding_and_storing(mocker, tmp_path):
        """
        Tests the embedding and storing pipeline with a mocked OpenAI client.
        """
        # 1. Setup: Create a temporary DB and sample chunks
        db_test_path = str(tmp_path / "test_db")
        collection = get_vector_database_collection(db_path=db_test_path)
        sample_chunks = [
            {"source": "doc1.pdf", "content": "This is the first chunk."},
            {"source": "doc2.txt", "content": "This is the second chunk."},
        ]

        # 2. Mocking: Create a fake response from the OpenAI embeddings API
        # Each "Embedding" object needs an `embedding` attribute which is a list of floats
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1] * 1536  # Matching ADA model's dimension
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.2] * 1536

        mock_api_response = MagicMock()
        mock_api_response.data = [mock_embedding_1, mock_embedding_2]

        # Patch the client and its method call to return our fake response
        mock_client_instance = MagicMock()
        mock_client_instance.embeddings.create.return_value = mock_api_response
        mocker.patch("src.vector_store.AzureOpenAI", return_value=mock_client_instance)

        # 3. Call the function under test
        embed_and_store_chunks(chunks=sample_chunks, collection=collection)

        # 4. Assertions
        # Assert that the embedding client was called correctly
        mock_client_instance.embeddings.create.assert_called_once_with(
            input=["This is the first chunk.", "This is the second chunk."],
            model="text-embedding-ada-002" # Or whatever is in your config
        )

        # Assert that the correct number of items were stored
        assert collection.count() == 2

        # Retrieve the items and verify their content and metadata
        stored_items = collection.get(include=["metadatas", "documents"])
        assert sorted(stored_items["ids"]) == ["chunk_0", "chunk_1"]
        assert "This is the first chunk." in stored_items["documents"]
        assert "This is the second chunk." in stored_items["documents"]
        assert {"source": "doc1.pdf"} in stored_items["metadatas"]
        assert {"source": "doc2.txt"} in stored_items["metadatas"]
    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This is a major milestone\! It confirms your entire data ingestion pipeline—from raw files to a queryable vector database—is logically sound and correctly implemented.

With the knowledge base now indexed, you're ready to build the user-facing part of the chatbot. Say "**continue**" to start building the retrieval and generation logic.