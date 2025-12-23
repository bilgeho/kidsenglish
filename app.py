import streamlit as st
from gtts import gTTS
import sqlite3
import io
from openai import OpenAI
import base64

# -----------------------------
# OpenAI istemcisi ve görsel üretimi
# -----------------------------
def get_openai_client() -> OpenAI | None:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


@st.cache_data(show_spinner=True)
def generate_image_bytes(prompt: str) -> bytes | None:
    client = get_openai_client()
    if client is None:
        st.warning("OPENAI_API_KEY bulunamadı, demo modunda çalışıyor.")
        return None

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        image_base64 = result.data[0].b64_json
        return base64.b64decode(image_base64)
    except Exception as e:
        st.error(f"Görsel üretim hatası: {e}")
        return None



# -----------------------------
# Yardımcı fonksiyonlar (DB, TTS, prompt)
# -----------------------------
def get_db_connection():
    # content.db proje kökünde duruyor
    return sqlite3.connect("content.db")


def get_sentence(level: str, page: int):
    """
    Seviye + sayfa numarasına göre DB'den cümleyi getirir.
    sentences(level, page, text_en, text_tr)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, text_en, text_tr
        FROM sentences
        WHERE level = ? AND page = ?
        LIMIT 1
        """,
        (level, page),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "text_en": row[1],
        "text_tr": row[2],
    }


def get_question(sentence_id: int):
    """
    Verilen cümle id'sine bağlı soruyu DB'den getirir.
    questions(sentence_id, question, option_a, option_b, option_c, correct_opt)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT question, option_a, option_b, option_c, correct_opt
        FROM questions
        WHERE sentence_id = ?
        LIMIT 1
        """,
        (sentence_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "text": row[0],
        "options": [row[1], row[2], row[3]],
        "correct": row[4],  # "A" / "B" / "C"
    }


def build_image_prompt(child_name: str, level: str, page: int, base_text: str) -> str:
    """
    Görsel üretim modeli için prompt.
    """
    level_desc = {
        "Başlangıç": "very simple, clear shapes, for kids aged 4-6",
        "Orta": "slightly more detailed, for kids aged 7-9",
        "İleri": "richer scenes with more details, for kids aged 9-11",
    }.get(level, "children's book style")

    page_moods = [
        "bright morning scene",
        "playful action scene",
        "focused searching scene",
        "surprised reaction scene",
        "happy sharing moment",
        "calm resting scene",
    ]
    mood = page_moods[(page - 1) % len(page_moods)]

    prompt = (
        f"Illustration for a kids English story. "
        f"Child name: {child_name}. "
        f"Story text: '{base_text}'. "
        f"Style: {level_desc}. "
        f"Scene mood: {mood}."
    )
    return prompt


def tts_from_text(text: str, lang: str = "en") -> bytes:
    """
    gTTS ile metni sese çevirir, raw bytes döner.
    """
    tts = gTTS(text=text, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


# -----------------------------
# Streamlit uygulaması
# -----------------------------
st.set_page_config(page_title="Kids English Story", page_icon="🧒", layout="wide")

st.markdown("<h1 style='text-align: center;'>🧒 Kids English Story</h1>", unsafe_allow_html=True)
st.write("Çocuğun adı ve seviyesini seç, sonra hikâyeyi başlat.")


# Profil oluşturma / demo başlatma
if "profile" not in st.session_state:
    with st.form("profile_form"):
        child_name = st.text_input("Çocuk Adı:", value="Duru")
        level = st.selectbox("Seviye", ["Başlangıç", "Orta", "İleri"])
        submitted = st.form_submit_button("Hikayeyi Başlat")

    if submitted:
        st.session_state.profile = {
            "name": child_name.strip() or "Duru",
            "level": level,
        }
        st.session_state.page = 1
        st.rerun()

else:
    profile = st.session_state.profile
    name = profile["name"]
    level = profile["level"]
    page_no = st.session_state.get("page", 1)

    # -------------------------
    # Hikaye cümlesini DB'den çek
    # -------------------------
    sentence = get_sentence(level, page_no)

    if sentence is None:
        st.warning("Bu seviye/sayfa için henüz cümle eklenmedi.")
        story_text = ""
    else:
        story_text = sentence["text_en"]

    # Üst bilgi
    st.markdown(f"### 📖 {name} için hikaye")
    st.caption(f"Sayfa {page_no} – Seviye: {level}")

    # Hikaye metni
    st.markdown(f"**{story_text}**")

    # -------------------------
    # AI ile hikaye görseli
    # -------------------------
    if story_text:
        image_prompt = build_image_prompt(name, level, page_no, story_text)

        # DEBUG satirleri
        st.write("DEBUG: image_prompt hazir")

        img_bytes = generate_image_bytes(image_prompt)

        if img_bytes:
            st.image(img_bytes, caption="AI illustration", use_container_width=True)
        else:
            st.write("DEBUG: img_bytes None")

    # -------------------------
    # Mini Quiz
    # -------------------------
    if sentence is not None:
        q = get_question(sentence["id"])
    else:
        q = None

    if q:
        st.markdown("### 🧠 Mini Quiz")
        options = q["options"]
        label_map = {"A": options[0], "B": options[1], "C": options[2]}

        answer = st.radio(
            q["text"],
            options,
            index=None,
            key=f"quiz_{sentence['id']}_{page_no}",
        )

        if answer:
            chosen_letter = [k for k, v in label_map.items() if v == answer][0]
            if chosen_letter == q["correct"]:
                st.success("Great job! 🎉")
            else:
                st.info("Tekrar deneyelim 🙂")

    # -------------------------
    # Seslendirme
    # -------------------------
    if story_text:
        if st.button("🔊 Dinle"):
            audio_bytes = tts_from_text(story_text, lang="en")
            st.audio(audio_bytes, format="audio/mp3")

    # -------------------------
    # Görsel prompt (metin olarak)
    # -------------------------
    with st.expander("AI Görsel Prompt (demo)"):
        image_prompt = build_image_prompt(name, level, page_no, story_text)
        st.code(image_prompt, language="text")

    # -------------------------
    # Sayfa navigasyonu
    # -------------------------
    col_prev, col_next = st.columns(2)

    with col_prev:
        if st.button("⬅️ Önceki Sayfa", disabled=page_no <= 1):
            st.session_state.page = max(1, page_no - 1)
            st.rerun()

    with col_next:
        if st.button("➡️ Sonraki Sayfa"):
            st.session_state.page = page_no + 1
            st.rerun()
