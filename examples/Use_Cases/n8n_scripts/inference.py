import os
import json
import sys
from llmware.prompts import Prompt

query = os.getenv("USER_QUERY", "")

# Read context from stdin
input_data = sys.stdin.read()

try:
    context_list = json.loads(input_data)
except json.JSONDecodeError:
    context_list = []

# Select a model suitable for code planning
# 'bling-phi-3-gguf' is a good local option
model_name = "bling-phi-3-gguf"

try:
    prompter = Prompt().load_model(model_name)

    # Add context
    prompter.add_source_query_results(context_list)

    system_instruction = (
        "You are a Senior Software Engineer specializing in Next.js 16, React 19, and Tailwind CSS. "
        "Create a production-ready feature implementation plan based on the user request. "
        "Focus on best practices."
    )

    full_prompt = f"{system_instruction}\n\nUser Request: {query}"

    response = prompter.prompt_with_source(full_prompt)

    # Output the structured response
    print(json.dumps(response))

except Exception as e:
    print(json.dumps({"error": str(e)}))
