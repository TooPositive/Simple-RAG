Right, the data is now loaded and standardized. The next crucial step is to break down these large blocks of text into smaller, digestible pieces for the embedding model. This process is called **chunking**.

-----

### **Spec Task `CHUNK-1`: Semantic Text Chunker**

#### **🎯 Objective**

To implement a function that takes the list of extracted documents and splits their content into smaller, semantically coherent chunks. We will use a "recursive character" splitting strategy, which is effective at keeping related sentences together.

#### **🔑 Key Components & Rationale**

  * **`src/text_processor.py`:** A new module dedicated to text manipulation tasks like chunking, cleaning, or formatting. This maintains a clean separation of concerns.
  * **`langchain_text_splitters` library:** We will use LangChain's `RecursiveCharacterTextSplitter`. This is a powerful, industry-standard tool that intelligently splits text by trying a sequence of separators (first paragraphs `\n\n`, then sentences `.`, then spaces `     `). This method is superior to a simple fixed-size split as it tries to preserve the semantic integrity of the text.
  * **Chunk Metadata:** It is **critical** that each new chunk retains a link back to its original source file. This allows for traceability and can be used later to show the user where the information came from. Our function will ensure this link (`source`) is preserved.

#### **✅ Acceptance Criteria**

1.  The `langchain-text-splitters` library is added to `requirements.txt`.
2.  A new file `src/text_processor.py` is created with a function `chunk_text(documents: list[dict], chunk_size: int, chunk_overlap: int) -> list[dict]`.
3.  A new test file `tests/test_text_processor.py` is created.
4.  The test `test_chunking` provides a long sample text to the function.
5.  The test asserts that the function returns more chunks than the input documents.
6.  The test asserts that the `source` field is correctly copied to all resulting chunks.
7.  The test asserts that the length of each chunk's content does not exceed the specified `chunk_size`.

#### **📝 Detailed Steps**

1.  **Update and Install Dependencies:**

      * Add the following to your `requirements.txt` file:
        ```
        # Text Processing
        langchain-text-splitters
        ```
      * Install the new library in your activated virtual environment:
        ```bash
        pip install -r requirements.txt
        ```

2.  **Implement the Chunker Function:**

      * Create the file `src/text_processor.py` and add the following Python code:

    <!-- end list -->

    ```python
    # src/text_processor.py
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from typing import List

    def chunk_text(
        documents: List[dict], chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[dict]:
        """
        Splits a list of documents into smaller, semantically meaningful chunks.

        Args:
            documents: A list of dictionaries, each with 'source' and 'content'.
            chunk_size: The maximum size of each chunk (in characters).
            chunk_overlap: The number of characters to overlap between chunks.

        Returns:
            A new list of dictionaries, where each dictionary represents a chunk.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        all_chunks = []
        for doc in documents:
            chunks_content = text_splitter.split_text(doc["content"])
            for chunk_content in chunks_content:
                all_chunks.append({
                    "source": doc["source"],
                    "content": chunk_content
                })
        
        return all_chunks

    ```

3.  **Implement the Unit Test (TDD):**

      * Create the file `tests/test_text_processor.py` and add the following test code:

    <!-- end list -->

    ```python
    # tests/test_text_processor.py
    from src.text_processor import chunk_text

    def test_chunking():
        """
        Tests the text chunking functionality to ensure it splits text correctly
        while preserving metadata.
        """
        # 1. Create a sample document with long content
        long_text = (
            "This is the first sentence. This is the second sentence which is a bit longer. "
            "Here comes the third one, making the paragraph grow. The fourth sentence will "
            "definitely push the content over the chunk size limit. The fifth sentence is "
            "here to ensure we have multiple chunks. The sixth sentence adds even more data. "
            "Finally, the seventh sentence concludes this long piece of text."
        )
        documents = [{"source": "test_document.txt", "content": long_text * 5}]
        
        # 2. Define chunking parameters for the test
        test_chunk_size = 150
        test_chunk_overlap = 30

        # 3. Call the function under test
        chunks = chunk_text(
            documents, 
            chunk_size=test_chunk_size, 
            chunk_overlap=test_chunk_overlap
        )

        # 4. Assertions
        assert isinstance(chunks, list)
        # We expect the long text to be split into multiple chunks
        assert len(chunks) > 1 

        for chunk in chunks:
            # All chunks must have the correct source
            assert chunk["source"] == "test_document.txt"
            # Each chunk's content must be a string
            assert isinstance(chunk["content"], str)
            # The length of each chunk should not exceed the specified size
            assert len(chunk["content"]) <= test_chunk_size
            
        # Check for overlap: the end of the first chunk should appear at the start of the second
        assert chunks[0]["content"][-test_chunk_overlap:] in chunks[1]["content"][:test_chunk_overlap+10]

    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  You should see all tests pass, including the new `test_chunking` test. This confirms your text splitter is correctly configured and working as expected.