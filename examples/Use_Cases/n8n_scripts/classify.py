import os
import json
import sys
from llmware.models import ModelCatalog

query = os.getenv("USER_QUERY", "")

if not query:
    print(json.dumps({"error": "No query provided"}))
    sys.exit(1)

# Using SLIM model for intent classification
# In a Fortune-500 setup, this routes the query to different workflows
try:
    classifier = ModelCatalog().load_model("slim-intent-tool")
    response = classifier.inference(query)

    # Enrich the response
    output = {
        "query": query,
        "classification": response,
        "intent": "coding_assistance" # Simplified default for this demo
    }

    print(json.dumps(output))

except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
