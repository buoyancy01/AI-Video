import time
import requests
from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

# 🔐 For now we hardcode—swap to os.getenv("ELAI_API_TOKEN") in prod
ELAI_API_TOKEN = "o4YU9YBUwEMhBs3y2U34OZ7bwzZ0fSEJ"
ELAI_AVATAR_ID = "6282089e661f88f4779b815f"
ELAI_API_URL = "https://apis.elai.io/api/v1/videos"

HEADERS = {
    "Authorization": f"Bearer {ELAI_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/generate", methods=["POST"])
def generate():
    payload = request.get_json() or {}
    name     = payload.get("name",    "Generated Elai Video")
    script   = payload.get("script",  "Hello from Elai!")
    voice    = payload.get("voice",   "en-US-Wavenet-A")
    language = payload.get("language","en")

    # 1) Trigger creation
    creation_payload = {
        "name":     name,
        "script":   script,
        "avatarId": ELAI_AVATAR_ID,
        "voice":    voice,
        "language": language
    }

    resp = requests.post(ELAI_API_URL, headers=HEADERS, json=creation_payload)
    print("▶️ CREATE ▶", resp.status_code, resp.text)

    if resp.status_code != 200:
        # Bail with the exact error from Elai
        return abort(resp.status_code, resp.text)

    data = resp.json()
    # 2) Extract nested video.id
    video_id = data.get("video", {}).get("id")
    if not video_id:
        print("❌ Creation response did not include video.id:", data)
        return abort(500, "Missing video ID in Elai response")

    print(f"🎥 Created video ID={video_id}")

    # 3) Poll status
    status_url = f"{ELAI_API_URL}/{video_id}"
    for _ in range(30):  # ~2.5 minutes max
        st = requests.get(status_url, headers=HEADERS).json()
        print("⌛ STATUS ▶", st.get("status"))
        if st.get("status") == "completed":
            video_url = st.get("videoUrl")
            break
        if st.get("status") == "failed":
            return abort(500, "Elai reported generation failed")
        time.sleep(5)
    else:
        return abort(500, "Video did not complete in time")

    # 4) Stream back the MP4
    video_data = requests.get(video_url)
    if video_data.status_code != 200:
        return abort(500, "Failed to download final video")
    with open("output.mp4", "wb") as f:
        f.write(video_data.content)

    return send_file("output.mp4", mimetype="video/mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)