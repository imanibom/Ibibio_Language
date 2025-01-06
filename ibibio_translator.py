import streamlit as st
import random
import os
import json
from gtts import gTTS
from io import BytesIO
import soundfile as sf
import numpy as np
import streamlit_webrtc as webrtc

# Initialize clustering data
if 'clusters' not in st.session_state:
    st.session_state['clusters'] = {}

# Define a list of random English words and sentences
WORDS = ["apple", "banana", "computer", "house", "sun"]
SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "A journey of a thousand miles begins with a single step.",
    "To be or not to be, that is the question.",
]

def generate_random_text():
    """Generate a random word or sentence."""
    if random.choice([True, False]):
        return random.choice(WORDS)
    else:
        return random.choice(SENTENCES)

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
st.title("English to Ibibio Translation App")
st.write("Generate a random English word or sentence and provide its translation in Ibibio.")

# Generate a random word or sentence
english_text = st.button("Generate Random Text")
if english_text or 'current_text' not in st.session_state:
    st.session_state['current_text'] = generate_random_text()
st.write(f"### English Text: {st.session_state['current_text']}")

# Convert the text to audio and play it
audio_buffer = text_to_audio(st.session_state['current_text'])
st.audio(audio_buffer, format="audio/mp3")

# Get Ibibio translation from the user
ibibio_translation = st.text_input("Provide the Ibibio translation in text:")

# Optionally, get an audio translation
st.write("Or provide the Ibibio translation as audio:")

# Audio recording option
st.write("Record your audio translation:")
webrtc_ctx = webrtc.streamlit_webrtc(
    key="translation-audio-recorder",
    mode=webrtc.ClientSettings.MODE.SENDONLY,
    media_stream_constraints={
        "audio": True,
        "video": False,
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
)

audio_file = st.file_uploader("Upload audio file in .wav format:", type=["wav"])
if audio_file is not None:
    audio_data, samplerate = sf.read(audio_file)
    st.audio(audio_file, format="audio/wav")

# Input cluster name
cluster_name = st.text_input("Enter a cluster name for this translation:")

# Save the translation
if st.button("Save Translation"):
    if not ibibio_translation and not audio_file and not (webrtc_ctx and webrtc_ctx.state.playing):
        st.warning("Please provide the Ibibio translation in either text or audio.")
    elif not cluster_name:
        st.warning("Please provide a cluster name.")
    else:
        if webrtc_ctx and webrtc_ctx.state.playing:
            st.warning("Currently, audio recording cannot be saved directly. Please upload a recorded file.")
        else:
            save_translation(st.session_state['current_text'], ibibio_translation or "Audio provided", cluster_name)
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
