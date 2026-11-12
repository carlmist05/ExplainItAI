import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from google import genai

# ============================================================
# ExplainIt AI — beginner-friendly AI learning assistant
# ============================================================

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "chat_history.db"
MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="ExplainIt AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------- Styling --------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: #1E293B !important;
        color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"] {
        background: #273449 !important;
        border-right: 1px solid #475569;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] li {
        color: #E2E8F0 !important;
    }
    .hero {
        background: linear-gradient(125deg, #263B57 0%, #0755B8 58%, #087EAA 100%);
        padding: 2.4rem;
        border: 1px solid rgba(147, 197, 253, .28);
        border-radius: 22px;
        margin-bottom: 1.7rem;
        box-shadow: 0 12px 30px rgba(2, 8, 23, .20);
    }
    .section-intro { color: #CBD5E1 !important; font-size: 1rem; line-height: 1.65; }
    .stTabs [data-baseweb="tab-list"] { gap: .5rem; }
    .stTabs [data-baseweb="tab"] { background: #334155; border-radius: 9px 9px 0 0; padding: .6rem 1rem; }
    div[data-testid="stMetric"] { background: #334155; border: 1px solid #475569; padding: 1rem; border-radius: 13px; }
    div[data-testid="stAlert"] { border-radius: 12px; }
    div[data-testid="stForm"] { background: #273449; border: 1px solid #475569; padding: 1rem; border-radius: 14px; }
    .hero h1 {
        color: #FFFFFF !important;
        font-size: 2.25rem;
        line-height: 1.25;
    }
    .hero p {
        color: #E2E8F0 !important;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    h1, h2, h3, h4, p, li, label {
        color: #F1F5F9;
    }
    [data-testid="stWidgetLabel"] p {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] > div {
        background: #334155 !important;
        border: 1px solid #64748B !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #F1F5F9 !important;
        -webkit-text-fill-color: #F1F5F9 !important;
    }
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        background: #334155 !important;
        color: #F1F5F9 !important;
        -webkit-text-fill-color: #F1F5F9 !important;
        border: 1px solid #64748B !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextInput"] input::placeholder {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
    }
    div.stButton > button,
    div.stDownloadButton > button {
        background: #1685F8 !important;
        color: white !important;
        border: 1px solid #1685F8 !important;
        border-radius: 10px !important;
        font-weight: 650 !important;
        min-height: 42px;
    }
    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background: #0968D8 !important;
        border-color: #0968D8 !important;
    }
    .feature-card {
        background: #334155;
        border: 1px solid #475569;
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: .7rem;
    }
    .muted {
        color: #CBD5E1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------- API configuration -------------------
def get_api_key():
    """Read the key from Streamlit Secrets first, then environment."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("GEMINI_API_KEY", "")


def get_client():
    key = get_api_key()
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


# ----------------------- Chat database ----------------------
def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                study_mode TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def save_chat(question, answer, study_mode):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_history (question, answer, study_mode, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                question,
                answer,
                study_mode,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


def get_all_chats():
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, question, answer, study_mode, created_at
            FROM chat_history ORDER BY id DESC
            """
        ).fetchall()


def get_chat(chat_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, question, answer, study_mode, created_at
            FROM chat_history WHERE id = ?
            """,
            (chat_id,),
        ).fetchone()


def delete_chat(chat_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE id = ?", (chat_id,))


def clear_all_chats():
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history")


def save_bookmark(question, answer):
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT id FROM bookmarks WHERE question = ? AND answer = ?", (question, answer)
        ).fetchone()
        if exists:
            return False
        conn.execute(
            "INSERT INTO bookmarks (question, answer, created_at) VALUES (?, ?, ?)",
            (question, answer, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return True


def get_bookmarks():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, question, answer, created_at FROM bookmarks ORDER BY id DESC"
        ).fetchall()


def delete_bookmark(bookmark_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))


def save_study_note(title, content):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO study_notes (title, content, updated_at) VALUES (?, ?, ?)",
            (title, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def get_study_notes():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, title, content, updated_at FROM study_notes ORDER BY id DESC"
        ).fetchall()


def delete_study_note(note_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM study_notes WHERE id = ?", (note_id,))


initialize_database()

# ------------------------- Session state --------------------
defaults = {
    "answer": "",
    "last_question": "",
    "last_study_mode": "Explain simply",
    "quiz_data": None,
    "quiz_topic": "",
    "quiz_submitted": False,
    "quiz_score": None,
    "explanation_level": "Beginner",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------- Sidebar --------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.65rem;font-weight:800;color:#93C5FD;">📚 ExplainIt AI</div>',
        unsafe_allow_html=True,
    )
    st.caption("Your personal learning companion")
    page = st.radio(
        "🧭 Navigation",
        ["🏠 Home", "📚 Learning history", "🔖 Bookmarks", "📝 Study notes", "🎓 Quiz generator", "ℹ️ About"],
        label_visibility="visible",
    )
    st.divider()
    st.markdown("### ✨ What you can do")
    st.markdown(
        """
        - Understand difficult topics
        - Learn with practical examples
        - Get step-by-step explanations
        - Generate practice quizzes
        - Listen to explanations
        - Download notes for revision
        """
    )
    st.divider()
    st.caption("Made for curious minds 💙")


# --------------------------- Home ---------------------------
if page == "🏠 Home":
    st.markdown(
        """
        <div class="hero">
          <h1>Learn anything. Understand everything. ✨</h1>
          <p>Confused about a topic? Ask ExplainIt AI. Get simple explanations,
          practical examples, and step-by-step guidance to support your learning.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("What would you like to learn?")
    st.markdown('<p class="muted">Enter a question below and choose how you want to learn.</p>',
                unsafe_allow_html=True)

    learning_style = st.selectbox(
        "Choose your learning style",
        [
            "Explain simply",
            "Step-by-step explanation",
            "Use practical examples",
            "Summarize the topic",
            "Explain programming code",
        ],
        key="learning_style",
    )
    explanation_level = st.selectbox(
        "Explanation level",
        ["Beginner", "Intermediate", "Advanced"],
        help="Choose how much background knowledge the explanation should assume.",
        key="explanation_level",
    )
    question = st.text_area(
        "Your question",
        value=st.session_state.last_question if st.session_state.last_question else "",
        placeholder="Example: Explain variables in Python as if I am a beginner...",
        height=130,
        max_chars=3000,
        key="question_input",
        label_visibility="collapsed",
    )

    st.markdown("**Need an idea? Try one of these:**")

    def set_suggested_question(text):
        st.session_state["question_input"] = text

    idea_cols = st.columns(3)
    ideas = [
        ("🐍 Python basics", "Explain Python variables to me as a beginner, using simple examples."),
        ("📊 Statistics", "Explain mean, median, and mode with a simple example."),
        ("💻 Computer networks", "Explain what a computer network is and give everyday examples."),
    ]
    for col, (label, idea) in zip(idea_cols, ideas):
        with col:
            st.button(
                label,
                use_container_width=True,
                on_click=set_suggested_question,
                args=(idea,),
            )

    if st.button("✨ Explain with AI", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Please type a question first.")
        else:
            client = get_client()
            if client is None:
                st.error(
                    "AI access is not configured. In Streamlit Community Cloud, open "
                    "Manage app → Settings → Secrets and add "
                    '`GEMINI_API_KEY = "your-key"`.'
                )
            else:
                mode_instructions = {
                    "Explain simply": "Use beginner-friendly language and define unfamiliar words.",
                    "Step-by-step explanation": "Explain in numbered, logical steps.",
                    "Use practical examples": "Use practical everyday examples and explain each one.",
                    "Summarize the topic": "Give a concise summary with key takeaways.",
                    "Explain programming code": "Explain the code line by line, with a small example if useful.",
                }
                prompt = f"""
You are ExplainIt AI, a patient learning assistant.
Answer the learner's question accurately and clearly.
Learning style: {learning_style}
Explanation level: {explanation_level}
Adapt vocabulary, depth, and assumed background knowledge to the selected level.
Instructions for this style: {mode_instructions[learning_style]}
Use headings and examples where helpful. If the question is ambiguous, state your assumption.
Question: {question.strip()}
"""
                try:
                    with st.spinner("ExplainIt AI is preparing your explanation..."):
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=prompt,
                        )
                    answer = (response.text or "").strip()
                    if not answer:
                        st.error("The AI returned an empty response. Please try again.")
                    else:
                        st.session_state.answer = answer
                        st.session_state.last_question = question.strip()
                        st.session_state.last_study_mode = learning_style
                        save_chat(question.strip(), answer, learning_style)
                        st.success("Your explanation has been saved to learning history.")
                except Exception as exc:
                    error_text = str(exc).lower()
                    if "503" in error_text or "unavailable" in error_text or "high demand" in error_text:
                        st.warning("Gemini is temporarily busy. Please wait a minute and try again.")
                    elif "429" in error_text or "quota" in error_text or "rate" in error_text:
                        st.warning("The AI service has reached a temporary usage limit. Please try again later.")
                    else:
                        st.error("The explanation could not be generated. Please check the app configuration or try again later.")
                    # Keep provider error details out of the public interface.
                    st.caption("If the problem continues, the app owner can review the deployment logs.")

    if st.session_state.answer:
        st.divider()
        st.subheader("📖 Your explanation")
        st.markdown(st.session_state.answer)
        if st.button("🔖 Save this explanation to bookmarks", use_container_width=True):
            added = save_bookmark(st.session_state.last_question, st.session_state.answer)
            if added:
                st.success("Saved to bookmarks.")
            else:
                st.info("This explanation is already bookmarked.")

        safe_filename = "explainit_ai_notes.txt"
        download_text = (
            f"ExplainIt AI Notes\n"
            f"Question: {st.session_state.last_question}\n"
            f"Learning style: {st.session_state.last_study_mode}\n\n"
            f"{st.session_state.answer}\n"
        )
        st.download_button(
            "📄 Download explanation (.txt)",
            data=download_text,
            file_name=safe_filename,
            mime="text/plain",
            use_container_width=True,
        )

        st.markdown("### 🔊 Listen to the explanation")
        st.caption("Uses your browser's built-in speech voice. Voice availability depends on your browser and device.")
        speech_payload = json.dumps(st.session_state.answer)
        components.html(
            f"""
            <div style="font-family:Arial,sans-serif;color:#F1F5F9;background:#334155;padding:14px;border-radius:12px;">
              <button id="play" style="background:#1685F8;color:white;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;">▶ Read aloud</button>
              <button id="stop" style="background:#475569;color:white;border:0;border-radius:8px;padding:10px 16px;margin-left:8px;cursor:pointer;">■ Stop</button>
              <span id="status" style="margin-left:10px;font-size:13px;">Ready</span>
            </div>
            <script>
              const textToRead = {speech_payload};
              const statusEl = document.getElementById("status");
              document.getElementById("play").onclick = () => {{
                if (!("speechSynthesis" in window)) {{
                  statusEl.textContent = "Speech is not supported in this browser.";
                  return;
                }}
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(textToRead);
                utterance.rate = 0.95;
                utterance.onstart = () => statusEl.textContent = "Reading...";
                utterance.onend = () => statusEl.textContent = "Finished";
                window.speechSynthesis.speak(utterance);
              }};
              document.getElementById("stop").onclick = () => {{
                if ("speechSynthesis" in window) window.speechSynthesis.cancel();
                statusEl.textContent = "Stopped";
              }};
            </script>
            """,
            height=85,
        )

# ---------------------- Learning history --------------------
elif page == "📚 Learning history":
    st.title("📚 Learning history")
    st.write("Reopen a previous explanation, or delete entries you no longer need.")
    st.info(
        "History is stored in this app's SQLite database. On Streamlit Community Cloud, "
        "local files may not survive every restart/redeployment. This version is best for "
        "a demo; durable multi-user history needs a persistent database."
    )
    chats = get_all_chats()
    if not chats:
        st.info("No saved explanations yet. Ask a question on the Home page first.")
    else:
        labels = {
            f"{row[4]} — {row[1][:65]}": row[0]
            for row in chats
        }
        chosen_label = st.selectbox("Saved explanations", list(labels.keys()))
        chosen_id = labels[chosen_label]
        selected = get_chat(chosen_id)
        if selected:
            st.markdown(f"**Question:** {selected[1]}")
            st.caption(f"Learning style: {selected[3]} · Saved: {selected[4]}")
            st.markdown("### Explanation")
            st.markdown(selected[2])
            st.download_button(
                "📄 Download this explanation",
                data=f"Question: {selected[1]}\n\n{selected[2]}",
                file_name=f"explainit_history_{selected[0]}.txt",
                mime="text/plain",
            )
            if st.button("🗑️ Delete this explanation"):
                delete_chat(chosen_id)
                st.success("Explanation deleted.")
                st.rerun()
        with st.expander("Danger zone: clear all learning history"):
            st.warning("This permanently deletes every entry in this app's local database.")
            confirm = st.checkbox("I understand and want to delete all history.")
            if st.button("Clear all history", disabled=not confirm):
                clear_all_chats()
                st.success("History cleared.")
                st.rerun()

# -------------------------- Bookmarks ------------------------
elif page == "🔖 Bookmarks":
    st.title("🔖 Bookmarked explanations")
    st.markdown('<p class="section-intro">Keep useful explanations close by for quick revision.</p>', unsafe_allow_html=True)
    st.info("This demo stores bookmarks in a shared app database. Do not save private or sensitive information here.")
    bookmarks = get_bookmarks()
    if not bookmarks:
        st.info("You have not bookmarked any explanations yet. Open an explanation on Home and select Save to bookmarks.")
    else:
        st.caption(f"You have {len(bookmarks)} bookmarked explanation(s).")
        for bookmark in bookmarks:
            with st.expander(bookmark[1][:100] or "Saved explanation"):
                st.caption(f"Saved: {bookmark[3]}")
                st.markdown(bookmark[2])
                st.download_button(
                    "📄 Download bookmark",
                    data=f"Question: {bookmark[1]}\n\n{bookmark[2]}",
                    file_name=f"explainit_bookmark_{bookmark[0]}.txt",
                    mime="text/plain",
                    key=f"download_bookmark_{bookmark[0]}",
                )
                if st.button("Remove bookmark", key=f"delete_bookmark_{bookmark[0]}"):
                    delete_bookmark(bookmark[0])
                    st.rerun()

# --------------------------- Study notes ---------------------
elif page == "📝 Study notes":
    st.title("📝 My study notes")
    st.markdown('<p class="section-intro">Write and save your own revision notes.</p>', unsafe_allow_html=True)
    st.info("This demo stores notes in a shared app database. Do not enter private or sensitive information.")
    with st.form("new_note_form", clear_on_submit=True):
        note_title = st.text_input("Note title", max_chars=100, placeholder="e.g. Introduction to computer networks")
        note_content = st.text_area("Your notes", max_chars=10000, height=180, placeholder="Write the important points you want to remember...")
        save_note = st.form_submit_button("💾 Save study note", use_container_width=True)
    if save_note:
        if not note_title.strip() or not note_content.strip():
            st.warning("Enter both a title and note content.")
        else:
            save_study_note(note_title.strip(), note_content.strip())
            st.success("Your study note has been saved.")
            st.rerun()
    st.divider()
    st.subheader("Saved notes")
    notes = get_study_notes()
    if not notes:
        st.info("No study notes yet. Create your first note above.")
    else:
        for note in notes:
            with st.expander(note[1]):
                st.caption(f"Saved: {note[3]}")
                st.markdown(note[2])
                st.download_button(
                    "📄 Download note",
                    data=f"{note[1]}\n\n{note[2]}",
                    file_name=f"explainit_note_{note[0]}.txt",
                    mime="text/plain",
                    key=f"download_note_{note[0]}",
                )
                if st.button("Delete note", key=f"delete_note_{note[0]}"):
                    delete_study_note(note[0])
                    st.rerun()

# ------------------------ Quiz generator --------------------
elif page == "🎓 Quiz generator":
    st.title("🎓 Quiz generator")
    st.write("Create a short multiple-choice quiz to check your understanding.")

    quiz_topic = st.text_input(
        "What topic would you like a quiz about?",
        placeholder="Example: Python variables, probability, computer networks",
        value=st.session_state.quiz_topic,
        max_chars=200,
    )
    difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    number_questions = st.select_slider("Number of questions", options=[3, 5, 8, 10], value=5)

    if st.button("✨ Generate quiz", use_container_width=True):
        if not quiz_topic.strip():
            st.warning("Enter a topic first.")
        else:
            client = get_client()
            if client is None:
                st.error(
                    "AI access is not configured. Add GEMINI_API_KEY in Streamlit app Secrets."
                )
            else:
                prompt = f"""
Create {number_questions} multiple-choice quiz questions about: {quiz_topic.strip()}.
Difficulty: {difficulty}.
Return ONLY valid JSON (no markdown fences) in this exact format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["A. option", "B. option", "C. option", "D. option"],
      "answer": 0,
      "explanation": "Short explanation of the correct answer"
    }}
  ]
}}
The answer must be an integer index from 0 to 3. Exactly four options per question.
Keep the questions educational, clear, and factually correct.
"""
                try:
                    with st.spinner("Creating your quiz..."):
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=prompt,
                        )
                    raw = (response.text or "").strip()
                    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    quiz = json.loads(raw)
                    questions = quiz.get("questions", [])
                    valid = (
                        len(questions) > 0
                        and all(
                            isinstance(q.get("question"), str)
                            and isinstance(q.get("options"), list)
                            and len(q["options"]) == 4
                            and isinstance(q.get("answer"), int)
                            and 0 <= q["answer"] <= 3
                            for q in questions
                        )
                    )
                    if not valid:
                        raise ValueError("The AI response did not match the expected quiz format.")
                    st.session_state.quiz_data = quiz
                    st.session_state.quiz_topic = quiz_topic.strip()
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_score = None
                    st.rerun()
                except Exception:
                    st.error("The quiz could not be generated. Please try again later or check the deployment logs.")

    if st.session_state.quiz_data:
        st.divider()
        st.subheader(f"Quiz: {st.session_state.quiz_topic}")
        with st.form("quiz_form"):
            selections = []
            for i, q in enumerate(st.session_state.quiz_data["questions"]):
                st.markdown(f"**{i + 1}. {q['question']}**")
                selection = st.radio(
                    f"Choose an answer for question {i + 1}",
                    options=list(range(4)),
                    format_func=lambda idx, opts=q["options"]: opts[idx],
                    key=f"quiz_answer_{i}",
                    index=None,
                    label_visibility="collapsed",
                )
                selections.append(selection)
            submitted = st.form_submit_button("Check my answers")
        if submitted:
            score = 0
            for q, selection in zip(st.session_state.quiz_data["questions"], selections):
                if selection == q["answer"]:
                    score += 1
            st.session_state.quiz_submitted = True
            st.session_state.quiz_score = (score, len(selections))
        if st.session_state.quiz_submitted:
            score, total = st.session_state.quiz_score
            st.success(f"You scored {score} out of {total}.")
            for i, q in enumerate(st.session_state.quiz_data["questions"]):
                st.markdown(f"**{i + 1}. {q['question']}**")
                st.write(f"Correct answer: {q['options'][q['answer']]}")
                st.write(f"Why: {q.get('explanation', 'Review this topic for more detail.')}")
                st.divider()
            if st.button("Create another quiz"):
                st.session_state.quiz_data = None
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = None
                st.rerun()

# ---------------------------- About -------------------------
elif page == "ℹ️ About":
    st.title("ℹ️ About ExplainIt AI")
    st.markdown(
        """
        ExplainIt AI is a beginner-friendly learning assistant designed to help learners
        understand difficult concepts using simple explanations, step-by-step guidance,
        practical examples, summaries, and programming help.

        **Features**
        - AI-powered explanations using Gemini
        - Learning history saved in a local SQLite database
        - Bookmarked explanations for revision
        - Personal study notes
        - Beginner, intermediate, and advanced explanation levels
        - Multiple-choice quiz generation
        - Browser-based text-to-speech
        - Downloadable notes for offline revision

        **Privacy and hosting**
        - Do not enter passwords, API keys, or other sensitive information as questions.
        - The Gemini API key should be stored in Streamlit Community Cloud Secrets.
        - This demo's SQLite history is local to the running app and is not a durable,
          private per-user cloud database.
        """
    )
    st.caption("Built with Python, Streamlit, SQLite, and the Google Gen AI SDK.")
