import os
import time
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

ELAI_API_TOKEN = os.getenv("ELAI_API_TOKEN")
ELAI_AVATAR_ID = "6282089e661f88f4779b815f"  # You can replace this with another avatar from Elai docs
ELAI_API_URL = "https://apis.elai.io/api/v1/videos/render"

headers = {
    "Authorization": f"Bearer {ELAI_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    script_text = data.get("script", "Hi there! This is a test from Elai API.")
    voice = data.get("voice", "en-US-Wavenet-A")
    language = data.get("language", "en")

    payload = {
        "avatarId": ELAI_AVATAR_ID,
        "script": script_text,
        "voice": voice,
        "language": language
    }

    try:
        response = requests.post(ELAI_API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            return jsonify({"error": response.json()}), response.status_code

        video_id = response.json()["videoId"]
        status_url = f"{ELAI_API_URL}/{video_id}"

        # Wait for video to be completed
        while True:
            status_resp = requests.get(status_url, headers=headers).json()
            if status_resp["status"] == "completed":
                video_url = status_resp["videoUrl"]
                break
            elif status_resp["status"] == "failed":
                return jsonify({"error": "Video generation failed"}), 500
            time.sleep(5)

        # Download video
        video_data = requests.get(video_url)
        with open("elai_output.mp4", "wb") as f:
            f.write(video_data.content)

        return send_file("elai_output.mp4", mimetype='video/mp4')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)