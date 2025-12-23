import streamlit as st
from gtts import gTTS
import sqlite3
import io
import base64  # Şu an aktif kullanılmıyor ama kalsın

from huggingface_hub import InferenceClient
import os

# -----------------------------
# Hugging Face istemcisi
# -----------------------------
HF_TOKEN = os.environ.get("HF_TOKEN")

hf_client = InferenceClient(
    token=HF_TOKEN,  # HF access token
)


def generate_image(image_prompt: str):
    """
    Hugging Face üzerinden text-to-image görsel üretir.
    PIL.Image döndürür; hata olursa None.
    """
    try:
        st.write("DEBUG: image_prompt hazir")
        image = hf_client.text_to_image(
            image_prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )
        return image
    except Exception as e:
        st.error(f"Görsel üretim hatası: {e}")
        return None


# -----------------------------
# DB şeması ve bağlantı
# -----------------------------
def init_db():
    conn = sqlite3.connect("content.db")
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS children (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_email  TEXT,
            name          TEXT NOT NULL,
            level         TEXT NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progress (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id     INTEGER NOT NULL,
            sentence_id  INTEGER NOT NULL,
            is_completed INTEGER NOT NULL DEFAULT 0,
            quiz_answer  TEXT,
            is_correct   INTEGER,
            answered_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id)    REFERENCES children(id),
            FOREIGN KEY (sentence_id) REFERENCES sentences(id)
        );
        """
    )
    conn.commit()
    conn.close()


def get_db_connection():
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


def get_or_create_child(name: str, level: str, parent_email: str | None = None) -> int:
    """
    Aynı isim + level için çocuk varsa onu döner, yoksa yeni kayıt oluşturur.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id FROM children
        WHERE name = ? AND level = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (name, level),
    )
    row = cur.fetchone()
    if row:
        child_id = row[0]
    else:
        cur.execute(
            """
            INSERT INTO children (parent_email, name, level)
            VALUES (?, ?, ?)
            """,
            (parent_email, name, level),
        )
        child_id = cur.lastrowid
        conn.commit()

    conn.close()
    return child_id


def save_progress(
    child_id: int,
    sentence_id: int,
    is_completed: int,
    quiz_answer: str | None,
    is_correct: int | None,
):
    """
    Çocuğun bir cümle/sayfadaki ilerlemesini kaydeder.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO progress
        (child_id, sentence_id, is_completed, quiz_answer, is_correct)
        VALUES (?, ?, ?, ?, ?)
        """,
        (child_id, sentence_id, is_completed, quiz_answer, is_correct),
    )
    conn.commit()
    conn.close()


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
init_db()  # Tablolar yoksa oluştur

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
        name_clean = child_name.strip() or "Duru"
        # parent_email şimdilik None, ileride login eklenirse doldurulur
        child_id = get_or_create_child(name_clean, level)

        st.session_state.profile = {
            "id": child_id,
            "name": name_clean,
            "level": level,
        }
        st.session_state.page = 1
        st.rerun()

else:
    profile = st.session_state.profile
    child_id = profile.get("id")
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

        image = generate_image(image_prompt)

        if image is not None:
            st.image(image, caption="AI illustration", use_container_width=True)
        else:
            st.write("DEBUG: image None")

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
            is_correct = 1 if chosen_letter == q["correct"] else 0

            if child_id is not None and sentence is not None:
                save_progress(
                    child_id=child_id,
                    sentence_id=sentence["id"],
                    is_completed=1,
                    quiz_answer=chosen_letter,
                    is_correct=is_correct,
                )

            if is_correct:
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
