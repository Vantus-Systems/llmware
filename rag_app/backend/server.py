
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_engine import RAGEngine

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Server")

app = Flask(__name__)
CORS(app)

rag = RAGEngine()

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        status = rag.get_status()
        config = rag.get_config()
        return jsonify({"status": "ok", "library": status, "config": config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/config', methods=['POST'])
def configure():
    data = request.json
    try:
        config = rag.configure_pipeline(
            embedding_model=data.get("embedding_model"),
            vector_db=data.get("vector_db"),
            llm_model=data.get("llm_model")
        )
        return jsonify({"status": "success", "config": config})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest():
    data = request.json
    folder_path = data.get('path')
    if not folder_path:
        return jsonify({"status": "error", "message": "Path is required"}), 400
    try:
        stats = rag.ingest_files(folder_path)
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    history = data.get('history', [])
    use_hyde = data.get('use_hyde', False)

    if not message:
        return jsonify({"status": "error", "message": "Message is required"}), 400
    try:
        response = rag.chat(message, history, use_hyde=use_hyde)
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analytics/clusters', methods=['GET'])
def get_clusters():
    try:
        data = rag.perform_clustering()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analytics/sentiment', methods=['GET'])
def get_sentiment():
    try:
        data = rag.analyze_sentiment()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analytics/timeseries', methods=['GET'])
def get_timeseries():
    try:
        data = rag.extract_time_series()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
