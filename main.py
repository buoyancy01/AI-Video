import os
import requests
import replicate
from flask import Flask, request, send_file, jsonify
import tempfile # Import for creating temporary files
from urllib.parse import urlparse # To parse URLs and get paths

app = Flask(__name__)

# Load Replicate API token from environment
replicate_api_token = os.environ.get("REPLICATE_API_TOKEN")
replicate_client = replicate.Client(api_token=replicate_api_token)

@app.route("/")
def home():
    return "👄 Lip-Sync API is Live"

@app.route("/generate", methods=["POST"])
def generate():
    # Use a list to store temporary files created, so we can clean them up later
    temp_files_to_clean = []
    try:
        data = request.get_json()

        image_url = data.get("image_url")
        audio_url = data.get("audio_url")

        if not image_url or not audio_url:
            return jsonify({"error": "Missing 'image_url' or 'audio_url'"}), 400

        # --- Handle Image Download and Naming ---
        # Get filename and extension from the URL for robust naming
        image_filename = os.path.basename(urlparse(image_url).path)
        # Ensure it has an extension, default to .jpg if none found
        if '.' not in image_filename:
            image_filename = image_filename + ".jpg" # Default to .jpg if no extension

        # Create a temporary file with the correct extension
        # tempfile.NamedTemporaryFile creates a unique file and returns its path
        with tempfile.NamedTemporaryFile(suffix=f"_{image_filename}", delete=False) as temp_face_file:
            temp_files_to_clean.append(temp_face_file.name) # Add to cleanup list
            img_response = requests.get(image_url)
            if img_response.status_code != 200:
                return jsonify({"error": "Failed to download image"}), 400
            temp_face_file.write(img_response.content)
            face_path = temp_face_file.name # Get the actual path of the temp file

        # --- Handle Audio Download and Naming ---
        # Get filename and extension from the URL for robust naming
        audio_filename = os.path.basename(urlparse(audio_url).path)
        # Ensure it has an extension, default to .wav if none found
        if '.' not in audio_filename:
            audio_filename = audio_filename + ".wav" # Default to .wav if no extension

        with tempfile.NamedTemporaryFile(suffix=f"_{audio_filename}", delete=False) as temp_audio_file:
            temp_files_to_clean.append(temp_audio_file.name) # Add to cleanup list
            audio_response = requests.get(audio_url)
            if audio_response.status_code != 200:
                return jsonify({"error": "Failed to download audio"}), 400
            temp_audio_file.write(audio_response.content)
            audio_path = temp_audio_file.name # Get the actual path of the temp file

        print(f"✅ Inputs downloaded to: {face_path} and {audio_path}. Sending to Replicate...")

        # Run the Replicate model
        output = replicate_client.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input={
                "face": open(face_path, "rb"),  # Pass the path of the temporary file
                "audio": open(audio_path, "rb"), # Pass the path of the temporary file
                "fps": 25
            }
        )

        print("🧪 Raw output from Replicate:", output)

        # Validate output - the model is expected to return a URL string
        if not output or not isinstance(output, str) or not output.startswith("http"):
            # Add more detail from the raw output if it's not a URL
            error_detail = f"Unexpected model output: {output}" if output else "No output"
            return jsonify({"error": f"No valid output returned from model. {error_detail}"}), 500

        # --- Handle Video Download and Serving ---
        # Use a temporary file for the output video as well
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video_file:
            temp_files_to_clean.append(temp_video_file.name) # Add to cleanup list
            video_response = requests.get(output)
            if video_response.status_code != 200:
                return jsonify({"error": "Failed to download video from Replicate"}), 500
            temp_video_file.write(video_response.content)
            video_path = temp_video_file.name # Get the actual path of the temp file

        # Send the file and then clean up
        return send_file(video_path, mimetype="video/mp4", as_attachment=False) # as_attachment=False to display in browser

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # Ensure all temporary files are cleaned up
        for f_path in temp_files_to_clean:
            if os.path.exists(f_path):
                os.remove(f_path)
                print(f"Cleaned up temporary file: {f_path}")


# Required for Render external access
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
