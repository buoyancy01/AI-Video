import os, time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_KEY = os.getenv("CAPTION_AI_API_KEY")
if not API_KEY:
    raise RuntimeError("CAPTION_AI_API_KEY is required")

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
        return jsonify({"error": "Require script and creatorName"}), 400

    # Submit job
    sub = requests.post(
        "https://api.captions.ai/api/creator/submit",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"script": script, "creatorName": creator, "resolution": "fhd"}
    ).json()

    job_id = sub.get("operationId")
    if not job_id:
        return jsonify({"error": "Failed to submit video job", "details": sub}), 500

    # Poll for result
    while True:
        status = requests.post(
            "https://api.captions.ai/api/creator/poll",
            headers=HEADERS,
            json={"operationId": job_id}
        ).json()

        if status.get("status") == "completed":
            return jsonify({"video_url": status.get("url")})
        elif status.get("status") == "error":
            return jsonify({"error": "Video generation failed"}), 500
        time.sleep(2)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)