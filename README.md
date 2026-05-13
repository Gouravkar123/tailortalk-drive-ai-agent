# 🗂️ TailorTalk – AI-Powered Google Drive File Discovery

> A production-ready conversational AI agent that searches Google Drive using natural language. Built with FastAPI, LangChain, Streamlit, and the Google Drive API.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat)](https://langchain.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python)](https://python.org)

---

## ✨ What It Does

TailorTalk lets you find files in Google Drive by asking questions naturally:

| You Ask | It Searches |
|---------|-------------|
| *"Find the financial report from last week"* | `name contains 'financial' and modifiedTime > '2025-01-05T00:00:00'` |
| *"Show me all PDFs"* | `mimeType = 'application/pdf'` |
| *"Find spreadsheets with budget in the name"* | `name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'` |
| *"Search for documents containing invoice"* | `fullText contains 'invoice'` |
| *"What images were uploaded this month?"* | `mimeType contains 'image/' and modifiedTime > '2025-01-01T00:00:00'` |

---

## 🏗️ Architecture

```
User (Browser)
    │
    ▼
Streamlit Frontend  ──HTTP POST /api/v1/chat──►  FastAPI Backend
(frontend/app.py)                                (backend/app/main.py)
                                                      │
                                                      ▼
                                            LangChain ReAct Agent
                                            (services/agent.py)
                                                      │
                                              Tool Calling (LLM)
                                                      │
                                                      ▼
                                            DriveSearchTool
                                            (q= query builder)
                                                      │
                                                      ▼
                                          Google Drive API v3
                                          (files.list with q=)
```

### Key Design: Tool Calling for Drive Queries

The LLM uses **function/tool calling** to translate natural language into precise Google Drive `q` parameter strings. This is the core insight that makes search highly accurate:

```python
@tool
def drive_search_tool(query: str) -> str:
    """
    The LLM calls this with a properly-formatted Drive q parameter.
    E.g.: name contains 'report' and modifiedTime > '2025-01-01T00:00:00'
    """
    result = search_drive_files(query)
    return format_results(result)
```

---

## 🚀 Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/TailorTalk.git
cd TailorTalk

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Google Drive API

**Step 1: Create a Google Cloud Project**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable the **Google Drive API**:
   - Navigate to *APIs & Services → Library*
   - Search for "Google Drive API" → Enable

**Step 2: Create a Service Account**
1. Go to *APIs & Services → Credentials*
2. Click *Create Credentials → Service Account*
3. Fill in name (e.g., `tailortalk-agent`) → Create
4. Click the service account → *Keys* tab → *Add Key → JSON*
5. Download the JSON file → **rename it `credentials.json`**
6. Place `credentials.json` in the project root

**Step 3: Share Your Drive Folder**
1. Copy the sample folder: [TailorTalk Sample Drive](https://drive.google.com/drive/folders/1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt)
2. Open the copied folder in your Drive
3. Click *Share* → paste your service account email (looks like `tailortalk-agent@project-id.iam.gserviceaccount.com`)
4. Set permission to **Viewer** → Share
5. Copy the folder ID from the URL: `drive.google.com/drive/folders/`**`THIS_PART`**

### 3. Get an LLM API Key

**Groq (Recommended – Free & Fast):**
1. Sign up at [console.groq.com](https://console.groq.com)
2. Create API Key → copy it

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
DRIVE_FOLDER_ID=your_folder_id_here
BACKEND_URL=http://localhost:8000
```

### 5. Run

**Terminal 1 – Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/api/v1/health
```

**Terminal 2 – Frontend:**
```bash
cd frontend
streamlit run app.py
# Opens: http://localhost:8501
```

---

## ☁️ Deploy to Cloud

### Backend → Render

1. Push to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/TailorTalk.git
git push -u origin main
```

2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `GROQ_API_KEY` = your key
   - `DRIVE_FOLDER_ID` = your folder ID
   - `GOOGLE_CREDENTIALS_JSON` = paste the **entire contents** of `credentials.json` as one line

> **Tip for GOOGLE_CREDENTIALS_JSON:** Run `python -c "import json; print(json.dumps(json.load(open('credentials.json'))))"` to get a single-line JSON string.

6. Deploy → note your URL: `https://your-app.onrender.com`

### Frontend → Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. New App → select your GitHub repo
3. **Main file path:** `frontend/app.py`
4. Add Secrets (Settings → Secrets):
```toml
BACKEND_URL = "https://your-app.onrender.com"
```
5. Deploy → get your public URL

---

## 📁 File Structure

```
TailorTalk/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app, CORS, routing
│       ├── api/
│       │   └── routes.py        # POST /api/v1/chat endpoint
│       ├── services/
│       │   ├── agent.py         # LangChain agent + DriveSearchTool
│       │   └── drive.py         # Google Drive API client
│       └── core/
│           └── config.py        # Pydantic settings (reads .env)
├── frontend/
│   ├── app.py                   # Streamlit chat UI
│   ├── requirements.txt         # Frontend-only deps
│   └── .streamlit/
│       └── config.toml          # Streamlit dark theme config
├── requirements.txt             # All Python dependencies
├── .env.example                 # Environment template
├── render.yaml                  # Render deployment config
├── railway.json                 # Railway deployment config
├── Procfile                     # Heroku/fly.io compat
└── README.md
```

---

## 🔍 Search Query Reference

The agent automatically translates your natural language into these Drive API queries:

| What You Say | Drive Query Generated |
|---|---|
| "Find report.pdf" | `name = 'report.pdf'` |
| "Files with 'budget' in name" | `name contains 'budget'` |
| "All PDFs" | `mimeType = 'application/pdf'` |
| "Google Sheets" | `mimeType = 'application/vnd.google-apps.spreadsheet'` |
| "Images" | `mimeType contains 'image/'` |
| "Files about revenue" | `fullText contains 'revenue'` |
| "Modified last week" | `modifiedTime > '2025-01-05T00:00:00'` |
| "PDFs from last month" | `mimeType = 'application/pdf' and modifiedTime > '2024-12-12T00:00:00'` |

---

## 🔧 Supported LLMs

Set exactly **one** of these in your `.env`:

| Provider | Key | Model Used |
|---|---|---|
| **Groq** (recommended) | `GROQ_API_KEY` | llama-3.1-8b-instant |
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini |
| Google Gemini | `GOOGLE_API_KEY` | gemini-1.5-flash |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run `uvicorn app.main:app` from inside the `backend/` folder |
| `Credentials not found` | Place `credentials.json` in project root; check `GOOGLE_APPLICATION_CREDENTIALS` in `.env` |
| `CORS error in Streamlit` | Confirm `BACKEND_URL` matches your actual backend URL (no trailing slash) |
| `No files found` | Verify the service account email is shared on your Drive folder |
| `Timeout on first query` | Groq free tier cold starts; retry after a few seconds |
| `Model decommissioned` | Update model name in `backend/app/services/agent.py` |

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

---

Built with ❤️ using **FastAPI · LangChain · Streamlit · Google Drive API**
