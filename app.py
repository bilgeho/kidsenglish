import streamlit as st
from gtts import gTTS
import io

# --- AI GORSEL PROMPT FONKSIYONU ---
def build_image_prompt(child_name: str, level: str, page: int, base_text: str) -> str:
    level_desc = {
        "Başlangıç": "very simple, clear shapes, for kids aged 4-6",
        "Orta": "slightly more detailed, for kids aged 7-9",
        "İleri": "richer scenes with more details, for kids aged 9-11"
    }.get(level, "children's book style")

    page_moods = [
        "bright morning scene",
        "playful action scene",
        "focused searching scene",
        "surprised reaction scene",
        "happy sharing moment",
        "calm resting scene",
        "exciting adventure moment",
        "sunset soft light",
        "cozy close-up scene",
        "warm story ending scene"
    ]
    page_mood = page_moods[page]

    learning_hint = f"Show clearly the idea: '{base_text}' so kids can learn this English sentence."

    prompt = (
        f"cute children’s book illustration of a child named {child_name}, "
        f"in the story moment: {base_text}. "
        f"{learning_hint} "
        f"Scene style: {page_mood}, {level_desc}, colorful, soft lines, no text, "
        f"safe for children"
    )
    return prompt

# --- PROFIL ve STATE ---
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "level": "Başlangıç",
        "page": 0,
        "progress": 0,
        "total_pages_read": 0,
        "total_correct": 0,
    }

st.title("🧒 Kids English Story")
st.markdown("Çocuklar için seviyeli, kişiselleştirilmiş ve sesli İngilizce hikayeler")

# --- PROFIL GIRISI ---
name = st.text_input("Çocuk Adı:", value=st.session_state.profile["name"])
level = st.selectbox(
    "Seviye",
    ["Başlangıç", "Orta", "İleri"],
    index=["Başlangıç", "Orta", "İleri"].index(st.session_state.profile["level"])
)

if st.button("👋 Profili Kaydet ve Başla"):
    st.session_state.profile["name"] = name
    st.session_state.profile["level"] = level
    st.session_state.profile["page"] = 0
    st.session_state.profile["progress"] = 0
    st.session_state.profile["total_pages_read"] = 0
    st.session_state.profile["total_correct"] = 0
    st.rerun()

# --- 10 SAYFALIK HIKAYELER ---
stories = {
    "Başlangıç": [
        "This is a cat.",
        "The cat is happy.",
        "The cat runs.",
        "This is a dog.",
        "The dog is friendly.",
        "Cat and dog play.",
        "They play in the park.",
        "The sun is bright.",
        "They eat and rest.",
        "Good night, friends!"
    ],
    "Orta": [
        "The happy cat runs in the park.",
        "A small dog joins the cat.",
        "They chase a red ball.",
        "The ball rolls under a tree.",
        "The cat jumps to catch it.",
        "The dog barks and laughs.",
        "Children watch and smile.",
        "The sun starts to go down.",
        "They sit and eat snacks.",
        "It was a fun day."
    ],
    "İleri": [
        "The clever cat woke up early.",
        "In the big park, the playful dog waited.",
        "They planned an exciting adventure together.",
        "A red ball became their treasure.",
        "They searched behind trees and under benches.",
        "The cat climbed high to look around.",
        "The dog sniffed the ground carefully.",
        "Finally, they found the ball near a flower bed.",
        "They shared the toy and felt proud.",
        "It was the perfect ending to a brave day."
    ]
}

