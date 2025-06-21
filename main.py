import os, time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_KEY = os.getenv("CAPTION_AI_API_KEY")
if not API_KEY:
    raise RuntimeError("CAPTION_AI_API_KEY environment variable is required")

HEADERS = {"x-api-key": API_KEY}

@app.route("/list-creators", methods=["POST"])
def list_creators():
    resp = requests.post("https://api.captions.ai/api/creator/list", headers=HEADERS)
    return jsonify(resp.json()), resp.status_code

@app.route("/generate-video", methods=["POST"])
def generate_video():
    data = request.get_json()
    script = data.get("script")
    creator = data.get("creatorName")
    if not script or not creator:
        return jsonify({"error": "creatorName and script are required"}), 400

    # 1. Submit video generation job
    sub = requests.post(
        "https://api.captions.ai/api/creator/submit",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"creatorName": creator, "script": script}
    ).json()

    job_id = sub.get("operationId")
    if not job_id:
        return jsonify({"error": "Failed to start video generation", "details": sub}), 500

    # 2. Poll until complete
    while True:
        status = requests.post(
            "https://api.captions.ai/api/creator/poll",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"operationId": job_id}
        ).json()
        if status.get("url"):
            return jsonify({"video_url": status["url"]})
        if status.get("status") == "error":
            return jsonify({"error": "Video generation failed"}), 500
        time.sleep(2)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)