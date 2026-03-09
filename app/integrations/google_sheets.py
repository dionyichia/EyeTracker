"""
Google Sheets integration utilities.
"""
from __future__ import annotations

import os
from typing import List, Optional

_IMPORT_ERROR: Optional[Exception] = None
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except Exception as exc:  # pragma: no cover - handled at runtime
    Credentials = None
    build = None
    _IMPORT_ERROR = exc


class GoogleSheetsError(RuntimeError):
    """Raised when Google Sheets integration fails."""


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_service(credentials_path: str):
    if _IMPORT_ERROR is not None or Credentials is None or build is None:
        raise GoogleSheetsError(
            "Google Sheets dependencies are missing. Install: "
            "google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib"
        )
    if not credentials_path:
        raise GoogleSheetsError("Google Sheets credentials_path is not set.")
    if not os.path.exists(credentials_path):
        raise GoogleSheetsError(f"Google Sheets credentials file not found: {credentials_path}")

    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def _ensure_header(service, spreadsheet_id: str, worksheet_name: str, header: List[str]):
    range_ = f"{worksheet_name}!1:1"
    existing = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_,
    ).execute()
    values = existing.get("values", [])
    if values:
        return
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet_name}!A1",
        valueInputOption="RAW",
        body={"values": [header]},
    ).execute()


def append_row(
    *,
    credentials_path: str,
    spreadsheet_id: str,
    worksheet_name: str,
    row_values: List[str],
    header: Optional[List[str]] = None,
):
    if not spreadsheet_id:
        raise GoogleSheetsError("Google Sheets spreadsheet_id is not set.")
    if not worksheet_name:
        raise GoogleSheetsError("Google Sheets worksheet_name is not set.")

    service = _get_service(credentials_path)
    if header:
        _ensure_header(service, spreadsheet_id, worksheet_name, header)

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{worksheet_name}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row_values]},
    ).execute()
