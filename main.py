import time
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# Replace with your valid Elai API token
ELAI_API_TOKEN = "o4YU9YBUwEMhBs3y2U34OZ7bwzZ0fSEJ"
ELAI_API_URL = "https://apis.elai.io/api/v1/videos"

headers = {
    "Authorization": f"Bearer {ELAI_API_TOKEN}",
    "Content-Type": "application/json"
}

def build_slide(speech_text):
    # Generates a slide structure matching the Elai UI export
    return {
        "id": int(time.time() * 1000),  # Unique numeric ID per slide
        "speech": speech_text,
        "avatar": {
            "code": "neyson.business",
            "name": "Neyson Business",
            "canvas": "https://d3u63mhbhkevz8.cloudfront.net/common/neyson/business/neyson.png",
            "gender": "male",
            "limit": 300
        },
        "language": "English",
        "voice": "en-US-AndrewMultilingualNeural:default",
        "voiceProvider": "azure",
        "voiceType": "text",
        "animation": "fade_in",
        "canvas": {
            "version": "4.4.0",
            "background": "#ffffff",
            "objects": [
                {
                    "type": "avatar",
                    "left": 151.5,
                    "top": 36,
                    "width": 0,
                    "height": 0,
                    "fill": "#4868FF",
                    "scaleX": 0.3,
                    "scaleY": 0.3,
                    "src": "https://d3u63mhbhkevz8.cloudfront.net/common/neyson/business/neyson.png",
                    "avatarType": "transparent",
                    "animation": {
                        "type": None,
                        "exitType": None
                    },
                    "_exists": True,
                    "visible": True
                }
            ]
        },
        "duration": 6.384
    }

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json() or {}
        script_text = data.get("script", "Welcome to Elai! Type your script and click \"Render\" to generate your first video!")
        video_name = data.get("name", "Generated Elai Video")

        payload = {
            "name": video_name,
            "slides": [build_slide(script_text)]
        }

        # Step 1: Send creation request
        response = requests.post(ELAI_API_URL, headers=headers, json=payload)
        print("▶️ Elai API Request:", response.status_code, response.text)
        try:
            print("▶️ Elai API JSON:", response.json())
        except Exception as e:
            print("▶️ Could not decode JSON:", e)

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