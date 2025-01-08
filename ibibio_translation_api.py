import streamlit as st
import requests
import os
from gtts import gTTS
from io import BytesIO
import json
import soundfile as sf

# Initialize clustering data
if 'clusters' not in st.session_state:
    st.session_state['clusters'] = {}

# Define Ollama API settings
OLLAMA_API_URL = "https://api.ollama.ai/v1/generate"  # Replace with actual endpoint
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")  # Store your API key securely

def generate_random_text():
    """Generate a random word or sentence using Ollama."""
    try:
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": "Provide a random English word or sentence.",
            "temperature": 0.7,
        }
        response = requests.post(OLLAMA_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("text", "Generated text could not be retrieved.")
    except Exception as e:
        st.error(f"Error generating text: {e}")
        return "Error: Unable to fetch text."

def text_to_audio(text):
    """Convert text to audio using gTTS."""
    tts = gTTS(text)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

def save_translation(english_text, ibibio_translation, cluster):
    """Save the translation to the appropriate cluster."""
    if cluster not in st.session_state['clusters']:
        st.session_state['clusters'][cluster] = []
    st.session_state['clusters'][cluster].append({
        "English": english_text,
        "Ibibio": ibibio_translation
    })
    
    # Save clusters to a file
    with open('translations.json', 'w') as f:
        json.dump(st.session_state['clusters'], f, indent=4)

# Streamlit app interface
st.title("English to Ibibio Translation App with Ollama")
st.write("Generate a random English word or sentence and provide its translation in Ibibio.")

# Generate a random word or sentence
if st.button("Generate Random Text") or 'current_text' not in st.session_state:
    st.session_state['current_text'] = generate_random_text()
st.write(f"### English Text: {st.session_state['current_text']}")

# Convert the text to audio and play it
audio_buffer = text_to_audio(st.session_state['current_text'])
st.audio(audio_buffer, format="audio/mp3")

#
# Get Ibibio translation from the user
ibibio_translation = st.text_input("Provide the Ibibio translation in text:")

# Optionally, get an audio translation
st.write("Upload the Ibibio translation as an audio file:")
audio_file = st.file_uploader("Upload audio file in .wav format:", type=["wav"])

if audio_file is not None:
    audio_data, samplerate = sf.read(audio_file)
    st.audio(audio_file, format="audio/wav")

# Input cluster name
cluster_name = st.text_input("Enter a cluster name for this translation:")

# Save the translation
if st.button("Save Translation"):
    if not ibibio_translation and not audio_file:
        st.warning("Please provide the Ibibio translation in either text or audio.")
    elif not cluster_name:
        st.warning("Please provide a cluster name.")
    else:
        translation = ibibio_translation if ibibio_translation else "Audio provided"
        save_translation(st.session_state['current_text'], translation, cluster_name)
        st.success("Translation saved successfully!")

# Display saved clusters
st.write("## Saved Clusters")
if st.session_state['clusters']:
    for cluster, translations in st.session_state['clusters'].items():
        st.write(f"### Cluster: {cluster}")
        for item in translations:
            st.write(f"- English: {item['English']}, Ibibio: {item['Ibibio']}")
else:
    st.write("No translations saved yet.")
