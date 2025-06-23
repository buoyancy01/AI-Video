import os
import requests
from dotenv import load_dotenv
import time
import google.generativeai as genai
from flask import Flask, request, jsonify

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# API Keys from .env
MASTERPIECEX_APP_ID = os.getenv("MASTERPIECEX_APP_ID")
MASTERPIECEX_API_KEY = os.getenv("MASTERPIECEX_API_KEY")
CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY") # Changed from ELEVENLABS_API_KEY
GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")

# Configure Google Gemini API
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

# API Endpoints
MASTERPIECEX_API_URL = "https://api.masterpiecex.com/v1/generate"
CREATOMATE_API_URL = "https://api.creatomate.com/v1/renders"
MURF_API_URL = "https://api.murf.ai/v1/speech/generate" # Updated to Murf AI endpoint

# --- Google Gemini API Functions (Auto-Generated Scripts) ---
def generate_script_gemini(product_details):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Write a short, engaging advertising script (around 100-150 words) for a product with the following details: {product_details}. Focus on benefits and a call to action."
    response = model.generate_content(prompt)
    return response.text

# --- Murf AI Functions (Ultra-Realistic TTS) ---
def generate_murf_audio(text, voice_id="en-US-marcus"): # Default to a common Murf voice
    headers = {
        "Authorization": f"Bearer {MURF_API_KEY}", # Murf AI uses Bearer token
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "voiceId": voice_id,
        "format": "MP3" # Request MP3 format
    }
    response = requests.post(MURF_API_URL, headers=headers, json=data)
    response.raise_for_status()
    # Murf AI returns the audio file directly in the response content
    return response.content

# --- Masterpiece X Functions (3D Product Animation) ---
def generate_masterpiecex_3d_model(product_description, image_url=None):
    headers = {
        "X-App-Id": MASTERPIECEX_APP_ID,
        "X-Api-Key": MASTERPIECEX_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": product_description,
        "image_url": image_url
    }
    print(f"Masterpiece X Request Payload: {payload}")
    # In a real scenario, you'd make an actual API call here:
    # response = requests.post(MASTERPIECEX_API_URL, headers=headers, json=payload)
    # response.raise_for_status()
    # return response.json()
    
    # Returning a dummy response for now to allow script to run
    return {"id": "masterpiecex_model_id_123", "status": "processing", "url": "https://example.com/masterpiecex_model.glb"}

def get_masterpiecex_model_status(model_id):
    headers = {
        "X-App-Id": MASTERPIECEX_APP_ID,
        "X-Api-Key": MASTERPIECEX_API_KEY,
    }
    print(f"Checking Masterpiece X model status for ID: {model_id}")
    # In a real scenario, you'd make an actual API call here:
    # response = requests.get(f"{MASTERPIECEX_API_URL}/status/{model_id}", headers=headers)
    # response.raise_for_status()
    # return response.json()

    # Returning a dummy completed response for now
    return {"status": "completed", "url": "https://example.com/masterpiecex_model.glb"}

