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
        # Ensure both image and audio are uploaded
        if "image" not in request.files or "audio" not in request.files:
            return jsonify({"error": "Missing 'image' or 'audio' file"}), 400

        image_file = request.files["image"]
        audio_file = request.files["audio"]

        # Validate file types
        if not image_file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
            return jsonify({"error": "Image must be .jpg, .jpeg, or .png"}), 400

        if not audio_file.filename.lower().endswith(".wav"):
            return jsonify({"error": "Audio must be .wav"}), 400

        # Save with correct extensions
        image_path = "face.jpg"
        audio_path = "voice.wav"

        image_file.save(image_path)
        audio_file.save(audio_path)

        print("✅ Uploaded files saved")

        # Optional debug logs
        print("🧪 face.jpg size:", os.path.getsize(image_path))
        print("🧪 voice.wav size:", os.path.getsize(audio_path))

        # Run model on Replicate
        output = replicate_client.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input={
                "face": open(image_path, "rb"),
                "audio": open(audio_path, "rb"),
                "fps": 25
            }
        )

        print("🧪 Raw output from Replicate:", output)

        if not output or not isinstance(output, str) or not output.startswith("http"):
            return jsonify({"error": "Invalid output from model"}), 500

        # Download video result
        video_response = requests.get(output)
        if video_response.status_code != 200:
            return jsonify({"error": "Failed to download result video"}), 500

        with open("output.mp4", "wb") as f:
            f.write(video_response.content)

        return send_file("output.mp4", mimetype="video/mp4")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Render needs 0.0.0.0 and PORT from env
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))