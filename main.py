import time
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# Replace these with your actual API token and avatar ID.
ELAI_API_TOKEN = "o4YU9YBUwEMhBs3y2U34OZ7bwzZ0fSEJ"
ELAI_AVATAR_ID = "6282089e661f88f4779b815f"
ELAI_API_URL = "https://apis.elai.io/api/v1/videos"

headers = {
    "Authorization": f"Bearer {ELAI_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        script_text = data.get("script", "This is Elai in action.")
        voice = data.get("voice", "en-US-Wavenet-A")
        language = data.get("language", "en")
        name = data.get("name", "Generated Elai Video")

        # The Elai API expects a slides list, not top-level script/voice/language.
        payload = {
            "name": name,
            "slides": [
                {
                    "avatarId": ELAI_AVATAR_ID,
                    "script": script_text,
                    "voice": voice,
                    "language": language
                }
            ]
        }

        # Step 1: Send creation request
        response = requests.post(ELAI_API_URL, headers=headers, json=payload)
        print("▶️ Elai API Request:", response.status_code, response.text)

        if response.status_code != 200:
            return jsonify({"error": response.text}), response.status_code

        creation_data = response.json()
        video_id = creation_data.get("id")
        if not video_id:
            return jsonify({"error": "Could not retrieve video ID from creation response"}), 500

        print(f"🎥 Created video with ID: {video_id}")

        # Step 2: Poll for video completion
        status_url = f"{ELAI_API_URL}/{video_id}"

        while True:
            status_response = requests.get(status_url, headers=headers)
            status_resp = status_response.json()
            status = status_resp.get("status")

            print(f"⌛ Status: {status}")

            if status == "completed":
                video_url = status_resp.get("videoUrl")
                if not video_url:
                    return jsonify({"error": "Video completed but no videoUrl found"}), 500
                break
            elif status == "failed":
                return jsonify({"error": "Video generation failed"}), 500

            time.sleep(5)

        # Step 3: Download and return video
        video_data = requests.get(video_url)
        with open("elai_output.mp4", "wb") as f:
            f.write(video_data.content)

        return send_file("elai_output.mp4", mimetype='video/mp4')

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)