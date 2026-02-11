import streamlit as st
from streamlit_gsheets import GSheetsConnection
from src.utils import process_uploaded_file
from src.gsheet import configure_gsheet
from src.display import display_leaderboard, display_setup_error, display_participant_results, update_and_plot_submissions, get_participant_name

# Constants
RESULTS_PATH = 'data/true_y.csv'

def main(gsheet_conn):
    st.title('Housing Classification App')
    st.write('Welcome to the housing classification app. Please enter your name and upload your results file to check your accuracy and see the leaderboard.')

    participant_name = get_participant_name()

    if participant_name:
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

        if uploaded_file:
            participant_results = process_uploaded_file(uploaded_file, participant_name, gsheet_conn, RESULTS_PATH)
            display_participant_results(participant_results)
            update_and_plot_submissions(participant_results, participant_name, gsheet_conn)
        else:
            st.warning('Please upload a file.')
    else:
        st.warning('Please enter your participant name.')

    display_leaderboard(gsheet_conn)

if __name__ == "__main__":
    gsheet_conn = configure_gsheet()
    if isinstance(gsheet_conn, GSheetsConnection):
        main(gsheet_conn)
    else:
        display_setup_error()
