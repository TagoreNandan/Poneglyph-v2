import sys
import os
from datetime import datetime

import streamlit as st

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from graph import graph

from memory.database import (
    get_history,
    get_report_by_id
)

# ----------------------------
# PAGE CONFIG
# ----------------------------

st.set_page_config(
    page_title="ResearchPilot AI",
    page_icon="🔬",
    layout="wide"
)

# ----------------------------
# PAGE HEADER
# ----------------------------

st.title("🔬 ResearchPilot AI")

st.caption(
    "Autonomous Multi-Agent Research System powered by LangGraph, RAG, ChromaDB, SQLite and Ollama"
)

# ----------------------------
# SIDEBAR
# ----------------------------

with st.sidebar:

    st.header("⚙️ System Status")

    st.success("Router Agent")
    st.success("Reader Agent")
    st.success("Research Agent")
    st.success("Critic Agent")
    st.success("Writer Agent")

    st.divider()

    st.header("📚 Research History")

    history = get_history()

    if history:

        for item in history[:10]:

            report_id = item[0]
            query_text = item[1]

            if st.button(
                query_text,
                key=f"history_{report_id}"
            ):

                st.session_state[
                    "selected_report"
                ] = report_id

    else:

        st.info(
            "No previous research yet."
        )

# ----------------------------
# DISPLAY SAVED REPORT
# ----------------------------

if "selected_report" in st.session_state:

    report = get_report_by_id(
        st.session_state[
            "selected_report"
        ]
    )

    if report:

        st.subheader(
            f"📄 {report[1]}"
        )

        st.markdown(
            report[3]
        )

        st.divider()

# ----------------------------
# QUERY INPUT
# ----------------------------

query = st.text_input(
    "Enter Research Topic",
    placeholder="Example: Latest developments in RAG"
)

# ----------------------------
# GENERATE REPORT
# ----------------------------

if st.button("🚀 Generate Report"):

    if query.strip() == "":

        st.warning(
            "Please enter a research topic."
        )

        st.stop()

    progress = st.progress(0)

    with st.spinner(
        "Running Multi-Agent Workflow..."
    ):

        progress.progress(20)

        start_time = datetime.now()

        result = graph.invoke(
            {
                "query": query
            }
        )

        progress.progress(100)

        end_time = datetime.now()

    # ----------------------------
    # METRICS
    # ----------------------------

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Route Used",
            result.get(
                "route",
                "Unknown"
            )
        )

    with col2:

        st.metric(
            "Sources",
            len(
                result.get(
                    "sources",
                    []
                )
            )
        )

    with col3:

        st.metric(
            "Execution Time",
            f"{(end_time - start_time).seconds}s"
        )

    # ----------------------------
    # REPORT
    # ----------------------------

    st.divider()

    st.subheader(
        "📄 Research Report"
    )

    st.markdown(
        result["formatted_report"]
    )

    # ----------------------------
    # DOWNLOAD
    # ----------------------------

    st.download_button(
        label="⬇️ Download Report",
        data=result["formatted_report"],
        file_name="research_report.md",
        mime="text/markdown"
    )