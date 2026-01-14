import os
import json
import sys
from llmware.models import ModelCatalog

query = os.getenv("USER_QUERY", "")

# Read search results from stdin
input_data = sys.stdin.read()

try:
    results = json.loads(input_data)
except json.JSONDecodeError:
    # If no valid JSON, return empty list
    print(json.dumps([]))
    sys.exit(0)

if not results or not query:
    print(json.dumps(results))
    sys.exit(0)

try:
    # Use a small, efficient reranker
    reranker = ModelCatalog().load_model("jina-reranker-tiny-onnx")

    # Reranker inference: (query, list_of_contexts)
    # Contexts can be dicts or strings. llmware handles dicts if they have 'text' key.
    ranked_results = reranker.inference(query, results)

    # Sort by 'rerank_score' descending
    ranked_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    # Return top 5
    print(json.dumps(ranked_results[:5]))

except Exception as e:
    # Fallback: return original results if reranking fails
    # print(f"Rerank failed: {e}", file=sys.stderr)
    print(json.dumps(results[:5]))
