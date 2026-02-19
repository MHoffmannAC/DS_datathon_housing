import streamlit as st
from src.utils import process_uploaded_file, state_inits
from src.display import (
    display_leaderboard,
    display_participant_results,
    update_and_plot_submissions,
    get_participant_info,
)

# Constants
RESULTS_PATH = "data/true_y.csv"


def main():
    st.title("Welcome to our classification competition!")

    participant_name, batch = get_participant_info()

    if participant_name and batch:
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

        if uploaded_file:
            participant_results = process_uploaded_file(uploaded_file, RESULTS_PATH)
            display_participant_results(participant_results)
            update_and_plot_submissions(participant_results, participant_name, batch)
        else:
            st.warning("Please upload a file.")

        display_leaderboard()
    else:
        st.stop()


state_inits()
main()
