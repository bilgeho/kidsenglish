import streamlit as st
from gtts import gTTS
import io

st.title("🧒 Kids English Story")
name = st.text_input("Çocuk Adı:")
level = st.selectbox("Seviye", ["Başlangıç", "Orta", "İleri"])

if st.button("Hikaye Başlat"):
    stories = {
        "Başlangıç": "The cat is happy.",
        "Orta": "The cat runs fast in park.",
        "İleri": "Clever cat chased playful dog."
    }
    story = stories[level]
    st.write(f"📖 {name}: **{story}**")
    
    tts = gTTS(story, lang='en', slow=True)
    audio = io.BytesIO()
    tts.write_to_fp(audio)
    st.audio(audio, format='audio/mp3')

