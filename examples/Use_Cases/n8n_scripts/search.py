import os
import json
import sys
from llmware.library import Library
from llmware.retrieval import Query
from llmware.configs import LLMWareConfig

LLMWareConfig().set_active_db("sqlite")
LLMWareConfig().set_vector_db("chromadb")

lib_name = os.getenv("LIBRARY_NAME", "nextjs_rag_lib")
query = os.getenv("USER_QUERY", "")

if not query:
    print(json.dumps([]))
    sys.exit(0)

try:
    lib = Library().load_library(lib_name)
    q = Query(lib)

    # Perform semantic search
    results = q.semantic_query(query, result_count=15)

    # Output results as JSON
    print(json.dumps(results))

except Exception as e:
    # Output empty list on error to keep workflow running (or fail if strict)
    print(json.dumps([]))
    # print(str(e), file=sys.stderr)
