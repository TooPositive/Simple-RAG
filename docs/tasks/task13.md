Of course. The `RAGChatbot` class is now a complete, self-contained engine. The final step is to build a user interface for it. We'll create a simple, interactive Command-Line Interface (CLI) so you can talk to your chatbot directly from the terminal.

-----

### **Spec Task `APP-2`: Command-Line Interface (CLI)**

#### **🎯 Objective**

To create a runnable Python script (`main.py`) that initializes the `RAGChatbot` and provides a simple, interactive loop for users to ask questions and receive answers in the console.

#### **🔑 Key Components & Rationale**

  * **`main.py`:** A dedicated entry-point script. This is standard practice and makes it clear to anyone using your project how to run it.
  * **`if __name__ == "__main__"`:** This is a crucial Python construct. It ensures that the code inside this block only runs when the script is executed directly (e.g., `python main.py`), not when it's imported by another module (like a test file).
  * **Interactive Loop:** A `while True` loop is the simplest way to create a continuous chat session. It will keep prompting the user for input until they explicitly decide to exit.
  * **User Experience (UX):** Simple `print` statements are used to welcome the user, indicate when the bot is ready, and provide clear instructions on how to quit. This makes the application much more user-friendly.

#### **✅ Acceptance Criteria**

1.  A new file `main.py` is created in the project's root directory.
2.  The script imports and instantiates the `RAGChatbot` class.
3.  The script enters a loop that prompts the user for input.
4.  It calls the `chatbot.ask()` method with the user's input and prints the returned answer.
5.  The loop can be exited by typing a specific command (e.g., 'quit', 'exit').
6.  This task will be verified by manual testing, as the core logic is already covered by automated tests.

#### **📝 Detailed Steps**

1.  **Create the Main Application Script:**

      * In the **root directory** of your `rag-chatbot` project, create the file `main.py`.
      * Add the following Python code to it:

    <!-- end list -->

    ```python
    # main.py
    from src.chatbot import RAGChatbot

    def main():
        """
        Main function to run the interactive RAG chatbot.
        """
        # Note: You can customize the paths to your data and database directories.
        # Make sure you have your PDF and audio files in the './data' directory.
        try:
            chatbot = RAGChatbot(data_dir="./data", db_dir="./chroma_db")
        except Exception as e:
            print(f"Failed to initialize the chatbot. Error: {e}")
            return

        print("\n✅ Chatbot initialized successfully!")
        print("🤖 Ask a question about the 'Databases for GenAI' lecture.")
        print("   Type 'quit' or 'exit' to end the chat.\n")

        while True:
            try:
                query = input("You: ")
                if query.lower() in ["quit", "exit"]:
                    print("🤖 Goodbye!")
                    break

                if not query.strip():
                    continue

                print("🤖 Thinking...")
                answer = chatbot.ask(query)
                print(f"Bot: {answer}\n")

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\n🤖 Goodbye!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")


    if __name__ == "__main__":
        main()

    ```

#### **🧪 TDD - Verification (Manual)**

This part is verified by running the application and interacting with it.

1.  **Prepare Your Data:** Place the "Databases for GenAI" presentation PDF and the lecture audio files into the `./data` directory.
2.  **Set Your Environment:** Make sure your `.env` file is in the root directory and contains your valid Azure OpenAI credentials.
3.  **Run the App:** Open your terminal, ensure your virtual environment is active, and run the script from the project's root directory:
    ```bash
    python main.py
    ```
4.  **First-Time Run:** You should see messages indicating that the vector database is empty and the data ingestion pipeline is running. This may take some time depending on the size of your files and your network speed.
5.  **Interact:** Once initialized, ask one of the test questions, like: `"What are the production 'Do's' for RAG?"`
6.  **Verify Exit:** Type `quit` and press Enter. The program should exit gracefully.