# --- Creatomate Functions (Dynamic Video Background) ---
def generate_creatomate_background(template_id, modifications):
    headers = {
        "Authorization": f"Bearer {CREATOMATE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "template_id": template_id,
        "modifications": modifications
    }
    print(f"Creatomate Request Payload: {payload}")
    response = requests.post(CREATOMATE_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def get_creatomate_render_status(render_id):
    headers = {
        "Authorization": f"Bearer {CREATOMATE_API_KEY}"
    }
    response = requests.get(f"{CREATOMATE_API_URL}/{render_id}", headers=headers)
    response.raise_for_status()
    return response.json()

@app.route('/')
def home():
    return "Welcome to the AI Video Generator Web Service! Use the /generate-video endpoint to create videos."

@app.route('/generate-video', methods=['POST'])
def generate_video():
    data = request.get_json()
    product_name = data.get('product_name', "Quantum Leap Smartwatch")
    product_features = data.get('product_features', "Advanced health tracking, 7-day battery life, sleek design, waterproof.")
    
    product_details = f"Product Name: {product_name}, Features: {product_features}"

    try:
        # 1. Auto-Generate Script
        print("\nGenerating script with Google Gemini API...")
        generated_script = generate_script_gemini(product_details)
        print(f"Generated Script: {generated_script}")

        # 2. Generate Ultra-Realistic TTS Audio (using Murf AI)
        print("\nGenerating audio with Murf AI...")
        audio_content = generate_murf_audio(generated_script) # Changed function call
        # In a web service, you might want to save this to a temporary file or cloud storage
        # For now, we'll just confirm its generation.
        # with open("output_audio.mp3", "wb") as f:
        #     f.write(audio_content)
        print("Audio content generated successfully.")

        # 3. Generate 3D Product Animation (Masterpiece X)
        print("\nGenerating 3D product animation with Masterpiece X...")
        masterpiecex_model_response = generate_masterpiecex_3d_model(product_details)
        masterpiecex_model_id = masterpiecex_model_response.get("id")
        if not masterpiecex_model_id:
            raise Exception(f"Masterpiece X model ID not found: {masterpiecex_model_response}")
        print(f"Masterpiece X Model ID: {masterpiecex_model_id}")

        masterpiecex_status = masterpiecex_model_response.get("status")
        masterpiecex_model_url = None
        while masterpiecex_status != "completed" and masterpiecex_status != "failed":
            print(f"Masterpiece X model status: {masterpiecex_status}. Waiting...")
            time.sleep(10)
            status_response = get_masterpiecex_model_status(masterpiecex_model_id)
            masterpiecex_status = status_response.get("status")
            if masterpiecex_status == "completed":
                masterpiecex_model_url = status_response.get("url")
                print(f"Masterpiece X 3D Model URL: {masterpiecex_model_url}")
            elif masterpiecex_status == "failed":
                raise Exception("Masterpiece X 3D model generation failed: {}".format(status_response.get("error")))

        if not masterpiecex_model_url:
            raise Exception("Masterpiece X 3D model URL not obtained.")

        # 4. Generate Creatomate Background Video
        print("\nGenerating Creatomate background video...")
        creatomate_template_id = "f3b247f9-d14c-42b2-8d8f-7e9dfff6bc64" # Your Creatomate template ID
        creatomate_modifications = {
            "Background-Image.source": "https://creatomate.com/files/assets/f4d19a7a-8043-4191-aea1-c225d977351f",
            "Product-Image.source": "https://creatomate.com/files/assets/cf4e2942-1046-4f1e-823c-a0162a1fc3df",
            "CTA.text": "Shop Now"
        }
        creatomate_response = generate_creatomate_background(creatomate_template_id, creatomate_modifications)
        creatomate_render_id = creatomate_response[0].get("id")
        if not creatomate_render_id:
            raise Exception(f"Creatomate render ID not found in response: {creatomate_response}")
        print(f"Creatomate Render ID: {creatomate_render_id}")

        creatomate_status = "rendering"
        creatomate_video_url = None
        while creatomate_status == "rendering" or creatomate_status == "queued":
            print(f"Creatomate background status: {creatomate_status}. Waiting...")
            time.sleep(30)
            status_response = get_creatomate_render_status(creatomate_render_id)
            creatomate_status = status_response.get("status")
            if creatomate_status == "succeeded":
                creatomate_video_url = status_response.get("url")
                print(f"Creatomate background video generated: {creatomate_video_url}")
            elif creatomate_status == "failed":
                raise Exception("Creatomate background generation failed: {}".format(status_response.get("error")))

        if not creatomate_video_url:
            raise Exception("Creatomate background video URL not obtained.")

        response_data = {
            "status": "success",
            "message": "Video generation process initiated and completed.",
            "generated_script": generated_script,
            "masterpiecex_model_url": masterpiecex_model_url,
            "creatomate_background_video_url": creatomate_video_url
        }
        return jsonify(response_data), 200

    except requests.exceptions.RequestException as e:
        error_message = f"An API error occurred: {e}"
        if e.response is not None:
            error_message += f" Response content: {e.response.text}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
