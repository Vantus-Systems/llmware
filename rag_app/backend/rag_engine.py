
import os
import logging
from llmware.library import Library
from llmware.retrieval import Query
from llmware.prompts import Prompt
from llmware.configs import LLMWareConfig
from llmware.models import ModelCatalog

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Encapsulates the core RAG logic using llmware.
    Designed to be a persistent singleton-like service.
    """
    def __init__(self, library_name="rag_assistant_v1"):
        self.library_name = library_name
        self.embedding_model = "mini-lm-sbert" # Fast, decent quality
        self.vector_db = "sqlite" # Embedded, no extra service needed
        self.inference_model = "bling-phi-3-gguf" # Robust local model
        self.library = None
        self.prompter = None

        # Initialize Configs
        LLMWareConfig().set_active_db("sqlite")

        # Ensure library exists or load it
        if not Library().check_if_library_exists(self.library_name):
            logger.info(f"Creating new library: {self.library_name}")
            self.library = Library().create_new_library(self.library_name)
        else:
            logger.info(f"Loading existing library: {self.library_name}")
            self.library = Library().load_library(self.library_name)

    def ingest_files(self, folder_path):
        """Ingests files from a local path."""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Path not found: {folder_path}")

        logger.info(f"Ingesting from {folder_path}...")

        # Add files
        self.library.add_files(folder_path)

        # Embed
        logger.info("Generating embeddings...")
        self.library.install_new_embedding(embedding_model_name=self.embedding_model,
                                           vector_db=self.vector_db)

        return self.library.get_library_card()

    def search(self, query_text, top_n=10):
        """Performs semantic search."""
        q = Query(self.library)
        results = q.semantic_query(query_text, result_count=top_n)
        return results

    def chat(self, user_message, history=None):
        """
        Generates a response using the LLM with context from the library.
        """
        if not self.prompter:
            logger.info(f"Loading model {self.inference_model}...")
            self.prompter = Prompt().load_model(self.inference_model)

        # 1. Search for context
        results = self.search(user_message, top_n=5)

        # 2. Add sources to prompt
        source_str = self.prompter.add_source_query_results(results)

        # 3. Prompt
        # Using a specialized prompt instruction for Q&A
        response = self.prompter.prompt_with_source(user_message, prompt_name="default_with_context")

        # Format response
        final_response = {
            "text": response[0]["llm_response"],
            "sources": results,
            "usage": response[0].get("usage", {})
        }

        return final_response

    def get_status(self):
        """Returns library statistics."""
        card = self.library.get_library_card()
        return card
