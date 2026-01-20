
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_engine import RAGEngine

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Server")

app = Flask(__name__)
CORS(app) # Allow frontend to talk to backend

# Initialize RAG Engine
# In production, this might be initialized lazily or via a factory
rag = RAGEngine()

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the status of the RAG system."""
    try:
        status = rag.get_status()
        return jsonify({"status": "ok", "library": status})
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest():
    """Ingest a local folder path."""
    data = request.json
    folder_path = data.get('path')

    if not folder_path:
        return jsonify({"status": "error", "message": "Path is required"}), 400

    try:
        stats = rag.ingest_files(folder_path)
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Semantic search."""
    data = request.json
    query = data.get('query')
    top_n = data.get('top_n', 10)

    if not query:
        return jsonify({"status": "error", "message": "Query is required"}), 400

    try:
        results = rag.search(query, top_n=top_n)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with the LLM."""
    data = request.json
    message = data.get('message')
    history = data.get('history', [])

    if not message:
        return jsonify({"status": "error", "message": "Message is required"}), 400

    try:
        response = rag.chat(message, history)
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
