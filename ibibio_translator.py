import streamlit as st
import random
import json
from gtts import gTTS
from io import BytesIO
import soundfile as sf
import tempfile
from pydub import AudioSegment

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
    tts = gTTS(text, lang='en')
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

def merge_audio(english_audio, ibibio_audio):
    """Merge English and Ibibio audio into one file."""
    english_segment = AudioSegment.from_file(english_audio, format="mp3")
    if ibibio_audio:
        ibibio_segment = AudioSegment.from_file(ibibio_audio, format="wav")
        combined_audio = english_segment + AudioSegment.silent(duration=500) + ibibio_segment
    else:
        combined_audio = english_segment
    output_buffer = BytesIO()
    combined_audio.export(output_buffer, format="mp3")
    output_buffer.seek(0)
    return output_buffer

@st.cache_data(ttl=180)
def get_cached_audio(english_text, ibibio_audio_file):
    """Cache the merged audio for 3 minutes."""
    english_audio = text_to_audio(english_text)
    merged_audio = merge_audio(english_audio, ibibio_audio_file)
    return merged_audio

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

def load_clusters():
    """Load clusters from the file if available."""
    try:
        with open('translations.json', 'r') as f:
            st.session_state['clusters'] = json.load(f)
    except FileNotFoundError:
        st.session_state['clusters'] = {}

# Load clusters at the start
if 'clusters_loaded' not in st.session_state:
    load_clusters()
    st.session_state['clusters_loaded'] = True

# Streamlit app interface
st.title("English to Ibibio Translation App")
st.write("Generate a random English word or sentence and provide its translation in Ibibio.")

# Generate a random word or sentence
if st.button("Generate Random Text") or 'current_text' not in st.session_state:
    st.session_state['current_text'] = generate_random_text()
st.write(f"### English Text: {st.session_state['current_text']}")

# Convert the text to audio and play it
audio_buffer = text_to_audio(st.session_state['current_text'])
st.audio(audio_buffer, format="audio/mp3")

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

# Merge and cache audio for download
if st.button("Generate Combined Audio"):
    merged_audio = get_cached_audio(st.session_state['current_text'], audio_file)
    st.audio(merged_audio, format="audio/mp3")
    st.download_button(
        "Download Combined Audio",
        data=merged_audio,
        file_name="combined_audio.mp3",
        mime="audio/mp3"
    )

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

# Display saved clusters with edit and delete options
st.write("## Saved Clusters")
if st.session_state['clusters']:
    for cluster, translations in st.session_state['clusters'].items():
        st.write(f"### Cluster: {cluster}")
        for idx, item in enumerate(translations):
            st.write(f"- English: {item['English']}, Ibibio: {item['Ibibio']}")
            if st.button(f"Delete [{idx}] from {cluster}"):
                translations.pop(idx)
                st.experimental_rerun()
else:
    st.write("No translations saved yet.")

# Download translations as JSON
if st.button("Download Translations as JSON"):
    json_data = json.dumps(st.session_state['clusters'], indent=4)
    st.download_button(
        "Download JSON",
        data=json_data,
        file_name="translations.json",
        mime="application/json"
    )
