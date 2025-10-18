Of course. We now have the building blocks to process individual files. The next step is to create a single function that can process an entire directory of mixed-format files, creating a unified knowledge base.

-----

### **Spec Task `DATA-3`: Unified Knowledge Base Loader**

#### **🎯 Objective**

To implement a high-level "orchestrator" function that scans a given directory, identifies supported file types (PDFs, audio), and uses the previously created functions (`load_text_from_pdf` and `transcribe_audio_file`) to process them into a single, standardized list of documents.

#### **🔑 Key Components & Rationale**

  * **Orchestration Function:** A function like `load_from_directory` acts as a single entry point for the entire data loading stage. This simplifies the main application logic, which won't need to know the details of how different file types are handled.
  * **Standardized Data Structure:** The function will return a list of dictionaries, each with `source` and `content` keys (e.g., `[{'source': 'lecture.pdf', 'content': 'Text from PDF...'}, {'source': 'lecture.wav', 'content': 'Text from audio...'}]`). This consistent format is crucial for the downstream chunking and embedding processes.
  * **Integration Testing:** The test for this function will verify the interaction between the orchestrator and the individual file loaders. It's a form of integration test for our data loading module, ensuring all parts work together as expected.

#### **✅ Acceptance Criteria**

1.  A new function `load_from_directory(directory_path: str) -> list[dict]` is added to `src/data_loader.py`.
2.  The function iterates through a directory, checks file extensions (`.pdf`, `.wav`, `.mp3`), and calls the appropriate processing function for each.
3.  It ignores unsupported file types.
4.  It returns a list of dictionaries, where each dictionary contains the `source` (filename) and extracted `content`.
5.  A new test, `test_load_from_directory`, is added to `tests/test_data_loader.py`.
6.  This test will **mock** both `load_text_from_pdf` and `transcribe_audio_file` to ensure it runs quickly and only tests the orchestration logic.

#### **📝 Detailed Steps**

1.  **Implement the Directory Loader Function:**

      * Append the following code to your `src/data_loader.py` file. This function will serve as the main entry point for loading all knowledge base documents.

    <!-- end list -->

    ```python
    # src/data_loader.py (append to existing file)

    # ... (keep existing imports and functions)

    def load_from_directory(directory_path: str | Path) -> list[dict]:
        """
        Loads all supported documents from a directory into a list of dictionaries.

        Args:
            directory_path: The path to the directory containing the documents.

        Returns:
            A list of dictionaries, each representing a document.
        """
        if not isinstance(directory_path, Path):
            directory_path = Path(directory_path)

        if not directory_path.is_dir():
            raise ValueError("Provided path is not a valid directory.")

        documents = []
        supported_audio = {".wav", ".mp3", ".m4a"} # Add other formats if needed

        for file_path in directory_path.iterdir():
            if not file_path.is_file():
                continue

            doc = None
            if file_path.suffix.lower() == ".pdf":
                content = load_text_from_pdf(file_path)
                if content:
                    doc = {"source": file_path.name, "content": content}
            elif file_path.suffix.lower() in supported_audio:
                content = transcribe_audio_file(file_path)
                if content:
                    doc = {"source": file_path.name, "content": content}
            
            if doc:
                documents.append(doc)
        
        return documents

    ```

2.  **Implement the Integration Test (TDD):**

      * Append the following test to your `tests/test_data_loader.py` file. This test verifies the logic of the new function without re-testing the underlying file processors.

    <!-- end list -->

    ```python
    # tests/test_data_loader.py (append to existing file)
    from src.data_loader import load_from_directory

    # ... (keep existing imports and tests)

    def test_load_from_directory(mocker):
        """
        Tests the directory loader's orchestration logic.
        It mocks the individual file processors to isolate the test.
        """
        # 1. Set the path to the directory containing our test files
        fixture_dir = Path(__file__).parent / "fixtures"

        # 2. Mock the functions that are called by the function under test
        mock_pdf_loader = mocker.patch(
            "src.data_loader.load_text_from_pdf", 
            return_value="Text from PDF."
        )
        mock_audio_loader = mocker.patch(
            "src.data_loader.transcribe_audio_file", 
            return_value="Text from audio."
        )

        # 3. Call the function under test
        documents = load_from_directory(fixture_dir)

        # 4. Assertions
        # Check that we got two documents back (one PDF, one audio)
        assert len(documents) == 2
        
        # Verify that the correct loaders were called for the correct files
        mock_pdf_loader.assert_called_once_with(fixture_dir / "sample.pdf")
        mock_audio_loader.assert_called_once_with(fixture_dir / "sample.wav")

        # Create sets for easier comparison, ignoring order
        expected_sources = {"sample.pdf", "sample.wav"}
        actual_sources = {doc['source'] for doc in documents}
        assert actual_sources == expected_sources

        expected_contents = {"Text from PDF.", "Text from audio."}
        actual_contents = {doc['content'] for doc in documents}
        assert actual_contents == expected_contents
    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the full test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This confirms that your directory scanner correctly identifies files and dispatches them to the right processors, and that the final data structure is correct.