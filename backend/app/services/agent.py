import json
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent

from app.services.drive import search_drive_files
from app.core.config import settings

logger = logging.getLogger(__name__)


@tool
def drive_search_tool(query: str) -> str:
    """
    Search Google Drive using the official 'q' query parameter syntax.

    The query must be a valid Google Drive API query string. Examples:
      - name contains 'report'
      - name = 'Budget 2024'
      - mimeType = 'application/pdf'
      - mimeType contains 'image'
      - fullText contains 'quarterly revenue'
      - modifiedTime > '2024-01-01T00:00:00'
      - name contains 'invoice' and mimeType = 'application/pdf'
      - modifiedTime > '2024-11-01T00:00:00' and mimeType = 'application/vnd.google-apps.spreadsheet'

    Always use proper Google Drive q syntax. Return only the raw q string, no extra text.
    """
    result = search_drive_files(query)

    if result.get("error"):
        return f"Error searching Drive: {result['error']}"

    files = result.get("files", [])
    demo_mode = result.get("demo_mode", False)

    if not files:
        return "No files found matching your query."

    demo_note = "\n⚠️ *Demo mode – connect credentials to search your real Drive.*\n" if demo_mode else ""

    lines = [f"{demo_note}Found **{len(files)}** file(s):\n"]
    for i, f in enumerate(files, 1):
        modified = f.get("modifiedTime", "")[:10] if f.get("modifiedTime") else "unknown"
        view_link = f.get("viewLink", "")
        link_text = f"[Open in Drive]({view_link})" if view_link and view_link != "https://drive.google.com" else ""
        lines.append(
            f"{i}. **{f['name']}**\n"
            f"   • Type: {f['type']}\n"
            f"   • Modified: {modified}\n"
            f"   • Size: {f['size']}\n"
            f"   {link_text}"
        )

    return "\n".join(lines)



SYSTEM_PROMPT = f"""You are TailorTalk, an expert AI assistant that helps users find files in Google Drive through natural conversation.

Today's date is: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} (UTC)

## Your Capabilities
You can search Google Drive files by:
- **Name**: exact or partial matches
- **File type**: PDFs, Docs, Sheets, Slides, images, Excel, Word, etc.
- **Content**: full-text search within documents
- **Date**: files modified before/after specific dates
- **Combinations**: any mix of the above

## How to Use the Drive Search Tool
Always call `drive_search_tool` with a proper Google Drive `q` query string.

### Query Syntax Reference
| Goal | Query |
|------|-------|
| Exact name | `name = 'Budget 2024'` |
| Name contains word | `name contains 'budget'` |
| PDF files | `mimeType = 'application/pdf'` |
| Google Docs | `mimeType = 'application/vnd.google-apps.document'` |
| Google Sheets | `mimeType = 'application/vnd.google-apps.spreadsheet'` |
| Google Slides | `mimeType = 'application/vnd.google-apps.presentation'` |
| Word documents | `mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'` |
| Excel files | `mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'` |
| Images (any) | `mimeType contains 'image/'` |
| Full-text search | `fullText contains 'quarterly revenue'` |
| Modified after date | `modifiedTime > '2024-01-01T00:00:00'` |
| Modified in last 7 days | `modifiedTime > '{(datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')}'` |
| Modified in last 30 days | `modifiedTime > '{(datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S')}'` |
| Combined | `name contains 'report' and mimeType = 'application/pdf'` |

### MIME Type Quick Reference
- PDF: `application/pdf`
- Google Doc: `application/vnd.google-apps.document`
- Google Sheet: `application/vnd.google-apps.spreadsheet`
- Google Slides: `application/vnd.google-apps.presentation`
- Images: `mimeType contains 'image/'`
- Word: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## Response Guidelines
- Be conversational and friendly
- After showing results, offer to refine or search differently
- If a query returns no results, suggest alternative search terms
- Always present results in a readable, organized format
- If the user's request is ambiguous, make a reasonable assumption and search, then ask if they want refinement
- For date-based queries, calculate exact dates from relative terms like "last week", "yesterday", "past month"
"""



def _get_llm():
    """Return the best available LLM."""
    # Try Groq first (fast & free tier)
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model="llama-3.1-8b-instant",
                temperature=0,
            )
        except Exception as e:
            logger.warning(f"Groq failed: {e}")


    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o-mini",
                temperature=0,
            )
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")

    if settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                google_api_key=settings.GOOGLE_API_KEY,
                model="gemini-1.5-flash",
                temperature=0,
            )
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

    raise ValueError(
        "No LLM API key configured. Set GROQ_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY in your .env file."
    )


def build_agent() -> AgentExecutor:
    """Build and return the LangChain agent with Drive tool."""
    llm = _get_llm()
    tools = [drive_search_tool]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)
    return executor


llm = _get_llm()
def run_agent(user_message: str, history=None):

    prompt = f"""
You are a Google Drive search assistant.

Convert the user's request into a Google Drive API q query.

Examples:

User: Find all PDF files
Query: mimeType = 'application/pdf'

User: Find spreadsheets
Query: mimeType = 'application/vnd.google-apps.spreadsheet'

User: Search files containing budget
Query: fullText contains 'budget'

User: Find images
Query: mimeType contains 'image/'

User: Find reports from last week
Query: name contains 'report' and modifiedTime > '2026-05-05T00:00:00'

User: Find Excel sheets
Query: mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

User request:
{user_message}

Return ONLY the query string.
"""

    response = llm.invoke(prompt)

    drive_query = response.content.strip()

    print("Generated Query:", drive_query)

    result = search_drive_files(drive_query)

    files = result.get("files", [])

    if not files:
        return "No matching files found."

    formatted = "## Found Files\n\n"

    for file in files:
        formatted += (
            f"### 📄 {file['name']}\n"
            f"- Type: {file['type']}\n"
            f"- Modified: {file.get('modifiedTime', 'N/A')}\n"
            f"- [Open File]({file.get('viewLink', '#')})\n\n"
        )

    return formatted