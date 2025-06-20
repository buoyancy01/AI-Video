import os
import requests
import replicate
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# Load Replicate API token from environment
replicate_api_token = os.environ.get("REPLICATE_API_TOKEN")
replicate_client = replicate.Client(api_token=replicate_api_token)

@app.route("/")
def home():
    return "👄 Lip-Sync API is Live"

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()

        image_url = data.get("image_url")
        audio_url = data.get("audio_url")

        if not image_url or not audio_url:
            return jsonify({"error": "Missing 'image_url' or 'audio_url'"}), 400

        # Download image
        img_response = requests.get(image_url)
        if img_response.status_code != 200:
            return jsonify({"error": "Failed to download image"}), 400
        with open("face.jpg", "wb") as f:
            f.write(img_response.content)

        # Download audio
        audio_response = requests.get(audio_url)
        if audio_response.status_code != 200:
            return jsonify({"error": "Failed to download audio"}), 400
        with open("voice.wav", "wb") as f:
            f.write(audio_response.content)

        print("✅ Inputs downloaded. Sending to Replicate...")

        # Run the Replicate model
        output = replicate_client.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input={
                "face": open("face.jpg", "rb"),
                "audio": open("voice.wav", "rb"),
                "fps": 25
            }
        )

        print("🧪 Raw output from Replicate:", output)

        # Validate output
        if not output or not isinstance(output, str) or not output.startswith("http"):
            return jsonify({"error": "No valid output returned from model"}), 500

        # Download the video
        video_response = requests.get(output)
        if video_response.status_code != 200:
            return jsonify({"error": "Failed to download video from Replicate"}), 500
        with open("output.mp4", "wb") as f:
            f.write(video_response.content)

        return send_file("output.mp4", mimetype="video/mp4")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Required for Render external access
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))