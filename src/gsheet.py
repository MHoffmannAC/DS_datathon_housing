from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

REQUIRED_COLUMNS_LEADERBOARD = ["participant", "accuracy", "submission_time", "batch"]


@st.cache_resource
def get_gsheet_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def ensure_batch_sheet_exists(batch: str):
    
    try:
        sh = open_gsheet_from_url()
    except gspread.SpreadsheetNotFound:
        st.error("Could not open spreadsheet")
        
    existing = [ws.title for ws in sh.worksheets()]

    
    if batch not in existing:
        sh.add_worksheet(title=batch, rows="1000", cols="3")    


def ensure_sheet_structure(batch: str):
        
    try:
        df = st.session_state.gsheet_conn.read(worksheet=batch, ttl=0)

        if df is None or df.empty:
            empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS_LEADERBOARD)
            st.session_state.gsheet_conn.update(worksheet=batch, data=empty_df)

            return empty_df

        if list(df.columns) != REQUIRED_COLUMNS_LEADERBOARD:
            raise Exception(
                f"Sheet structure is invalid. "
                f"Expected columns: {REQUIRED_COLUMNS_LEADERBOARD}, "
                f"but got: {list(df.columns)}"
            )

        return df

    except Exception as e:
        raise Exception(f"Could not validate Google Sheet structure. {e}")


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
            
            if batch:
                ensure_batch_sheet_exists(batch)
                ensure_sheet_structure(batch)
            st.session_state.gsheet_conn = gsheet_conn
            return "Successful"
        except Exception as e:
            return f"Error connecting to Google Sheets. Please check whether you shared the Spreadsheet with the Service Account. {e}"
    else:
        return "Streamlit secrets incomplete. Please set up your secrets as per the instructions."


@st.cache_data(ttl=60)
def open_gsheet_from_url():
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet_url = creds_dict["spreadsheet"]
    return client.open_by_url(spreadsheet_url)