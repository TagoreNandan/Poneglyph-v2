import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from graph import graph

import streamlit as st

st.set_page_config(
    page_title="ResearchPilot AI",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 ResearchPilot AI")

query = st.text_input(
    "Enter Research Topic"
)

if st.button("Generate Report"):

    with st.spinner(
        "Researching..."
    ):

        result = graph.invoke(
            {
                "query": query
            }
        )

    st.markdown(
        result["formatted_report"]
    )

    st.download_button(
        label="Download Report",
        data=result["formatted_report"],
        file_name="research_report.md",
        mime="text/markdown"
    )