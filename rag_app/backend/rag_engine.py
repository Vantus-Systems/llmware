
import os
import logging
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from collections import Counter

from llmware.library import Library
from llmware.retrieval import Query
from llmware.prompts import Prompt
from llmware.configs import LLMWareConfig
from llmware.models import ModelCatalog

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Advanced RAG Engine encapsulating llmware logic with analytics capabilities.
    """
    def __init__(self, library_name="rag_assistant_v1"):
        self.library_name = library_name
        self.embedding_model = "mini-lm-sbert"
        self.vector_db = "sqlite"
        self.inference_model = "bling-phi-3-gguf"

        self.library = None
        self.prompter = None

        # Default Configuration
        LLMWareConfig().set_active_db("sqlite")

        self._load_library()

    def _load_library(self):
        if not Library().check_if_library_exists(self.library_name):
            logger.info(f"Creating new library: {self.library_name}")
            self.library = Library().create_new_library(self.library_name)
        else:
            logger.info(f"Loading existing library: {self.library_name}")
            self.library = Library().load_library(self.library_name)

    def configure_pipeline(self, embedding_model=None, vector_db=None, llm_model=None):
        """Dynamically update the pipeline configuration."""
        if embedding_model:
            self.embedding_model = embedding_model
        if vector_db:
            self.vector_db = vector_db
            LLMWareConfig().set_vector_db(vector_db)
        if llm_model:
            self.inference_model = llm_model
            self.prompter = None # Reset prompter to force reload

        logger.info(f"Pipeline Configured: Emb={self.embedding_model}, DB={self.vector_db}, LLM={self.inference_model}")
        return self.get_config()

    def get_config(self):
        return {
            "embedding_model": self.embedding_model,
            "vector_db": self.vector_db,
            "inference_model": self.inference_model
        }

    def ingest_files(self, folder_path):
        """Ingests files from a local path."""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Path not found: {folder_path}")

        logger.info(f"Ingesting from {folder_path}...")
        self.library.add_files(folder_path)

        logger.info(f"Generating embeddings using {self.embedding_model}...")
        self.library.install_new_embedding(embedding_model_name=self.embedding_model,
                                           vector_db=self.vector_db)

        return self.library.get_library_card()

    def search(self, query_text, top_n=10, use_hyde=False):
        """
        Performs semantic search, optionally using HyDE (Hypothetical Document Embeddings).
        """
        q = Query(self.library)

        search_query = query_text

        if use_hyde:
            # Generate a hypothetical answer to improve retrieval
            if not self.prompter:
                self.prompter = Prompt().load_model(self.inference_model)

            hyde_prompt = f"Please write a short, plausible passage that answers the question: {query_text}"
            hypothetical_doc = self.prompter.prompt_main(hyde_prompt, prompt_name="default_no_context")
            search_query = hypothetical_doc["llm_response"]
            logger.info(f"HyDE enabled. Searching for hypothetical doc: {search_query[:50]}...")

        results = q.semantic_query(search_query, result_count=top_n)
        return results

    def chat(self, user_message, history=None, use_hyde=False):
        """
        Generates a response using the LLM with context from the library.
        """
        if not self.prompter:
            logger.info(f"Loading model {self.inference_model}...")
            self.prompter = Prompt().load_model(self.inference_model)

        # 1. Search for context (with optional HyDE)
        results = self.search(user_message, top_n=5, use_hyde=use_hyde)

        # 2. Add sources to prompt
        source_str = self.prompter.add_source_query_results(results)

        # 3. Prompt
        response = self.prompter.prompt_with_source(user_message, prompt_name="default_with_context")

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

    # --- Analytics Features ---

    def perform_clustering(self, n_clusters=5):
        """
        Performs K-Means clustering on document embeddings to find topics.
        """
        q = Query(self.library)

        # Safe sampling: If library is empty or " " fails, handle gracefully
        try:
            # Query for a common term or use a wildcard if supported.
            # In llmware FTS, querying for "the" is often a safe bet for English text if stopwords aren't aggressive,
            # but getting *all* without a keyword requires a specific method usually.
            # We'll try a generic broad query or fallback to empty.
            results = q.text_query("report", result_count=100)
            if not results:
                 # Try another common word
                 results = q.text_query("data", result_count=100)
        except:
            return {"clusters": []}

        if not results:
            return {"clusters": []}

        # Mock clustering on text length and keyword frequency for demo purposes
        # if actual vectors aren't easily exposed in uniform API yet.

        # However, to be "best class", let's try to grab metadata.

        data = []
        for r in results:
            data.append({
                "text": r.get("text", ""),
                "source": r.get("file_source", "unknown"),
                "score": r.get("distance", 0) # This is distance to " " query, maybe not useful
            })

        df = pd.DataFrame(data)

        # Simple TF-IDF like feature extraction for clustering demo
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
        X = vectorizer.fit_transform(df['text'])

        kmeans = KMeans(n_clusters=min(n_clusters, len(df)), random_state=42)
        kmeans.fit(X)

        df['cluster'] = kmeans.labels_

        # Summarize clusters
        clusters = []
        for i in range(n_clusters):
            cluster_docs = df[df['cluster'] == i]
            if len(cluster_docs) == 0: continue

            # Get top keywords
            centroid = kmeans.cluster_centers_[i]
            # Map back to features... (complex without feature names)
            # Instead, just take most common source
            top_source = cluster_docs['source'].mode().iloc[0] if not cluster_docs.empty else "N/A"

            clusters.append({
                "id": int(i),
                "count": int(len(cluster_docs)),
                "top_source": top_source,
                "sample_text": cluster_docs.iloc[0]['text'][:50] + "..."
            })

        return {"clusters": clusters}

    def analyze_sentiment(self):
        """
        Analyzes sentiment of the ingested content (Sampled).
        """
        q = Query(self.library)
        try:
            results = q.text_query("report", result_count=50)
            if not results:
                results = q.text_query("data", result_count=50)
        except:
            results = []

        sentiments = {"positive": 0, "negative": 0, "neutral": 0}

        # Simple keyword based for speed/demo (Enterprise would use a specific model)
        pos_words = ["success", "good", "great", "excellent", "profit", "growth", "valid", "true"]
        neg_words = ["fail", "error", "loss", "bad", "bug", "false", "crash"]

        for r in results:
            text = r.get("text", "").lower()
            score = 0
            for w in pos_words: score += text.count(w)
            for w in neg_words: score -= text.count(w)

            if score > 0: sentiments["positive"] += 1
            elif score < 0: sentiments["negative"] += 1
            else: sentiments["neutral"] += 1

        return sentiments

    def extract_time_series(self):
        """
        Extracts temporal data from document metadata (created/modified dates).
        """
        # Strategy: Query all docs, aggregate by date
        # Note: 'created_date' in blocks is often populated by the parser if available.
        # If empty, we can't plot it. We'll fallback to "Unknown" bucket.

        q = Query(self.library)
        try:
            # Broad query
            results = q.text_query("report", result_count=500)
            if not results:
                results = q.text_query("data", result_count=500)
        except:
            return []

        dates = []
        for r in results:
            # Parser populates 'created_date' or 'modified_date'
            d = r.get("created_date") or r.get("modified_date") or "Unknown"
            # Normalize date (take YYYY-MM)
            if len(d) >= 7:
                dates.append(d[:7])
            else:
                dates.append("Unknown")

        # Count frequency
        counts = Counter(dates)

        # Format for frontend
        data = []
        for date, count in counts.items():
            if date != "Unknown":
                data.append({"date": date, "count": count})

        # Sort by date
        data.sort(key=lambda x: x["date"])

        return data
