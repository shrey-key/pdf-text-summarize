from flask import Flask, request, render_template, jsonify
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
import io
import os

app = Flask(__name__)

# Configure Google Gemini API (Replace with your API Key)
genai.configure(api_key="AIzaSyAAqksHax179b70O5ABFhziOH0TaG7UlT0")

# Function to Convert PDF to Images
def convert_pdf_to_images(pdf_path):
    """Converts PDF pages to images."""
    poppler_path = "/usr/bin/"
    images = convert_from_path(pdf_path, poppler_path=poppler_path)
    return images

    
# Function to Encode Image for API
def encode_image(image):
    """Encodes image as bytes for Gemini API."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return buffered.getvalue()

# Function to Extract Handwritten Text using Gemini 1.5 Flash
def extract_text_from_image(image):
    """Uses Gemini 1.5 Flash to extract handwritten text from an image."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    img_data = encode_image(image)

    response = model.generate_content([
        {"role": "user", "parts": [{"mime_type": "image/jpeg", "data": img_data}]},
        {"role": "user", "parts": [{"text": "Extract the handwritten text from this image."}]}
    ])

    return response.text.strip() if response.text else "No text extracted."

# Function to Summarize Extracted Text
def summarize_text(text):
    """Uses Gemini 1.5 Flash to summarize extracted text."""
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Summarize this text: {text}")
    return response.text.strip() if response.text else "No summary available."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    pdf_path = os.path.join("uploads", file.filename)
    file.save(pdf_path)

    # Convert PDF to Images
    images = convert_pdf_to_images(pdf_path)

    # Extract Handwritten Text from Each Page
    extracted_texts = [extract_text_from_image(img) for img in images]
    full_text = "\n\n".join(extracted_texts)

    # Summarize the Extracted Text
    summary = summarize_text(full_text)

    return render_template('results.html', extracted_text=full_text, summary=summary)
if __name__ == '__main__':
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True)
