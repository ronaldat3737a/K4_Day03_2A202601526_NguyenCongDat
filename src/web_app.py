"""
🖥️ DEMO WEB APP (dùng khi pitching): giao diện so sánh Chatbot Baseline vs ReAct Agent.
Chạy: python src/web_app.py rồi mở http://127.0.0.1:5000
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, Response, jsonify, request, send_from_directory

from app import (
    run_baseline_chatbot,
    run_react_agent,
    run_react_agent_stream,
    load_test_cases,
)
from providers import get_llm_provider

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")
provider = get_llm_provider()


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/test-cases")
def api_test_cases():
    return jsonify(load_test_cases())


@app.get("/api/provider")
def api_provider():
    return jsonify({
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "Offline Mock Mode"),
    })


@app.post("/api/compare")
def api_compare():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Thiếu câu hỏi."}), 400

    baseline_answer = run_baseline_chatbot(question, provider)
    agent_result = run_react_agent(question, provider)

    return jsonify({
        "question": question,
        "baseline": {"answer": baseline_answer},
        "agent": agent_result,
    })


@app.post("/api/compare/stream")
def api_compare_stream():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Thiếu câu hỏi."}), 400

    def event(obj):
        return json.dumps(obj, ensure_ascii=False) + "\n"

    def gen():
        # ponytail: giao diện chat chỉ hiện 1 câu trả lời (agent) — bỏ nhánh baseline
        # khỏi luồng live để đỡ tốn 1 lượt gọi LLM không cần thiết, phản hồi nhanh hơn.
        # So sánh Baseline vs Agent đầy đủ vẫn có ở /api/compare và ở CLI (src/app.py).
        for ev in run_react_agent_stream(question, provider):
            yield event(ev)
        yield event({"type": "done"})

    return Response(gen(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    print(f"🔌 LLM Provider: {provider.__class__.__name__} ({getattr(provider, 'model_name', 'Mock')})")
    print("🌐 Demo UI: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
