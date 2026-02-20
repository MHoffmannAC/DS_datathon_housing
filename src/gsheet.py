from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

REQUIRED_COLUMNS_LEADERBOARD = ["participant", "accuracy", "submission_time", "batch"]


def _open_spreadsheet():
    creds_dict = dict(st.secrets["connections"]["gsheets"])

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    return client.open_by_url(creds_dict["spreadsheet"])


@st.cache_resource
def get_gsheet_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def ensure_batch_sheet_exists(batch: str):

    conn = st.session_state.gsheet_conn

    try:
        conn.read(worksheet=batch, ttl=0)
        return

    except WorksheetNotFound:
        pass

    sh = _open_spreadsheet()

    sh.add_worksheet(
        title=batch,
        rows="1000",
        cols="10",
    )

    empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS_LEADERBOARD)
    conn.update(worksheet=batch, data=empty_df)


def ensure_sheet_structure(batch: str):
    try:
        df = st.session_state.gsheet_conn.read(worksheet=batch, ttl=0)

        if df is None or df.empty:
            empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS_LEADERBOARD)
            st.session_state.gsheet_conn.update(worksheet=batch, data=empty_df)

            return empty_df

        return df

    except Exception:
        st.error("Could not validate Google Sheet structure.")


@st.cache_data
def configure_gsheet(batch: str | None = None):
    try:
        "connections" in st.secrets
    except Exception:
        return "Streamlit secrets not found or empty. Please set up your secrets as per the instructions."

    if (
        "connections" in st.secrets
        and "gsheets" in st.secrets["connections"]
        and "spreadsheet" in st.secrets["connections"]["gsheets"]
        and "private_key" in st.secrets["connections"]["gsheets"]
    ):
        try:
            gsheet_conn = get_gsheet_connection()
            st.session_state.gsheet_conn = gsheet_conn
            
            if batch:
                ensure_batch_sheet_exists(batch)
                ensure_sheet_structure(batch)
            
            return "Successful"
        except Exception as e:
            raise Exception(f"Error connecting to Google Sheets. Please check whether you shared the Spreadsheet with the Service Account. {e}")
    else:
        return "Streamlit secrets incomplete. Please set up your secrets as per the instructions."
