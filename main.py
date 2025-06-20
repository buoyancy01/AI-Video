import time
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# ⚠️ Hardcoded Elai API Token — update this later to use environment variables for safety
ELAI_API_TOKEN = "o4YU9YBUwEMhBs3y2U34OZ7bwzZ0fSEJ"
ELAI_AVATAR_ID = "6282089e661f88f4779b815f"  # Default Elai avatar
ELAI_API_URL = "https://apis.elai.io/api/v1/videos"

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
        # Request Elai to render the video
        response = requests.post(ELAI_API_URL, headers=headers, json=payload)
        print("Elai API Raw Response:", response.status_code, response.text)

        if response.status_code != 200:
            return jsonify({"error": response.text}), response.status_code

        video_id = response.json().get("videoId")
        if not video_id:
            return jsonify({"error": "Missing video ID in response"}), 500

        # Check status of the video
        status_url = f"{ELAI_API_URL}/{video_id}"
        print(f"Checking status for video ID: {video_id}")

        while True:
            status_resp = requests.get(status_url, headers=headers).json()
            print("Status:", status_resp.get("status"))

            if status_resp["status"] == "completed":
                video_url = status_resp["videoUrl"]
                break
            elif status_resp["status"] == "failed":
                return jsonify({"error": "Video generation failed"}), 500
            time.sleep(5)

        # Download the video
        print("Downloading video from:", video_url)
        video_data = requests.get(video_url)
        with open("elai_output.mp4", "wb") as f:
            f.write(video_data.content)

        return send_file("elai_output.mp4", mimetype='video/mp4')

    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)