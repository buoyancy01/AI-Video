import os
from flask import Flask, request, send_file, jsonify
import replicate
import requests

app = Flask(__name__)
replicate_client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    image_url = data.get('image_url')
    audio_url = data.get('audio_url')

    if not image_url or not audio_url:
        return jsonify({'error': 'image_url and audio_url required'}), 400

    # Fetch image and save it
    img_response = requests.get(image_url)
    if img_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch image from URL'}), 400
    with open('face.jpg', 'wb') as f:
        f.write(img_response.content)

    # Fetch audio and save it
    aud_response = requests.get(audio_url)
    if aud_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch audio from URL'}), 400
    with open('voice.wav', 'wb') as f:
        f.write(aud_response.content)

    # Run the first-order-model to animate the image
    # Note: The 'driving_video' is also set to 'face.jpg' here.
    # If you intend to use an actual driving video, you would need to fetch that too.
    animation_output = replicate_client.run(
        "ali-siarohin/first-order-model:latest",
        input={
            "image": open('face.jpg', 'rb'),
            "driving_video": open('face.jpg', 'rb')
        }
    )

    # Ensure the animation output contains a video URL
    if not animation_output or 'video' not in animation_output:
        return jsonify({'error': 'First-order-model did not return a video'}), 500

    # Run wav2lip to synchronize audio with the animated video
    final_output = replicate_client.run(
        "pmpromonet/wav2lip:latest",
        input={
            "video": open(animation_output['video'], 'rb'),
            "audio": open('voice.wav', 'rb')
        }
    )

    # Ensure the final output contains a video URL
    if not final_output or 'output' not in final_output:
        return jsonify({'error': 'Wav2lip model did not return a video output'}), 500

    video_url = final_output['output']
    
    # Fetch the final generated video
    result_response = requests.get(video_url)
    if result_response.status_code != 200:
        return jsonify({'error': 'Failed to fetch final video from Replicate'}), 500
    with open('output.mp4', 'wb') as f:
        f.write(result_response.content)

    return send_file('output.mp4', mimetype='video/mp4')

# Optional: Add a main block to run the Flask app if this file is executed directly
if __name__ == '__main__':
    app.run(debug=True)