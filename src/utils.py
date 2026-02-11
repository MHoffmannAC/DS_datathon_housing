import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import io
from src.eval import get_ready_test, get_accuracy


def validate_csv_file(file):
    try:
        file.seek(0)  # Reset file pointer to the beginning
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))

        if set(['Id', 'Expensive']).issubset(df.columns):
            return True
        else:
            return False
    except Exception as e:
        return False


def update_submissions(participant_results: pd.DataFrame, gsheet_conn: GSheetsConnection):
    """
    Update the submissions file with the participant's results.

    Args:
        participant_results (pd.DataFrame): DataFrame containing the participant's results.
    """
    submissions_df = get_submissions_dataframe(gsheet_conn)
    updated_submissions_df = pd.concat([submissions_df, participant_results])
    gsheet_conn.update(data=updated_submissions_df)


def get_submissions_dataframe(gsheet_conn: GSheetsConnection):
    try:
        return gsheet_conn.read(ttl=0)
    except Exception as e:
        raise Exception(f"Could not read submissions from Google Sheets. Please check your connection. {e}")


def process_uploaded_file(uploaded_file, participant_name, gsheet_conn: GSheetsConnection, RESULTS_PATH: str):
    if validate_csv_file(uploaded_file):
        try:
            uploaded_file.seek(0)  # Reset file pointer to the beginning
            test = get_ready_test(RESULTS_PATH, uploaded_file)
            if isinstance(test, pd.DataFrame):
                participant_results = get_accuracy(RESULTS_PATH, test)
                st.success('Dataframe uploaded successfully!')
                return participant_results
                
        except Exception as e:
            st.error(f'The file could not be processed. Error: {e}')
    else:
        st.error('The uploaded file has the wrong format. Please, review it and ensure it contains the required columns.')


def generate_leaderboard_dataframe(submissions_df):
    best_results_per_participant = (
        submissions_df
        .assign(
            attempts=lambda df_: df_.groupby('participant')['participant'].transform('count')
        )
        .sort_values(['accuracy','submission_time'], ascending=[False, True])
        .drop_duplicates(subset=['participant'], keep='first')
        .assign(position=lambda df_: range(1, len(df_) + 1))
        .set_index('position')
        .filter(['participant', 'accuracy', 'attempts'])
        )

    return best_results_per_participant