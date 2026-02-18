import streamlit as st
import pandas as pd
from src.utils import (
    get_batches_dataframe,
    generate_leaderboard_dataframe,
    update_submissions,
)
from src.gsheet import configure_gsheet
from streamlit_server_state import server_state


def get_participant_info():

    welcome_container = st.empty()

    with welcome_container.container():
        st.write(
            "If you haven't done so yet, please download the test data, train data, and an example upload file below."
        )

        cols = st.columns(3)

        with cols[0]:
            with open("data/test.csv", "rb") as f:
                st.download_button(
                    label="Download test data",
                    data=f,
                    file_name="test.csv",
                    mime="text/csv",
                )

        with cols[1]:
            with open("data/housing-classification-iter6.csv", "rb") as f:
                st.download_button(
                    label="Download train data",
                    data=f,
                    file_name="train.csv",
                    mime="text/csv",
                )

        with cols[2]:
            with open("data/example_upload.csv", "rb") as f:
                st.download_button(
                    label="Download example upload",
                    data=f,
                    file_name="example_upload.csv",
                    mime="text/csv",
                )

        st.divider()

        st.warning(
            "Please enter **your name** (real or alias) and **the code** provided by your instructor."
        )

        st.text_input("Enter your name: ", key="name_input")
        st.text_input("Enter your batch's secret code: ", key="code_input")

    batches_df = get_batches_dataframe()

    code_to_batch = batches_df.set_index("Code")["Batch"]
    code_to_alltime = batches_df.set_index("Code")["Show All-time?"]

    st.session_state.batch = code_to_batch.get(st.session_state.code_input)
    st.session_state.alltime = code_to_alltime.get(st.session_state.code_input)
    print(st.session_state.alltime)

    if (
        st.session_state.name_input
        and st.session_state.code_input
        and st.session_state.batch
    ):
        welcome_container.empty()
        if st.session_state.batch not in server_state.submissions:
            server_state.submissions[st.session_state.batch] = (
                st.session_state.gsheet_conn.read(
                    worksheet=st.session_state.batch,
                    ttl=0,
                )
            )
        configure_gsheet(st.session_state.batch)
        st.info(f"Welcome {st.session_state.name_input} from {st.session_state.batch}")
        return st.session_state.name_input, st.session_state.batch

    return None, None


def plot_submissions(participant_name):
    """
    Plot submission accuracy for a participant over time.

    Args:
        participant_name (str): Name of the participant.
    """
    participant_submissions = (
        server_state.submissions[st.session_state.batch]
        .query("participant == @participant_name")
        .filter(["submission_time", "accuracy"])
        .copy()
    )
    if len(participant_submissions) > 1:
        participant_submissions["submission_time"] = pd.to_datetime(
            participant_submissions["submission_time"]
        )
        participant_submissions = participant_submissions.sort_values(
            "submission_time"
        ).set_index("submission_time")
        st.line_chart(participant_submissions)
    else:
        st.success("Congratulations on your first submission!")


def show_leaderboard():

    if st.session_state.batch == "anonymous":
        st.write("You decided to not compete in any leaderboard.")
    else:
        st.divider()
        st.header(f"Leaderboard from {st.session_state.batch}")
        submissions_df = server_state.submissions[st.session_state.batch]
        if not submissions_df.empty:
            leaderboard_df = generate_leaderboard_dataframe(submissions_df).drop(
                "batch", axis=1
            )
            st.dataframe(leaderboard_df)
        else:
            st.write("There are no submissions from your batch yet.")

        if (not server_state.alltime_submissions.empty) and st.session_state.alltime:
            st.divider()
            st.header("All-time Leaderboard")

            leaderboard_df = generate_leaderboard_dataframe(
                server_state.alltime_submissions
            )
            st.dataframe(leaderboard_df)


@st.fragment(run_every=30)
def display_leaderboard() -> None:
    try:
        show_leaderboard()
    except Exception as e:
        st.error(f"An error occured while extracting the leaderboard: {e}")


def display_participant_results(participant_results) -> None:
    st.title("Participant results")
    st.dataframe(participant_results)


def display_setup_error(error_desc: str) -> None:
    st.warning("⚠️ **Leaderboard Configuration Missing**")
    st.info(f"""
        It looks like this app hasn't been connected to a Google Sheet yet.
    
        Error details: {error_desc}
    """)


def update_and_plot_submissions(
    participant_results: pd.DataFrame, participant_name: str, batch: str
):
    update_submissions(participant_results)
    plot_submissions(participant_name)
