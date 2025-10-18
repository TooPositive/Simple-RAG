Of course. Let's start with the very first task. This is the foundational step that sets up the entire project structure and ensures a clean, organized, and testable codebase from the beginning.

Here is the first spec task.

-----

### **Spec Task `SETUP-1`: Project Skeleton and Environment Initialization**

#### **🎯 Objective**

To create a robust and standardized project directory structure, initialize a Python virtual environment, and set up the initial files for version control and dependencies. This task establishes the foundation for the entire application.

#### **🔑 Key Components & Rationale**

  * **Directory Structure:** A well-defined structure separates concerns (source code, tests, data), making the project easier to navigate, maintain, and scale.
  * **Virtual Environment:** Isolates project dependencies, preventing conflicts with other Python projects on the system.
  * **`.gitignore`:** Prevents committing unnecessary or sensitive files (like the virtual environment, `.env` file, and large data files) to version control.
  * **`requirements.txt`:** Provides a reproducible environment by listing all necessary libraries for the project. We will start with the essentials for testing and configuration.

#### **✅ Acceptance Criteria**

1.  A root directory named `rag-chatbot` is created.
2.  Inside `rag-chatbot`, the following subdirectories are created: `src`, `tests`, `data`.
3.  The `src` and `tests` directories each contain an empty `__init__.py` file to mark them as Python packages.
4.  A Python virtual environment (e.g., in a `.venv` directory) is created and activated.
5.  A `.gitignore` file is created in the root directory with appropriate rules.
6.  A `requirements.txt` file is created in the root directory containing the initial dependencies.

#### **📝 Detailed Steps**

1.  **Create Directory Structure:**
    Execute the following commands in your terminal:

    ```bash
    mkdir -p rag-chatbot/src rag-chatbot/tests rag-chatbot/data
    touch rag-chatbot/src/__init__.py
    touch rag-chatbot/tests/__init__.py
    cd rag-chatbot
    ```

2.  **Initialize Virtual Environment:**
    Execute the following commands from within the `rag-chatbot` directory:

    ```bash
    python -m venv .venv
    # Activate the environment (command differs for OS)
    # Windows:
    # .\.venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Create `.gitignore` File:**
    Create a file named `.gitignore` in the `rag-chatbot` root with the following content. This is crucial for keeping your repository clean.

    ```
    # Python
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    .Python
    env/
    venv/
    .venv/
    pip-selfcheck.json

    # Environment
    .env

    # Data - Assuming data is project-specific and not for the repo
    data/

    # IDEs
    .vscode/
    .idea/
    ```

4.  **Create Initial `requirements.txt`:**
    Create a file named `requirements.txt` in the `rag-chatbot` root. We'll start with just the libraries needed for testing and environment management.

    ```
    # Testing
    pytest
    pytest-mock

    # Configuration
    python-dotenv
    ```

5.  **Install Initial Dependencies:**
    With your virtual environment active, run:

    ```bash
    pip install -r requirements.txt
    ```

#### **🧪 TDD - Verification (Manual)**

This setup task does not involve writing a Python test case. The "test" is to verify the deliverables manually:

  * Run `ls -R` (or `dir /s` on Windows) in the `rag-chatbot` directory and confirm that the file and folder structure matches the specification.
  * Run `pip list` and confirm that `pytest`, `pytest-mock`, and `python-dotenv` are installed.
