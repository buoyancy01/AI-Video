import time
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# 🔐 Hardcoded API Token — use env var in production
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

        payload = {
            "name": name,
            "script": script_text,
            "avatarId": ELAI_AVATAR_ID,
            "voice": voice,
            "language": language
        }

        # Step 1: Send creation request
        response = requests.post(ELAI_API_URL, headers=headers, json=payload)
        print("▶️ Elai API Request:", response.status_code, response.text)

        if response.status_code != 200:
            return jsonify({"error": response.text}), response.status_code

        # Step 2: Wait 2 seconds before listing videos
        time.sleep(2)
        list_resp = requests.get(ELAI_API_URL, headers=headers).json()

        if not list_resp or not isinstance(list_resp, list) or not list_resp[0].get("id"):
            return jsonify({"error": "Could not retrieve video ID"}), 500

        video_id = list_resp[0]["id"]
        print(f"🎥 Fetched latest video ID: {video_id}")

        # Step 3: Poll for video completion
        status_url = f"{ELAI_API_URL}/{video_id}"

        while True:
            status_resp = requests.get(status_url, headers=headers).json()
            status = status_resp.get("status")

            if status == "completed":
                video_url = status_resp.get("videoUrl")
                break
            elif status == "failed":
                return jsonify({"error": "Video generation failed"}), 500

            print(f"⌛ Status: {status}")
            time.sleep(5)

        # Step 4: Download and return video
        video_data = requests.get(video_url)
        with open("elai_output.mp4", "wb") as f:
            f.write(video_data.content)

        return send_file("elai_output.mp4", mimetype='video/mp4')

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)