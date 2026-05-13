import streamlit as st
import requests
import os
from datetime import datetime


st.set_page_config(
    page_title="TailorTalk – Drive AI",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: #0f1117;
        color: #e8eaf0;
    }

    /* Hide default streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #161b27;
        border-right: 1px solid #252d3d;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #7c8cf8;
    }

    /* Chat messages */
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin: 12px 0;
    }
    .user-bubble {
        background: linear-gradient(135deg, #4f63d2 0%, #7c8cf8 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 2px 12px rgba(79, 99, 210, 0.3);
    }
    .assistant-message {
        display: flex;
        justify-content: flex-start;
        margin: 12px 0;
        gap: 10px;
        align-items: flex-start;
    }
    .assistant-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1e2a45 0%, #2d3f6b 100%);
        border: 1px solid #3d52a0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        line-height: 34px;
        text-align: center;
    }
    .assistant-bubble {
        background: #1a2035;
        border: 1px solid #252d3d;
        color: #e8eaf0;
        padding: 12px 18px;
        border-radius: 4px 18px 18px 18px;
        max-width: 80%;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* Header banner */
    .main-header {
        background: linear-gradient(135deg, #111827 0%, #1a2035 50%, #111827 100%);
        border: 1px solid #252d3d;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .header-logo {
        font-size: 2.2rem;
    }
    .header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #7c8cf8;
        font-family: 'Space Mono', monospace;
        margin: 0;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: #6b7280;
        margin: 2px 0 0 0;
    }

    /* Status dot */
    .status-dot-online {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #22c55e;
        display: inline-block;
        margin-right: 6px;
        box-shadow: 0 0 6px #22c55e;
    }
    .status-dot-offline {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #ef4444;
        display: inline-block;
        margin-right: 6px;
    }

    /* Suggestion chips */
    .chip-container { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .chip {
        background: #1a2035;
        border: 1px solid #2d3f6b;
        color: #7c8cf8;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        cursor: pointer;
    }

    /* Timestamp */
    .ts {
        font-size: 0.7rem;
        color: #4b5563;
        margin-top: 4px;
        text-align: right;
    }

    /* Input area */
    .stTextInput input, .stTextArea textarea {
        background: #1a2035 !important;
        border: 1px solid #252d3d !important;
        color: #e8eaf0 !important;
        border-radius: 10px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4f63d2 !important;
        box-shadow: 0 0 0 2px rgba(79,99,210,0.25) !important;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #4f63d2 0%, #7c8cf8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(79,99,210,0.4) !important;
    }

    /* Sidebar pills */
    .query-example {
        background: #1a2035;
        border: 1px solid #252d3d;
        border-left: 3px solid #4f63d2;
        border-radius: 0 8px 8px 0;
        padding: 8px 12px;
        margin: 6px 0;
        font-size: 0.82rem;
        color: #9ca3af;
        cursor: pointer;
    }
    .query-example:hover { border-left-color: #7c8cf8; color: #e8eaf0; }

    /* Thinking spinner */
    .thinking {
        display: flex; align-items: center; gap: 8px;
        color: #7c8cf8; font-size: 0.85rem; padding: 8px 0;
    }

    /* Stats card */
    .stat-card {
        background: #1a2035;
        border: 1px solid #252d3d;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .stat-number { font-size: 1.5rem; font-weight: 700; color: #7c8cf8; }
    .stat-label { font-size: 0.75rem; color: #6b7280; margin-top: 2px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = None



def check_backend() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def send_message(message: str) -> str:
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/chat",
            json={"message": message, "chat_history": history},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "No response received.")
    except requests.exceptions.ConnectionError:
        return (
            " **Cannot connect to backend.**\n\n"
            f"Make sure the backend is running at `{BACKEND_URL}`.\n\n"
            "Run: `cd backend && uvicorn app.main:app --reload --port 8000`"
        )
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. The LLM might be warming up — please try again."
    except Exception as e:
        return f" Error: {str(e)}"


def now_str() -> str:
    return datetime.now().strftime("%H:%M")


EXAMPLE_QUERIES = [
    "Find all PDF files",
    "Show me spreadsheets modified this month",
    "Search for files with 'budget' in the name",
    "Find images uploaded last week",
    "Look for any document about marketing",
    "Show the most recently modified files",
    "Find all Google Docs",
    "Search for files containing the word 'invoice'",
]

WELCOME_MESSAGE = """👋 **Hello! I'm TailorTalk**, your Google Drive AI assistant.

I can help you **find any file** in your connected Drive using natural language. Just tell me what you're looking for!

**Try asking me:**
- *"Find the financial report from last week"*
- *"Show me all PDFs uploaded this month"*
- *"Search for spreadsheets containing the word budget"*
- *"List all images in the drive"*

What would you like to find today?"""


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🗂️ TailorTalk")
    st.markdown("*Google Drive AI Assistant*")
    st.divider()

    # Backend status
    if st.button("🔄 Check Connection", use_container_width=True):
        st.session_state.backend_ok = check_backend()

    if st.session_state.backend_ok is None:
        st.session_state.backend_ok = check_backend()

    if st.session_state.backend_ok:
        st.markdown('<span class="status-dot-online"></span> **Backend Connected**', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot-offline"></span> **Backend Offline**', unsafe_allow_html=True)
        st.caption(f"Expected at: `{BACKEND_URL}`")

    st.divider()

    # Stats
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{st.session_state.query_count}</div>'
            f'<div class="stat-label">Searches</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{len(st.session_state.messages)}</div>'
            f'<div class="stat-label">Messages</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### 💡 Example Queries")
    st.caption("Click any example to use it:")

    for q in EXAMPLE_QUERIES:
        if st.button(q, key=f"ex_{q}", use_container_width=True):
            st.session_state["prefill_query"] = q

    st.divider()
    st.markdown("### ⚙️ Search Capabilities")
    st.markdown(
        """
- 📄 **By name** (exact or partial)
- 📁 **By file type** (PDF, Doc, Sheet…)
- 🔍 **Full-text** within documents
- 📅 **By date** (last week, month, etc.)
- 🔗 **Combinations** of the above
        """
    )

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.query_count = 0
        st.rerun()


# Header
st.markdown(
    """
    <div class="main-header">
        <div class="header-logo">🗂️</div>
        <div>
            <div class="header-title">TailorTalk</div>
            <div class="header-subtitle">AI-powered Google Drive file discovery · Natural language search</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown(
            f'<div class="assistant-message">'
            f'<div class="assistant-avatar">🤖</div>'
            f'<div><div class="assistant-bubble">{WELCOME_MESSAGE}</div>'
            f'<div class="ts">Now</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-message">'
                    f'<div><div class="user-bubble">{msg["content"]}</div>'
                    f'<div class="ts">{msg.get("ts","")}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="assistant-message">'
                    f'<div class="assistant-avatar">🤖</div>'
                    f'<div style="max-width:80%">',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""
                    <div class="assistant-bubble">
                    {msg["content"]}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ts">{msg.get("ts","")}</div></div></div>',
                    unsafe_allow_html=True,
                )




st.divider()

if "chat_input_value" not in st.session_state:
    st.session_state.chat_input_value = ""


prefill = st.session_state.pop("prefill_query", None)

if prefill:
    st.session_state.chat_input_value = prefill

col_input, col_send = st.columns([5, 1])

with col_input:
    user_input = st.text_input(
        "Message",
        placeholder="Ask me to find any file… e.g. 'Show me PDFs from last month'",
        label_visibility="collapsed",
        key="chat_input_value",
    )

with col_send:
    send_clicked = st.button("Send ➤", use_container_width=True)

if send_clicked:

    user_msg = st.session_state.chat_input_value.strip()

    if user_msg:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_msg,
                "ts": now_str(),
            }
        )

        st.session_state.query_count += 1


        with st.spinner("🔍 Searching your Drive…"):
            response = send_message(user_msg)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "ts": now_str(),
            }
        )

        # Trigger rerun safely
        st.session_state["clear_input"] = True

        st.rerun()

st.markdown(
    """
    <div style="text-align:center; color:#374151; font-size:0.75rem; margin-top:20px; padding:10px">
        TailorTalk · Powered by LangChain + Google Drive API
        · <a href="/docs" style="color:#4f63d2">API Docs</a>
    </div>
    """,
    unsafe_allow_html=True,
)
