Excellent. Our text is now properly chunked. The next phase is to prepare a place to store these chunks as numerical representations (vectors). We will set up a persistent vector database using ChromaDB.

-----

### **Spec Task `STORE-1`: Vector Database Setup**

#### **🎯 Objective**

To implement a function that initializes a persistent vector database client using ChromaDB. This function will create or connect to a database stored on the local disk, ensuring that our processed data is not lost when the application restarts.

#### **🔑 Key Components & Rationale**

  * **`chromadb` library:** A popular, open-source, and easy-to-use vector database that can run locally. Its "persistent client" feature is perfect for this project, as it saves the database to a directory on disk.
  * **`src/vector_store.py`:** We'll create a new module to encapsulate all interactions with the vector database. This adheres to the single-responsibility principle.
  * **`get_vector_database_client` function:** This function will act as a factory for getting a connection to a specific "collection" within our database. A collection is similar to a table in a traditional database.
  * **Testing with `tmp_path`:** `pytest` provides a powerful fixture called `tmp_path` that creates a unique temporary directory for a test function to run in. This is the perfect tool for testing our database initialization, as it ensures a clean environment for each test run and handles automatic cleanup of the created database files.

#### **✅ Acceptance Criteria**

1.  The `chromadb` library is added to `requirements.txt`.
2.  A new file `src/vector_store.py` is created.
3.  The file contains a function `get_vector_database_collection(...)` that initializes a persistent ChromaDB client and returns a collection object.
4.  A new test file `tests/test_vector_store.py` is created.
5.  The test `test_db_initialization` uses the `tmp_path` fixture to create a temporary database.
6.  The test asserts that the function returns a valid `Collection` object.
7.  The test verifies that the database directory is physically created on disk within the temporary path.

#### **📝 Detailed Steps**

1.  **Update and Install Dependencies:**

      * Add the following to your `requirements.txt` file:
        ```
        # Vector Database
        chromadb
        ```
      * Install the library in your virtual environment:
        ```bash
        pip install -r requirements.txt
        ```

2.  **Implement the Vector Database Initializer:**

      * Create the file `src/vector_store.py` and add the following Python code:

    <!-- end list -->

    ```python
    # src/vector_store.py
    import chromadb
    from chromadb.types import Collection
    from pathlib import Path

    def get_vector_database_collection(
        db_path: str = "./chroma_db", collection_name: str = "documents"
    ) -> Collection:
        """
        Initializes a persistent ChromaDB client and returns a collection.

        Args:
            db_path: The path to the directory where the database will be stored.
            collection_name: The name of the collection to create or load.

        Returns:
            A ChromaDB Collection object.
        """
        if not Path(db_path).is_dir():
            print(f"Database path '{db_path}' not found, creating it.")
            Path(db_path).mkdir(parents=True, exist_ok=True)
            
        client = chromadb.PersistentClient(path=db_path)
        
        collection = client.get_or_create_collection(name=collection_name)
        
        return collection

    ```

3.  **Implement the Unit Test (TDD):**

      * Create the file `tests/test_vector_store.py` and add the following test code:

    <!-- end list -->

    ```python
    # tests/test_vector_store.py
    import chromadb
    from src.vector_store import get_vector_database_collection

    def test_db_initialization(tmp_path):
        """
        Tests that the ChromaDB client is initialized correctly in a temporary directory.
        
        Args:
            tmp_path: A pytest fixture providing a temporary directory path.
        """
        # 1. Define a database path within the temporary directory provided by pytest
        db_test_path = str(tmp_path / "test_db")
        test_collection_name = "test_collection"

        # 2. Call the function under test
        collection = get_vector_database_collection(
            db_path=db_test_path, 
            collection_name=test_collection_name
        )

        # 3. Assertions
        # Check that the returned object is a ChromaDB Collection instance
        assert isinstance(collection, chromadb.Collection)
        
        # Check that the collection has the correct name
        assert collection.name == test_collection_name
        
        # Check that the database directory was physically created on disk
        assert (tmp_path / "test_db").exists()
        assert (tmp_path / "test_db").is_dir()
    ```

#### **🧪 TDD - Verification**

1.  Navigate to the root `rag-chatbot` directory.
2.  Run the test suite:
    ```bash
    pytest
    ```
3.  All tests should pass. This confirms your function can correctly create and connect to a persistent vector database, and the test automatically cleans up after itself.

With the database ready, say "**continue**" to proceed to the next step: generating embeddings and storing them.