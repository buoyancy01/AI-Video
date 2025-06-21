from flask import Flask, request, render_template, jsonify
import requests
import os

app = Flask(__name__)

# API key from environment variable with fallback for testing
API_KEY = os.getenv('CAPTIONS_API_KEY', "b982e299-251f-4233-a813-dc491505a3df")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_avatar():
    # Extract text from form data
    text = request.form.get('text')
    if not text:
        return jsonify({'error': 'Text is required'}), 400

    # Call captions.ai API
    url = 'https://api.captions.ai/generate-avatar'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    data = {'text': text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        video_url = response.json().get('video_url')
        if not video_url:
            return jsonify({'error': 'No video URL returned from API'}), 500
        return jsonify({'video_url': video_url})
    except requests.RequestException as e:
        return jsonify({'error': f'API request failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)