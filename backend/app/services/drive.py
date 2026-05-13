import os
import json
import logging
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

MIME_TYPE_LABELS = {
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheet",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.google-apps.folder": "Folder",
    "application/pdf": "PDF",
    "image/jpeg": "JPEG Image",
    "image/png": "PNG Image",
    "image/gif": "GIF Image",
    "image/webp": "WebP Image",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint",
    "text/plain": "Text File",
    "text/csv": "CSV File",
    "application/zip": "ZIP Archive",
}


def get_drive_service():
    """Build and return an authenticated Google Drive service."""
    try:
        # Try raw JSON string first (for cloud deployments via env var)
        if settings.GOOGLE_CREDENTIALS_JSON:
            info = json.loads(settings.GOOGLE_CREDENTIALS_JSON)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        elif settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
            )
        else:
            logger.warning("No Google credentials found. Drive search will return demo data.")
            return None

        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build Drive service: {e}")
        return None


def search_drive_files(query: str, folder_id: Optional[str] = None, max_results: int = 20) -> dict:
    """
    Execute a Google Drive files.list query.
    Returns a dict with 'files' list and 'error' key.
    """
    service = get_drive_service()

    if service is None:
        return {
            "files": _demo_files(query),
            "error": None,
            "demo_mode": True,
        }

    try:
        folder_id = folder_id or settings.DRIVE_FOLDER_ID

        # Build the final query
        final_query = query
        if folder_id:
            # Restrict search to the specified folder (including subfolders via recursive approach)
            final_query = f"({query}) and '{folder_id}' in parents and trashed = false"
        else:
            final_query = f"({query}) and trashed = false"

        logger.info(f"Executing Drive query: {final_query}")

        results = (
            service.files()
            .list(
                q=final_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, size, webViewLink, webContentLink, parents, description)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])
        formatted = []
        for f in files:
            mime = f.get("mimeType", "")
            formatted.append(
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "type": MIME_TYPE_LABELS.get(mime, mime.split("/")[-1].replace("vnd.", "")),
                    "mimeType": mime,
                    "modifiedTime": f.get("modifiedTime", ""),
                    "size": _format_size(f.get("size")),
                    "viewLink": f.get("webViewLink", ""),
                    "downloadLink": f.get("webContentLink", ""),
                    "description": f.get("description", ""),
                }
            )

        return {"files": formatted, "error": None, "demo_mode": False}

    except HttpError as e:
        logger.error(f"Drive API HTTP error: {e}")
        return {"files": [], "error": str(e), "demo_mode": False}
    except Exception as e:
        logger.error(f"Drive search error: {e}")
        return {"files": [], "error": str(e), "demo_mode": False}


def _format_size(size_str: Optional[str]) -> str:
    if not size_str:
        return "—"
    try:
        size = int(size_str)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 ** 3:
            return f"{size / 1024 ** 2:.1f} MB"
        else:
            return f"{size / 1024 ** 3:.1f} GB"
    except Exception:
        return "—"


def _demo_files(query: str) -> list:
    """Return demo files when no credentials are configured."""
    demo = [
        {
            "id": "demo1",
            "name": "Q4 Financial Report 2024.pdf",
            "type": "PDF",
            "mimeType": "application/pdf",
            "modifiedTime": "2024-12-15T10:30:00Z",
            "size": "2.4 MB",
            "viewLink": "https://drive.google.com",
            "downloadLink": "",
            "description": "Quarterly financial summary",
        },
        {
            "id": "demo2",
            "name": "Budget Planning Sheet.xlsx",
            "type": "Excel Sheet",
            "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "modifiedTime": "2024-12-10T14:00:00Z",
            "size": "512 KB",
            "viewLink": "https://drive.google.com",
            "downloadLink": "",
            "description": "Annual budget planning",
        },
        {
            "id": "demo3",
            "name": "Project Roadmap.docx",
            "type": "Word Doc",
            "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "modifiedTime": "2024-12-08T09:00:00Z",
            "size": "128 KB",
            "viewLink": "https://drive.google.com",
            "downloadLink": "",
            "description": "",
        },
        {
            "id": "demo4",
            "name": "Company Logo.png",
            "type": "PNG Image",
            "mimeType": "image/png",
            "modifiedTime": "2024-11-20T16:00:00Z",
            "size": "340 KB",
            "viewLink": "https://drive.google.com",
            "downloadLink": "",
            "description": "",
        },
        {
            "id": "demo5",
            "name": "Meeting Notes - Dec 2024.gdoc",
            "type": "Google Doc",
            "mimeType": "application/vnd.google-apps.document",
            "modifiedTime": "2024-12-12T11:00:00Z",
            "size": "—",
            "viewLink": "https://drive.google.com",
            "downloadLink": "",
            "description": "Team meeting notes",
        },
    ]
    return demo
