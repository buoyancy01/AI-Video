import time
import requests
from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

# Hardcode for now; move to os.getenv("ELAI_API_TOKEN") in prod
ELAI_API_TOKEN = "PASTE_YOUR_ELAI_API_TOKEN_HERE"
ELAI_API_URL   = "https://apis.elai.io/api/v1/videos/render"
ELAI_AVATAR_ID = "6282089e661f88f4779b815f"  # default avatar from docs

HEADERS = {
    "Authorization": f"Bearer {ELAI_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/generate", methods=["POST"])
def generate():
    body = request.get_json() or {}
    name     = body.get("name",    "Demo Video")
    script   = body.get("script",  "Hello! This is a test from Elai.")
    voice    = body.get("voice",   "en-US-Wavenet-A")
    language = body.get("language","en")

    # 1) kick off render
    payload = {
        "name":     name,
        "script":   script,
        "avatarId": ELAI_AVATAR_ID,
        "voice":    voice,
        "language": language
    }
    r = requests.post(ELAI_API_URL, headers=HEADERS, json=payload)
    print("▶️ CREATE ▶", r.status_code, r.text)
    if r.status_code != 200:
        return abort(r.status_code, r.text)

    data = r.json()
    video_id = data.get("videoId")
    if not video_id:
        print("❌ No videoId in response:", data)
        return abort(500, "Missing videoId in Elai response")

    print(f"🎥 videoId={video_id}")

    # 2) poll until done
    status_url = f"https://apis.elai.io/api/v1/videos/{video_id}"
    for _ in range(30):   # give it up to ~2.5 minutes
        s = requests.get(status_url, headers=HEADERS).json()
        status = s.get("status")
        print("⌛ status=", status)
        if status == "completed":
            video_url = s.get("videoUrl")
            break
        if status == "failed":
            return abort(500, "Elai generation failed")
        time.sleep(5)
    else:
        return abort(500, "Timed out waiting for video")

    # 3) fetch and return
    v = requests.get(video_url)
    if v.status_code != 200:
        return abort(500, "Failed to download video")
    with open("output.mp4", "wb") as f:
        f.write(v.content)

    return send_file("output.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)