import pandas as pd
import streamlit as st
import io
from src.eval import get_ready_test, get_accuracy
from src.gsheet import configure_gsheet


@st.cache_resource
def get_global_store():
    return {
        "submissions": {},
        "alltime_submissions": None,
        "leaderboards": {},
        "alltime_leaderboard": None,
        "batches": None,
        "batches_last_updated": None,
    }


def state_inits():
    if "gsheet_conn" not in st.session_state:
        configure_gsheet()
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "code_input" not in st.session_state:
        st.session_state.code_input = None
    if "batch" not in st.session_state:
        st.session_state.batch = None
    if "alltime" not in st.session_state:
        st.session_state.alltime = None

    store = get_global_store()

    if store["alltime_submissions"] is None:
        
        batches = st.session_state.gsheet_conn.read(
            worksheet="Batches",
            ttl=0
        )["Batch"].tolist()

        worksheet_titles = [
            b for b in batches if b not in ["Batches", "anonymous"]
        ]

        dfs = []
        for ws_name in worksheet_titles:
            try:
                df = st.session_state.gsheet_conn.read(
                    worksheet=ws_name,
                    ttl=0
                )
                if df is not None and not df.empty:
                    dfs.append(df)

            except Exception:
                pass

        store["alltime_submissions"] = (
            pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        )

        build_leaderboards()
        
    if store["batches"] is None or store["batches_last_updated"] is None or (pd.Timestamp.now() - store["batches_last_updated"]).seconds > 300:
        store["batches"] = st.session_state.gsheet_conn.read(
            worksheet="Batches",
            ttl=0,
        )
        store["batches_last_updated"] = pd.Timestamp.now()

def validate_csv_file(file):
    try:
        file.seek(0)  # Reset file pointer to the beginning
        df = pd.read_csv(io.StringIO(file.read().decode("utf-8")))

        if set(["Id", "Expensive"]).issubset(df.columns):
            return True
        else:
            return False
    except Exception:
        return False


def update_submissions(participant_results: pd.DataFrame):
    store = get_global_store()
    batch = st.session_state.batch

    if batch in store["submissions"] and not store["submissions"][batch].empty:
        store["submissions"][batch] = pd.concat(
            [store["submissions"][batch], participant_results],
            ignore_index=True,
        )
    else:
        store["submissions"][batch] = participant_results

    updated_submissions_df = store["submissions"][batch].copy()

    store["alltime_submissions"] = pd.concat(
        [store["alltime_submissions"], participant_results],
        ignore_index=True,
    )

    st.session_state.gsheet_conn.update(worksheet=batch, data=updated_submissions_df)

    build_leaderboards()


def process_uploaded_file(uploaded_file, RESULTS_PATH: str):
    if validate_csv_file(uploaded_file):
        try:
            uploaded_file.seek(0)  # Reset file pointer to the beginning
            test = get_ready_test(RESULTS_PATH, uploaded_file)
            if isinstance(test, pd.DataFrame):
                participant_results = get_accuracy(RESULTS_PATH, test)
                st.success("Dataframe uploaded successfully!")
                return participant_results

        except Exception as e:
            st.error(f"The file could not be processed. Error: {e}")
    else:
        st.error(
            "The uploaded file has the wrong format. Please, review it and ensure it contains the required columns."
        )


def generate_leaderboard_dataframe(submissions_df):
    best_results_per_participant = (
        submissions_df.assign(
            attempts=lambda df_: df_.groupby("participant")["participant"].transform(
                "count"
            )
        )
        .sort_values(
            ["accuracy", "submission_time", "batch"], ascending=[False, True, True]
        )
        .drop_duplicates(subset=["participant"], keep="first")
        .assign(position=lambda df_: range(1, len(df_) + 1))
        .set_index("position")
        .filter(["participant", "accuracy", "attempts", "batch"])
    )

    return best_results_per_participant


def build_leaderboards():
    store = get_global_store()

    for batch, df in store["submissions"].items():
        if df is not None and not df.empty:
            store["leaderboards"][batch] = generate_leaderboard_dataframe(df)
        else:
            store["leaderboards"][batch] = pd.DataFrame()

    if (
        store["alltime_submissions"] is not None
        and not store["alltime_submissions"].empty
    ):
        store["alltime_leaderboard"] = generate_leaderboard_dataframe(
            store["alltime_submissions"]
        )
