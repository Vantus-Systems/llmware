import os
import sys
from llmware.library import Library
from llmware.parsers import Parser
from llmware.configs import LLMWareConfig

# Configure SQLite/Chroma as default for the workflow
LLMWareConfig().set_active_db("sqlite")
LLMWareConfig().set_vector_db("chromadb")

# Monkey-patching to ensure support even if library isn't fully updated in environment
code_extensions = ["ts", "tsx", "js", "jsx", "css", "py", "json", "java", "cpp", "c", "h", "cs", "php", "rb", "go", "rs", "swift", "kt"]
for ext in code_extensions:
    if ext not in Parser.ACCEPTED_FILE_FORMATS:
        Parser.ACCEPTED_FILE_FORMATS.append(ext)

    # Check if code_types attr exists (it might not in older versions)
    if hasattr(Parser, "code_types"):
        if ext not in Parser.code_types:
            Parser.code_types.append(ext)
    else:
        # Fallback: treat as text_types if code_types doesn't exist
        if ext not in Parser.text_types:
            Parser.text_types.append(ext)

lib_name = os.getenv("LIBRARY_NAME", "nextjs_rag_lib")
source_path = os.getenv("SOURCE_PATH", "./tests/data/nextjs_project")

print(f"Starting ingestion for library: {lib_name}")
print(f"Source path: {source_path}")

try:
    lib = Library().create_new_library(lib_name)
    lib.add_files(input_folder_path=source_path)

    # Using a small, fast model for demo purposes
    # In production, use 'nomic-embed-text-v1.5' or similar
    embedding_model = os.getenv("EMBEDDING_MODEL", "mini-lm-sbert")
    print(f"Generating embeddings with {embedding_model}...")
    lib.install_new_embedding(embedding_model_name=embedding_model, vector_db="chromadb")
    print("Ingestion and Embedding Complete.")

except Exception as e:
    print(f"Error during ingestion: {e}")
    sys.exit(1)