# --- QUIZ SORULARI ---
quiz_data = {
    "Başlangıç": {
        0: {"question": "What animal is this?",
            "options": ["Cat", "Dog", "Bird"],
            "answer": "Cat"},
        1: {"question": "How is the cat?",
            "options": ["Sad", "Happy", "Angry"],
            "answer": "Happy"},
        2: {"question": "What does the cat do?",
            "options": ["Runs", "Sleeps", "Flies"],
            "answer": "Runs"},
        3: {"question": "What animal is this?",
            "options": ["Dog", "Fish", "Cat"],
            "answer": "Dog"},
        4: {"question": "How is the dog?",
            "options": ["Friendly", "Scary", "Invisible"],
            "answer": "Friendly"},
        5: {"question": "Where do the cat and dog play?",
            "options": ["In the park", "In the car", "In the sky"],
            "answer": "In the park"},
        6: {"question": "What is the weather like?",
            "options": ["Rainy", "Sunny", "Snowy"],
            "answer": "Sunny"},
        7: {"question": "What shines in the sky?",
            "options": ["The moon", "The sun", "A plane"],
            "answer": "The sun"},
        8: {"question": "What do they do after playing?",
            "options": ["Eat and rest", "Go to school", "Fly away"],
            "answer": "Eat and rest"},
        9: {"question": "What time is it in the story?",
            "options": ["Morning", "Afternoon", "Night"],
            "answer": "Night"},
    },
    "Orta": {
        0: {"question": "Where does the cat run?",
            "options": ["In the park", "In the house", "In the car"],
            "answer": "In the park"},
        1: {"question": "Who joins the cat?",
            "options": ["A bird", "A small dog", "A child"],
            "answer": "A small dog"},
        2: {"question": "What do they chase?",
            "options": ["A red ball", "A blue car", "A yellow bird"],
            "answer": "A red ball"},
    },
    "İleri": {
        0: {"question": "When does the clever cat wake up?",
            "options": ["Late at night", "Early in the morning", "At midnight"],
            "answer": "Early in the morning"},
        1: {"question": "Where does the playful dog wait?",
            "options": ["In the big park", "In the kitchen", "On the roof"],
            "answer": "In the big park"},
        2: {"question": "What becomes their treasure?",
            "options": ["A red ball", "A blue book", "A green hat"],
            "answer": "A red ball"},
    }
}

# --- HIKAYE GOSTERIMI ---
if st.session_state.profile["name"]:
    p = st.session_state.profile
    current_story = stories[p["level"]]
    page = p["page"]

    st.markdown(f"### 📖 {p['name']} için hikaye")
    st.markdown(f"**Sayfa {page+1} / 10 - Seviye: {p['level']}**")
    text = current_story[page]
    st.write(text)

    # AI görsel prompt'u
    prompt = build_image_prompt(p["name"], p["level"], page, text)
    st.caption("🔮 AI image prompt (ileride gerçek görsel buradan üretilecek):")
    st.code(prompt, language="text")

    # Seslendirme
    if st.button("🔊 Dinle"):
        tts = gTTS(text, lang='en', slow=True)
        audio = io.BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        st.audio(audio, format="audio/mp3")

    # Mini quiz
    page_quiz = quiz_data.get(p["level"], {}).get(page)
    if page_quiz:
        st.markdown("### ❓ Mini Quiz")
        st.write(page_quiz["question"])

        selected = st.radio(
            "Choose the correct answer:",
            page_quiz["options"],
            key=f"quiz_{p['level']}_{page}"
        )

        if st.button("Cevabı Kontrol Et", key=f"check_{p['level']}_{page}"):
            if selected == page_quiz["answer"]:
                st.success("✅ Correct! Great job!")
                st.session_state.profile["progress"] = min(
                    100, st.session_state.profile["progress"] + 5
                )
                st.session_state.profile["total_correct"] += 1
            else:
                st.error("❌ Not correct. Try again.")

    # Sayfa gezinme
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Önceki Sayfa"):
            if st.session_state.profile["page"] > 0:
                st.session_state.profile["page"] -= 1
                st.rerun()
    with col2:
        if st.button("➡️ Sonraki Sayfa"):
            st.session_state.profile["total_pages_read"] += 1
            if st.session_state.profile["page"] < 9:
                st.session_state.profile["page"] += 1
            else:
                st.session_state.profile["page"] = 0
                st.session_state.profile["progress"] = min(
                    100, st.session_state.profile["progress"] + 10
                )
            st.rerun()

    st.progress(st.session_state.profile["progress"] / 100)
    st.metric("🏆 Toplam İlerleme", f"{st.session_state.profile['progress']}%")

    # Ebeveyn paneli
    with st.expander("👨‍👩‍👧 Parent View / Ebeveyn Görünümü"):
        total_pages = st.session_state.profile.get("total_pages_read", 0)
        total_correct = st.session_state.profile.get("total_correct", 0)

        st.write(f"Toplam okunan sayfa: **{total_pages}**")
        st.write(f"Toplam doğru cevap: **{total_correct}**")

        if total_correct >= 8 and p["level"] == "Başlangıç":
            st.info("Öneri: Çocuğunuz bir üst seviye (Orta) için hazır olabilir.")
        elif total_correct >= 8 and p["level"] == "Orta":
            st.info("Öneri: Çocuğunuz bir üst seviye (İleri) için hazır olabilir.")
        else:
            st.write("Seviye: Şimdilik mevcut seviyede devam etmesi uygun görünüyor.")
else:
    st.info("Önce çocuğun adını ve seviyesini girip butona bas.")

