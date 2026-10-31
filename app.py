import os
import sqlite3
import streamlit as st
from google import genai
from pathlib import Path

# ==========================================
# PERMANENT CHAT HISTORY DATABASE
# ==========================================

# Store the database in the project folder.
DB_PATH = Path(__file__).resolve().parent / "chat_history.db"


def get_connection():
    """Connect to the local SQLite database."""
    return sqlite3.connect(DB_PATH)


def initialize_database():
    """Create the history table if it does not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                study_mode TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (
                    datetime('now', 'localtime')
                )
            )
        """)


def save_chat(question, answer, study_mode):
    """Save a question and its AI answer permanently."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_history
                (question, answer, study_mode)
            VALUES (?, ?, ?)
            """,
            (question, answer, study_mode)
        )


def get_all_chats():
    """Return saved conversations, newest first."""
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, question, answer, study_mode, created_at
            FROM chat_history
            ORDER BY id DESC
        """).fetchall()


def get_chat(chat_id):
    """Retrieve one saved conversation."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT id, question, answer, study_mode, created_at
            FROM chat_history
            WHERE id = ?
            """,
            (chat_id,)
        ).fetchone()


def delete_chat(chat_id):
    """Delete one conversation."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_history WHERE id = ?",
            (chat_id,)
        )


def clear_all_chats():
    """Delete every saved conversation."""
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history")


# Create the database when the app starts.
initialize_database()

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="ExplainIt AI | Smart Learning",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM DESIGN AND COLOURS
# ==========================================

