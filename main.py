from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# API key from environment variable with fallback for testing
API_KEY = os.getenv('CAPTIONS_API_KEY', 'b982e299-251f-4233-a813-dc491505a3df')

@app.route('/generate', methods=['POST'])
def generate_avatar():
    # Extract text from form data
    text = request.form.get('text')
    if not text:
        app.logger.error('No text provided in request')
        return jsonify({'error': 'Text is required'}), 400

    # Call captions.ai API
    url = 'https://api.captions.ai/generate-avatar'
    headers = {'Authorization': f'Bearer {API_KEY}'}
    data = {'text': text}

    app.logger.info(f'Sending request to {url} with text: {text}')
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        app.logger.info(f'API response: {result}')
        video_url = result.get('video_url')
        if not video_url:
            app.logger.error('No video_url in API response')
            return jsonify({'error': 'No video URL returned from API'}), 500
        return jsonify({'video_url': video_url})
    except requests.RequestException as e:
        app.logger.error(f'API request failed: {str(e)}')
        return jsonify({'error': f'API request failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)