from flask import Flask, jsonify, request
from aw.graph import run_aw

app = Flask(__name__)


@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "tokyo-sushi-aw"})


@app.post("/api/search")
def search():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()
    if not question:
        return jsonify({"error": "question is required"}), 400
    try:
        return jsonify(run_aw(question))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
