# app.py
import time
import requests
from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

ELAI_TOKEN = "iJwxbNGxFTJ0X3W6dJj40LmtAkRwxKgl"
HEADERS = {
    "Authorization": f"Bearer {ELAI_TOKEN}",
    "Content-Type": "application/json"
}

def create_video(slides, name="Demo Video", tags=None):
    url = "https://apis.elai.io/api/v1/videos"
    payload = {"name": name, "slides": slides}
    if tags:
        payload["tags"] = tags

    resp = requests.post(url, headers=HEADERS, json=payload)
    print("CREATE", resp.status_code, resp.text)
    if resp.status_code != 200:
        abort(resp.status_code, resp.text)
    body = resp.json()
    return body.get("_id") or body.get("id")

def render_video(video_id):
    url = f"https://apis.elai.io/api/v1/videos/render/{video_id}"
    resp = requests.post(url, headers=HEADERS)
    print("RENDER TRIGGER", resp.status_code, resp.text)
    if resp.status_code not in (200, 202):
        abort(resp.status_code, resp.text)

def wait_video(video_id, timeout=900):
    status_url = f"https://apis.elai.io/api/v1/videos/{video_id}"
    for _ in range(timeout // 5):
        resp = requests.get(status_url, headers=HEADERS)
        data = resp.json()
        status = data.get("status")
        print("STATUS", status)
        if status == "completed":
            return data.get("videoUrl")
        if status == "failed":
            abort(500, "Elai generation failed")
        time.sleep(5)
    abort(500, "Video creation timeout")

@app.route("/generate", methods=["POST"])
def generate():
    body = request.get_json()
    if not body or "slides" not in body:
        abort(400, "Missing 'slides' in request body")

    slides = body["slides"]
    name = body.get("name", "Demo Video")
    tags = body.get("tags")

    video_id = create_video(slides, name, tags)
    print("VIDEO ID:", video_id)

    render_video(video_id)
    video_url = wait_video(video_id)

    video_resp = requests.get(video_url)
    print("DOWNLOAD STATUS", video_resp.status_code)
    if video_resp.status_code != 200:
        abort(500, "Failed to download video")

    # Optionally: write to disk
    filename = "output.mp4"
    with open(filename, "wb") as f:
        f.write(video_resp.content)

    return send_file(filename, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)