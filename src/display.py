from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
from src.utils import get_submissions_dataframe, generate_leaderboard_dataframe, update_submissions


def get_participant_name():
    
    welcome_container = st.empty()

    with welcome_container.container():

        st.write("You can download the test data, train data and an example upload file below:")

        cols = st.columns(3)

        with cols[0]:
            with open("data/test.csv", "rb") as f:
                st.download_button(
                    label="Download test data",
                    data=f,
                    file_name="test.csv",
                    mime="text/csv"
                )

        with cols[1]:
            with open("data/housing-classification-iter6.csv", "rb") as f:
                st.download_button(
                    label="Download train data",
                    data=f,
                    file_name="train.csv",
                    mime="text/csv"
                )

        with cols[2]:
            with open("data/example_upload.csv", "rb") as f:
                st.download_button(
                    label="Download example upload",
                    data=f,
                    file_name="example_upload.csv",
                    mime="text/csv"
                )

        st.text_input("Enter your participant name: ", key="text_input")



    if st.session_state.text_input != "":
        welcome_container.empty()
        st.info(f'Participant name {st.session_state.text_input}')
        return st.session_state.text_input

    return None


def plot_submissions(participant_name, gsheet_conn: GSheetsConnection):
    """
    Plot submission accuracy for a participant over time.
    
    Args:
        participant_name (str): Name of the participant.
    """
    participant_submissions = (
        get_submissions_dataframe(gsheet_conn)
            .query('participant == @participant_name')
            .filter(['submission_time', 'accuracy'])
            .copy()
    )
    if len(participant_submissions) > 1:
        participant_submissions["submission_time"] = (
            pd.to_datetime(participant_submissions["submission_time"]))
        participant_submissions = (
            participant_submissions
                .sort_values("submission_time")
                .set_index("submission_time")
        )
        st.line_chart(participant_submissions)
    else:
        st.success('Congratulations on your first submission!')


def show_leaderboard(gsheet_conn: GSheetsConnection): 
    st.title('LEADERBOARD')
    
    submissions_df = get_submissions_dataframe(gsheet_conn)
    if not submissions_df.empty:
        leaderboard_df = generate_leaderboard_dataframe(submissions_df)
        st.dataframe(leaderboard_df)
    else:
        st.write("There are no submissions.")


@st.fragment(run_every=20)
def display_leaderboard(gsheet_conn: GSheetsConnection) -> None:
    try:
        show_leaderboard(gsheet_conn)
    except:
        st.write("There are no submissions.")


def display_participant_results(participant_results) -> None:
    st.title('Participant results')
    st.dataframe(participant_results)


def display_setup_error(error_desc: str) -> None:
    st.warning("⚠️ **Leaderboard Configuration Missing**")
    st.info(f"""
        It looks like this app hasn't been connected to a Google Sheet yet.
        
        **To set this up, please follow the steps laid out in the "Streamlit: Google Service Account (Data Team)" secret on 1password.**
    
        Error details: {error_desc}
    """)


def update_and_plot_submissions(participant_results, participant_name, gsheet_conn: GSheetsConnection):
    update_submissions(participant_results, gsheet_conn)
    plot_submissions(participant_name, gsheet_conn)