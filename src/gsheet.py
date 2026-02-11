from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd

REQUIRED_COLUMNS_LEADERBOARD = ["participant", "accuracy", "submission_time"]

def ensure_sheet_structure(gsheet_conn: GSheetsConnection):
    try:
        df = gsheet_conn.read(ttl=0)

        if df is None or df.empty:
            empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS_LEADERBOARD)
            gsheet_conn.update(data=empty_df)
            return empty_df

        if list(df.columns) != REQUIRED_COLUMNS_LEADERBOARD:
            raise Exception(
                f"Sheet structure is invalid. "
                f"Expected columns: {REQUIRED_COLUMNS_LEADERBOARD}, "
                f"but got: {list(df.columns)}"
            )

        return df

    except Exception as e:
        raise Exception(
            f"Could not validate Google Sheet structure. {e}"
        )

def configure_gsheet():
    try:
        "connections" in st.secrets
    except:
        return "Streamlit secrets not found or empty. Please set up your secrets as per the instructions."
    if (
        "connections" in st.secrets and 
        "gsheets" in st.secrets["connections"] and 
        "spreadsheet" in st.secrets["connections"]["gsheets"] and
        "private_key"in st.secrets["connections"]["gsheets"]
    ):
        try:
            gsheet_conn = st.connection(
                                        "gsheets",
                                        type=GSheetsConnection,
                                        )
            ensure_sheet_structure(gsheet_conn)
            return gsheet_conn
        except Exception as e:
            return f"Error connecting to Google Sheets. Please check whether you shared the Spreadsheet with the Service Account. {e}"
    else:
        return "Streamlit secrets incomplete. Please set up your secrets as per the instructions."