st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #1E293B !important;
        color: #F1F5F9 !important;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #273449 !important;
        border-right: 1px solid #475569;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] li {
        color: #E2E8F0 !important;
    }

    .brand {
        font-size: 1.7rem;
        font-weight: 800;
        color: #93C5FD !important;
    }

    .brand-caption {
        color: #CBD5E1 !important;
        margin-bottom: 2rem;
    }

    /* HEADER */
    .hero {
        background: linear-gradient(
            135deg,
            #334155,
            #1D4ED8
        ) !important;
        padding: 2.5rem;
        border-radius: 22px;
        margin-bottom: 2rem;
    }

    .hero h1 {
        color: #FFFFFF !important;
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.3;
    }

    .hero p {
        color: #E2E8F0 !important;
        font-size: 1.05rem;
        line-height: 1.8;
    }

    /* SECTION HEADINGS */
    .section-title {
        font-size: 1.4rem;
        font-weight: 750;
        color: #F1F5F9 !important;
        margin-top: 1.5rem;
        margin-bottom: 0.6rem;
    }

    .section-caption {
        color: #CBD5E1 !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* FORM LABELS */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }

    /* LEARNING-STYLE DROPDOWN */
    div[data-baseweb="select"] > div {
        background-color: #334155 !important;
        border: 1px solid #64748B !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #F1F5F9 !important;
        -webkit-text-fill-color: #F1F5F9 !important;
    }

    div[data-baseweb="select"] svg {
        fill: #93C5FD !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="menu"] {
        background-color: #334155 !important;
    }

    li[role="option"] {
        background-color: #334155 !important;
        color: #F1F5F9 !important;
    }

    li[role="option"]:hover {
        background-color: #475569 !important;
        color: #FFFFFF !important;
    }

    /* QUESTION BOX */
    div[data-testid="stTextArea"] textarea {
        background-color: #334155 !important;
        color: #F1F5F9 !important;
        -webkit-text-fill-color: #F1F5F9 !important;
        border: 1px solid #64748B !important;
        border-radius: 12px !important;
    }

    div[data-testid="stTextArea"] textarea::placeholder {
        color: #CBD5E1 !important;
        -webkit-text-fill-color: #CBD5E1 !important;
    }

    /* BUTTONS */
    div.stButton > button {
        background-color: #3B82F6 !important;
        color: #FFFFFF !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 10px !important;
        min-height: 45px;
        font-weight: 600;
    }

    div.stButton > button p {
        color: #FFFFFF !important;
    }

    div.stButton > button:hover {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }

    /* FEATURE CARDS */
    .feature-card {
        background-color: #334155 !important;
        padding: 1.3rem;
        border-radius: 16px;
        border: 1px solid #475569;
        min-height: 125px;
        margin-bottom: 0.5rem;
    }

    .feature-title {
        color: #F1F5F9 !important;
        font-weight: 700;
    }

    .feature-description {
        color: #CBD5E1 !important;
        line-height: 1.6;
    }

    /* AI ANSWER TEXT */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] strong {
        color: #F1F5F9 !important;
    }

    /* CODE EXAMPLES */
    div[data-testid="stMarkdownContainer"] code {
        background-color: #475569 !important;
        color: #FCA5A5 !important;
        border-radius: 4px;
        padding: 2px 5px;
    }

    div[data-testid="stMarkdownContainer"] pre {
        background-color: #0F172A !important;
        border: 1px solid #475569;
        border-radius: 10px;
        padding: 1rem;
        overflow-x: auto;
    }

    div[data-testid="stMarkdownContainer"] pre code {
        background-color: transparent !important;
        color: #E2E8F0 !important;
    }

    /* ANSWER CONTAINER */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #334155 !important;
        border-color: #475569 !important;
        border-radius: 16px;
    }

    /* FOOTER */
    .footer {
        text-align: center;
        color: #CBD5E1 !important;
        font-size: 0.9rem;
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================

if "question" not in st.session_state:
    st.session_state.question = ""

if "answer" not in st.session_state:
    st.session_state.answer = ""

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.markdown(
        '<div class="brand">📚 ExplainIt AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-caption">'
        'Your personal learning companion'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("### 🧭 Navigation")

    page = st.radio(
        "Choose a page",
        ["🏠 Home", "📖 About"],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### ✨ What you can do")

    st.markdown("""
    - Understand difficult topics
    - Learn with practical examples
    - Get step-by-step explanations
    - Summarize topics
    - Understand programming code
    """)

    st.divider()

    # ======================================
    # SAVED CHAT HISTORY
    # ======================================

    st.divider()

    st.markdown("### 💾 Chat History")

    saved_chats = get_all_chats()

    if saved_chats:

        # Display saved questions in a dropdown.
        chat_options = {
            f"#{chat[0]} - {chat[1][:45]}": chat[0]
            for chat in saved_chats
        }

        selected_label = st.selectbox(
            "Previous conversations",
            options=list(chat_options.keys()),
            key="history_selector"
        )

        selected_id = chat_options[selected_label]

        if st.button(
            "📖 Open conversation",
            use_container_width=True
        ):
            selected_chat = get_chat(selected_id)

            if selected_chat:
                st.session_state.answer = selected_chat[2]
                st.session_state.last_question = selected_chat[1]
                st.session_state.question = selected_chat[1]
                st.session_state.last_study_mode = selected_chat[3]

                st.session_state.history_loaded = True

                st.rerun()

        if st.button(
            "🗑️ Delete selected conversation",
            use_container_width=True
        ):
            delete_chat(selected_id)

            st.session_state.answer = ""
            st.session_state.last_question = ""
            st.session_state.question = ""

            st.rerun()

        # Clear all saved conversations.
        if st.button(
            "🧹 Clear all history",
            use_container_width=True
        ):
            st.session_state.confirm_clear_history = True

        if st.session_state.get("confirm_clear_history", False):

            st.warning(
                "This will permanently delete all saved conversations."
            )

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button("Yes, delete"):
                    clear_all_chats()

                    st.session_state.answer = ""
                    st.session_state.last_question = ""
                    st.session_state.question = ""
                    st.session_state.confirm_clear_history = False

                    st.rerun()

            with cancel_col:
                if st.button("Cancel"):
                    st.session_state.confirm_clear_history = False
                    st.rerun()

    else:
        st.caption("Your saved conversations will appear here.")

    st.caption("Made for curious minds 💜")

# ==========================================
# ABOUT PAGE
# ==========================================

if page == "📖 About":

    st.title("📖 About ExplainIt AI")

    st.write("""
    ExplainIt AI is a learning assistant designed to help
    students understand difficult concepts using artificial
    intelligence.
    """)

    st.subheader("🎯 Our mission")

    st.write("""
    Make learning easier by turning complex ideas into
    understandable explanations.
    """)

    st.subheader("👨‍🎓 Who is it for?")

    st.write("""
    University students, programming beginners, and anyone
    who wants to learn something new.
    """)

    st.subheader("🛠️ Technology")

    st.markdown("""
    - Python
    - Streamlit
    - Google Gen AI SDK
    - Gemma model integration
    """)

    st.info(
        "AI-generated information can be incorrect. "
        "Verify important information using reliable sources."
    )

# ==========================================
# HOME PAGE
# ==========================================

else:

    # Welcome banner
    st.markdown("""
    <div class="hero">
        <h1>Learn anything. Understand everything. ✨</h1>
        <p>
            Confused about a topic? Ask ExplainIt AI.
            Get simple explanations, practical examples,
            and step-by-step guidance to support your learning.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">'
        'What would you like to learn?'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-caption">'
        'Enter a question below and choose how you want to learn.'
        '</div>',
        unsafe_allow_html=True
    )

    # Study modes
    study_mode = st.selectbox(
    "Choose your learning style",
    [
        "Explain simply",
        "Explain step by step",
        "Give practical examples",
        "Summarize a topic",
        "Help me understand code",
        "Generate a quiz",
        "Create revision questions"
    ]
)

    # Question input
    question = st.text_area(
        "Your question",
        value=st.session_state.question,
        placeholder=(
            "Example: Explain variables in Python "
            "as if I am a beginner..."
        ),
        height=140,
        label_visibility="collapsed"
    )

    # Example questions
    st.markdown("**Need an idea? Try one of these:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "🐍 Python basics",
            use_container_width=True
        ):
            st.session_state.question = (
                "Explain Python variables to a beginner."
            )
            st.rerun()

    with col2:
        if st.button(
            "📊 Statistics",
            use_container_width=True
        ):
            st.session_state.question = (
                "Explain probability in simple English "
                "with an example."
            )
            st.rerun()

    with col3:
        if st.button(
            "💻 Computer networks",
            use_container_width=True
        ):
            st.session_state.question = (
                "Explain how computer networks work "
                "with a simple example."
            )
            st.rerun()

    # ======================================
    # AI CONNECTION
    # ======================================

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        st.error(
            "AI access is not configured. "
            "Check your GEMINI_API_KEY environment variable."
        )

    else:
        client = genai.Client(api_key=api_key)

        if st.button(
            "✨ Explain with AI",
            type="primary",
            use_container_width=True
        ):

            if not question.strip():
                st.warning("Please enter a question first.")

            else:

                instructions = {
                    "Explain simply": (
                        "Explain the topic in simple English "
                        "for a beginner. Define difficult terms."
                    ),
                    "Explain step by step": (
                        "Explain the topic in clear numbered "
                        "steps, moving from basic to advanced."
                    ),
                    "Give practical examples": (
                        "Explain the topic and provide useful "
                        "practical examples."
                    ),
                    "Summarize a topic": (
                        "Give a concise summary with the most "
                        "important points."
                    ),
                    "Help me understand code": (
                        "Explain programming concepts and "
                        "code line by line when code is provided."
                    ),
                    "Generate a quiz": (
                        "Create five multiple-choice questions about the topic. "
                        "Give four options for each question, labelled A, B, C, D. "
                        "Put the answer key at the end with brief explanations."
                    ),
                    "Create revision questions": (
                        "Create ten revision questions about the topic. "
                        "Include a mixture of short-answer and understanding questions. "
                        "Provide suggested answers in a separate section at the end."
                    )
                }

                prompt = f"""
You are ExplainIt AI, a helpful educational assistant.

Teaching style:
{instructions[study_mode]}

Student's question:
{question}

Guidelines:
- Use clear, friendly language.
- Organize the response with headings when useful.
- Include examples where appropriate.
- Use readable Markdown formatting.
- Be honest about uncertainty.
- Do not invent facts or references.
- Help the student understand the reasoning.
"""

                with st.spinner(
                    "📚 Preparing your explanation..."
                ):

                    try:
                        response = client.models.generate_content(
                            model="gemma-4-26b-a4b-it",
                            contents=prompt
                        )

                        if response.text:
                            # Display the latest answer.
                            st.session_state.answer = response.text
                            st.session_state.last_question = question
                            st.session_state.question = question

                            # Remember the selected learning style.
                            st.session_state.last_study_mode = study_mode

                            # Save the conversation permanently.
                            save_chat(
                                question=question,
                                answer=response.text,
                                study_mode=study_mode
                            )

                            st.success("Your question and answer have been saved!")

                        else:
                            st.warning(
                                "The AI returned an empty answer. "
                                "Please try again."
                            )

                    except Exception as error:
                        st.error(
                            "We couldn't generate your answer. "
                            "Check your internet connection and "
                            "AI model access, then try again."
                        )

                        # Show technical details for troubleshooting
                        with st.expander("Technical details"):
                            st.code(str(error))

    # ======================================
# DISPLAY AI ANSWER
# ======================================

if st.session_state.answer:

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        '💡 Your explanation'
        '</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Question: " + st.session_state.last_question
    )

    # Use a real Streamlit container so the answer
    # and its Markdown formatting display reliably.
    with st.container(border=True):

        st.markdown(st.session_state.answer)

        st.divider()

        st.caption(
            "Learning tip: Verify important facts "
            "using reliable learning materials."
        )

    if st.button("🗑️ Clear answer"):

        st.session_state.answer = ""
        st.session_state.last_question = ""
        st.session_state.question = ""

        st.rerun()

        # Streamlit Markdown keeps headings, lists and code formatting
        st.markdown(st.session_state.answer)

        st.markdown(
            """
            <div style="
                border-top: 1px solid #E5E7EB;
                margin-top: 20px;
                padding-top: 10px;
                color: #4B5563;
                font-size: 13px;
            ">
                Learning tip: Make sure you understand the
                explanation, and verify important facts.
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🗑️ Clear answer"):

            st.session_state.answer = ""
            st.session_state.last_question = ""
            st.session_state.question = ""

            st.rerun()

    # ======================================
    # FEATURE CARDS
    # ======================================

    st.markdown("---")

    st.markdown(
        '<div class="section-title">'
        'Your learning toolkit'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Understand concepts</div>
            <div class="feature-description">
                Break difficult topics into simpler ideas.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🪜</div>
            <div class="feature-title">Learn step by step</div>
            <div class="feature-description">
                Follow explanations in a logical order.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💡</div>
            <div class="feature-title">Explore examples</div>
            <div class="feature-description">
                Connect new ideas to practical examples.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ======================================
    # FOOTER
    # ======================================

    st.markdown("""
    <div class="footer">
        ExplainIt AI · Learn one concept at a time 💜
        <br>
        AI can make mistakes. Verify important information.
    </div>
    """, unsafe_allow_html=True)