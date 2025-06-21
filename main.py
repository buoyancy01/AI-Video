import time
import requests
from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

ELAI_TOKEN = "iJwxbNGxFTJ0X3W6dJj40LmtAkRwxKgl"
HEADERS = {"Authorization": f"Bearer {ELAI_TOKEN}", "Content-Type": "application/json"}

def create_video(payload):
    url = "https://apis.elai.io/api/v1/videos"
    resp = requests.post(url, headers=HEADERS, json=payload)
    print("CREATE", resp.status_code, resp.text)
    if resp.status_code != 200:
        abort(resp.status_code, resp.text)
    return resp.json().get("video", {}).get("id")

def wait_video(video_id, timeout=150):
    status_url = f"https://apis.elai.io/api/v1/videos/{video_id}"
    for _ in range(timeout // 5):
        resp = requests.get(status_url, headers=HEADERS).json()
        status = resp.get("status")
        print("STATUS", status)
        if status == "completed":
            return resp.get("videoUrl")
        if status == "failed":
            abort(500, "Elai generation failed")
        time.sleep(5)
    abort(500, "Video creation timeout")

@app.route("/generate", methods=["POST"])
def generate():
    body = request.get_json() or {}
    payload = {
        "name":     body.get("name", "Demo Video"),
        "script":   body.get("script", "Hello from Elai"),
        "avatarId": "6282089e661f88f4779b815f",
        "voice":    body.get("voice", "en-US-Wavenet-A"),
        "language": body.get("language", "en")
    }

    vid = create_video(payload)
    print("VID", vid)
    if not vid:
        abort(500, "Missing video ID in creation response")

    video_url = wait_video(vid)
    v = requests.get(video_url)
    print("DOWNLOAD STATUS", v.status_code)
    if v.status_code != 200:
        abort(500, "Failed to download video")
    with open("output.mp4", "wb") as f:
        f.write(v.content)

    return send_file("output.mp4", mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)