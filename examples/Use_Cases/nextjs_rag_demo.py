
"""
Next.js 16 + React 19 + Tailwind Codebase RAG Assistant
=======================================================

This example demonstrates a "corporate-level" RAG system designed to assist with
development in a modern Next.js stack.

Key Features:
1.  **Automated Ingestion**: Scans and indexes source code (.tsx, .ts, .js, .css, etc.).
2.  **Semantic Search**: Uses embedding models to understand code context.
3.  **Inference**: Uses a local LLM (or cloud model) to answer questions and generate plans.
4.  **Reranking**: Uses a cross-encoder to refine search results for better relevance.
5.  **Production-Ready Structure**: Encapsulated in a class for easy integration into workflows.

Dependencies:
    pip install llmware

"""

import os
import shutil
import logging
from llmware.library import Library
from llmware.retrieval import Query
from llmware.prompts import Prompt
from llmware.configs import LLMWareConfig
from llmware.setup import Setup
from llmware.models import ModelCatalog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseRAG:
    def __init__(self, library_name="nextjs_codebase", embedding_model="mini-lm-sbert", vector_db="chromadb"):
        """
        Initialize the Codebase RAG system.

        Args:
            library_name (str): Name of the llmware library to create/use.
            embedding_model (str): Name of the embedding model (e.g., 'mini-lm-sbert', 'nomic-embed-text-v1.5').
            vector_db (str): Vector database to use (e.g., 'chromadb', 'milvus', 'postgres').
        """
        self.library_name = library_name
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.library = None

        # Ensure setup
        LLMWareConfig().set_active_db("sqlite")
        LLMWareConfig().set_vector_db(vector_db)

    def ingest_codebase(self, source_path):
        """
        Ingest the codebase from the given path.
        """
        logger.info(f"Ingesting codebase from: {source_path}")

        # Create or load library
        logger.info(f"Creating/Loading library: {self.library_name}")
        self.library = Library().create_new_library(self.library_name)

        # Clear existing data to ensure fresh ingestion (optional, good for demo)
        # In production, you might want incremental updates.
        # For this demo, we'll just add files.

        # Add files - llmware parser will handle supported code extensions
        # Note: We updated parsers.py to support .ts, .tsx, etc.
        parsing_output = self.library.add_files(input_folder_path=source_path)

        logger.info(f"Ingestion complete. Stats: {parsing_output}")

        # Create embeddings
        logger.info(f"Generating embeddings using {self.embedding_model}...")
        self.library.install_new_embedding(embedding_model_name=self.embedding_model, vector_db=self.vector_db)

        logger.info("Embedding generation complete.")

    def search_code(self, query, result_count=10):
        """
        Perform a semantic search on the codebase.
        """
        if not self.library:
            self.library = Library().load_library(self.library_name)

        logger.info(f"Searching for: {query}")
        q = Query(self.library)
        results = q.semantic_query(query, result_count=result_count)

        return results

    def rerank_results(self, query, results, model_name="jinaai/jina-reranker-v1-tiny-en", top_n=5):
        """
        Rerank the search results using a cross-encoder model.
        """
        logger.info(f"Reranking results using {model_name}...")

        # Load reranker model
        reranker = ModelCatalog().load_model(model_name)

        # Prepare inputs for reranker
        # inference takes (query, context_list)
        # context_list can be list of strings or list of dicts (if dicts, keys used are 'text', 'context', or 'passage')

        # Rerank
        ranked_results = reranker.inference(query, results)

        # If output is a list of dicts with scores, sort and slice
        # Note: llmware rerankers usually return a list of dicts with 'rerank_score' added

        # Sort by rerank_score descending
        ranked_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        return ranked_results[:top_n]

    def generate_feature_plan(self, request, model_name="bling-phi-3-gguf"):
        """
        Generate a feature implementation plan using RAG.
        """
        if not self.library:
            self.library = Library().load_library(self.library_name)

        logger.info(f"Generating plan for: {request}")

        # Load model
        logger.info(f"Loading model: {model_name}")
        prompter = Prompt().load_model(model_name)

        # Retrieve relevant context
        # We assume the request implies looking for relevant existing code to modify or reference.
        # 1. Semantic Search
        search_results = self.search_code(request, result_count=20)

        # 2. Rerank (Refinement)
        try:
            # Using a lightweight reranker
            refined_results = self.rerank_results(request, search_results, top_n=5)
        except Exception as e:
            logger.warning(f"Reranking failed (using raw search results): {e}")
            refined_results = search_results[:5]

        # Construct prompt source
        sources = prompter.add_source_query_results(refined_results)

        # Define the prompt
        # We want a corporate-level implementation plan.
        system_instruction = (
            "You are a Senior Software Engineer specializing in Next.js 16, React 19, and Tailwind CSS. "
            "Your task is to create a detailed, production-ready feature implementation plan based on the user request "
            "and the provided existing codebase context. "
            "Identify which files need to be created or modified. "
            "Suggest code snippets where appropriate. "
            "Focus on best practices, performance, and maintainability."
        )

        # We can pass system_instruction as 'system_prompt' in some models or prepend to query
        full_query = f"{system_instruction}\n\nUser Request: {request}"

        response = prompter.prompt_with_source(full_query, prompt_name="default_with_context")

        # In a real app, you might want to iterate or chain prompts.

        return response

def main():
    # Path to our dummy project
    # In a real scenario, this would be the root of your git repo
    project_path = os.path.join(os.getcwd(), "tests", "data", "nextjs_project")

    if not os.path.exists(project_path):
        print(f"Error: Project path not found at {project_path}")
        return

    # Initialize RAG
    rag = CodebaseRAG(library_name="nextjs_assistant_v1")

    # 1. Ingest Codebase
    print("\n--- Step 1: Ingesting Codebase ---")
    rag.ingest_codebase(project_path)

    # 2. Verify Ingestion by searching for a specific component
    print("\n--- Step 2: Verifying Ingestion (Search) ---")
    results = rag.search_code("Button component")
    for i, res in enumerate(results[:3]):
        print(f"Result {i+1}: {res['file_source']} (Score: {res['distance']})")
        print(f"Snippet: {res['text'][:100]}...")

    # 3. Generate a Plan
    print("\n--- Step 3: Generating Feature Implementation Plan ---")
    user_request = "I need to add a 'Login' button to the homepage header that redirects to /login."

    # Using 'bling-phi-3-gguf' as it's a good local model supported by llmware
    responses = rag.generate_feature_plan(user_request, model_name="bling-phi-3-gguf")

    print("\n--- AI Response ---")
    for r in responses:
        print(r["llm_response"])

if __name__ == "__main__":
    main()
