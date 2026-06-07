import sys
import os
from datetime import datetime

import streamlit as st

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "latest_report" not in st.session_state:
    st.session_state["latest_report"] = None

if "latest_route" not in st.session_state:
    st.session_state["latest_route"] = "Unknown"

if "latest_sources" not in st.session_state:
    st.session_state["latest_sources"] = []

if "latest_time" not in st.session_state:
    st.session_state["latest_time"] = 0

if "insights" not in st.session_state:
    st.session_state["insights"] = ""

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from agents.chat_agent import (
    chat_with_report
)

from graph import graph

from memory.database import (
    get_history,
    get_report_by_id
)

from ui.components import (
    render_hero,
    render_compact_header,
    render_metric_card,
    render_source_card,
    render_gap_alert,
    render_contradiction_alert,
    render_status_badge
)


from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from reportlab.lib import colors



def generate_pdf(text, insights):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = getSampleStyleSheet()

    content = []

    # -----------------
    # TITLE
    # -----------------

    # -----------------
    # # INSIGHTS SECTION
    # # -----------------
    
    content.append(
        Paragraph(
            "Research Insights",
            styles["Heading1"]
        )
    )
    
    content.append(
        Paragraph(
            "Research Quality Indicators",
            styles["Heading1"]
        )
    )
    
    ref_used = insights.get("references_used", insights.get("reference_count", "N/A"))
    uniq_src = insights.get("unique_sources", "N/A")
    freshness = insights.get("average_source_freshness", "N/A")
    
    citation_density = insights.get("citation_density", "N/A")
    evidence_coverage = insights.get("evidence_coverage", "N/A")
    
    density_str = f"{int(citation_density * 100)}%" if isinstance(citation_density, (int, float)) else "N/A"
    coverage_str = f"{int(evidence_coverage * 100)}%" if isinstance(evidence_coverage, (int, float)) else "N/A"

    content.append(Paragraph(f"References Used: {ref_used}", styles["BodyText"]))
    content.append(Paragraph(f"Unique Sources: {uniq_src}", styles["BodyText"]))
    content.append(Paragraph(f"Average Source Freshness: {freshness}", styles["BodyText"]))
    content.append(Paragraph(f"Citation Density: {density_str}", styles["BodyText"]))
    content.append(Paragraph(f"Evidence Coverage: {coverage_str}", styles["BodyText"]))
    

    content.append(
        Paragraph(
            "Contradictions",
            styles["Heading2"]
        )
    )
    
    contradictions = insights.get(
    "contradictions",
    []
    )
    
    if contradictions:
        for item in contradictions:
            content.append(
            Paragraph(
                f"• {item}",
                styles["BodyText"]
            )
        )
    else:
        content.append(
            Paragraph(
            "None",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            "ResearchPilot AI",
            styles["Title"]
        )
    )

    content.append(
        Paragraph(
            "Autonomous Research Report",
            styles["Heading2"]
        )
    )

    content.append(
        Spacer(
            1,
            20
        )
    )

    # -----------------
    # REPORT BODY
    # -----------------

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # markdown headings

        if line.startswith("# "):

            content.append(
                Spacer(
                    1,
                    10
                )
            )

            content.append(
                Paragraph(
                    line.replace(
                        "# ",
                        ""
                    ),
                    styles["Heading1"]
                )
            )

        elif line.startswith("## "):

            content.append(
                Paragraph(
                    line.replace(
                        "## ",
                        ""
                    ),
                    styles["Heading2"]
                )
            )

        elif line.startswith("### "):

            content.append(
                Paragraph(
                    line.replace(
                        "### ",
                        ""
                    ),
                    styles["Heading3"]
                )
            )

        else:

            content.append(
                Paragraph(
                    line,
                    styles["BodyText"]
                )
            )

        content.append(
            Spacer(
                1,
                4
            )
        )

        content.append(
            Paragraph(
            "Generated by ResearchPilot AI",
            styles["Italic"]
            )
        )

    # -----------------
    # FOOTER
    # -----------------

    content.append(
        Spacer(
            1,
            20
        )
    )

    content.append(
        Paragraph(
            "Generated by ResearchPilot AI",
            styles["Italic"]
        )
    )

    doc.build(
        content
    )

    buffer.seek(0)

    return buffer

# ----------------------------
# PAGE CONFIG
# ----------------------------

st.set_page_config(
    page_title="ResearchPilot AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load external CSS styles
css_file = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_file):
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ----------------------------
# SESSION STATE
# ----------------------------

if "agent_status" not in st.session_state:

    st.session_state.agent_status = {
        "Router Agent": "⏳ Waiting",
        "Reader Agent": "⏳ Waiting",
        "Research Agent": "⏳ Waiting",
        "Critic Agent": "⏳ Waiting",
        "Writer Agent": "⏳ Waiting"
    }

# ----------------------------
# SIDEBAR
# ----------------------------

with st.sidebar:

    st.markdown("<h3>⚙️ System Status</h3>", unsafe_allow_html=True)

    st.markdown('<div class="agent-status-container">', unsafe_allow_html=True)
    for agent, status in st.session_state.agent_status.items():
        st.markdown(
            render_status_badge(agent, status),
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    history = get_history()

    st.metric(
        "📊 Reports Generated",
        len(history)
    )

    st.markdown("<h3>📚 Research History</h3>", unsafe_allow_html=True)

    if history:
        for item in history[:10]:
            report_id = item[0]
            query_text = item[1]

            if st.button(
                query_text,
                key=f"history_{report_id}"
            ):
                st.session_state["selected_report"] = report_id
                # Clear active report to avoid layout overlap
                st.session_state["latest_report"] = None
                st.rerun()
    else:
        st.info("No previous research yet.")

# ----------------------------
# ROUTING & RENDERING ENGINE
# ----------------------------

has_active_report = bool(st.session_state.get("latest_report") or st.session_state.get("selected_report"))

# 1. HOME SCREEN (No active report)
if not has_active_report:
    st.markdown(render_hero(), unsafe_allow_html=True)
    
    query = st.text_input(
        "Enter Research Topic",
        placeholder="What would you like to research today?",
        label_visibility="collapsed"
    )
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        generate_clicked = st.button("Generate Report")
        
    if generate_clicked:
        if query.strip() == "":
            st.warning("Please enter a research topic.")
            st.stop()

        progress = st.progress(0)

        with st.spinner("Running Multi-Agent Workflow..."):
            start_time = datetime.now()
            st.session_state.agent_status["Router Agent"] = "🔄 Running"
            progress.progress(20)

            result = graph.invoke({"query": query})

            end_time = datetime.now()

            for agent in st.session_state.agent_status:
                st.session_state.agent_status[agent] = "Complete"

            progress.progress(100)

            st.session_state["latest_report"] = result["formatted_report"]
            st.session_state["latest_route"] = result.get("route", "Unknown")
            st.session_state["latest_sources"] = result.get("sources", [])
            st.session_state["latest_time"] = (end_time - start_time).seconds
            st.session_state["insights"] = result.get("insights", "")
            
            # Clear historical selection
            if "selected_report" in st.session_state:
                del st.session_state["selected_report"]
                
            st.rerun()

# 2. DASHBOARD SCREEN (Active report loaded)
else:
    # Navigation / Header bar
    col_h1, col_h2 = st.columns([6, 2])
    with col_h1:
        st.markdown(render_compact_header(), unsafe_allow_html=True)
    with col_h2:
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
        if st.button("New Research"):
            st.session_state["latest_report"] = None
            if "selected_report" in st.session_state:
                del st.session_state["selected_report"]
            st.session_state["chat_history"] = []
            st.session_state["latest_sources"] = []
            st.session_state["insights"] = ""
            st.rerun()

    # Case A: Viewing historical report
    if "selected_report" in st.session_state:
        report = get_report_by_id(st.session_state["selected_report"])
        if report:
            report_title = report[1]
            report_content = report[3]
            
            # Metadata stats
            word_count = len(report_content.split())
            st.info(
                f"📄 Words: {word_count} | 📚 Loaded from Research History"
            )
            
            # Report container
            st.markdown('<div class="report-card-anchor"></div>', unsafe_allow_html=True)
            st.markdown(report_content)
            
            # Download buttons
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="Download Markdown",
                    data=report_content,
                    file_name="research_report.md",
                    mime="text/markdown",
                    key="download_md_history"
                )
            with col_d2:
                try:
                    pdf_file = generate_pdf(report_content, {})
                    st.download_button(
                        label="Download PDF",
                        data=pdf_file,
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        key="download_pdf_history"
                    )
                except Exception as e:
                    st.error(f"PDF Error: {e}")

    # Case B: Viewing latest generated report
    elif st.session_state.get("latest_report"):
        latest_report = st.session_state["latest_report"]
        insights = st.session_state.get("insights", {})
        if not isinstance(insights, dict):
            insights = {}
        sources = st.session_state.get("latest_sources", [])
        duration = st.session_state.get("latest_time", 0)
        
        # 1. Display Insights if they exist and contain data
        if "references_used" in insights or "word_count" in insights:
            st.markdown("<h3>Research Quality Indicators</h3>", unsafe_allow_html=True)
            
            ref_used = insights.get("references_used", insights.get("reference_count", 0))
            uniq_src = insights.get("unique_sources", 0)
            freshness = insights.get("average_source_freshness", "N/A")
            density_pct = insights.get("citation_density", 0)
            coverage_pct = insights.get("evidence_coverage", 0)
            
            density_val = f"{int(density_pct * 100)}%" if isinstance(density_pct, (int, float)) else "N/A"
            coverage_val = f"{int(coverage_pct * 100)}%" if isinstance(coverage_pct, (int, float)) else "N/A"
            
            metric_html = f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">References Used</div>
                    <div class="metric-value">{ref_used}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Unique Sources</div>
                    <div class="metric-value">{uniq_src}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Avg Source Freshness</div>
                    <div class="metric-value">{freshness}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Citation Density</div>
                    <div class="metric-value">{density_val}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Evidence Coverage</div>
                    <div class="metric-value">{coverage_val}</div>
                </div>
            </div>
            """
            st.markdown(metric_html, unsafe_allow_html=True)
            
            with st.expander("Contradictions", expanded=False):
                contradictions = insights.get("contradictions", [])
                if contradictions:
                    for item in contradictions:
                        st.markdown(render_contradiction_alert(item), unsafe_allow_html=True)
                else:
                    st.markdown(render_contradiction_alert("No contradictions found."), unsafe_allow_html=True)
            
            st.markdown("<hr/>", unsafe_allow_html=True)
            
        # 2. Display Report
        st.markdown("<h3>Research Report</h3>", unsafe_allow_html=True)
        
        word_count = len(latest_report.split())
        st.info(
            f"Words: {word_count} • "
            f"Sources: {len(sources)} • "
            f"Generated in: {duration}s"
        )
        
        st.markdown('<div class="report-card-anchor"></div>', unsafe_allow_html=True)
        st.markdown(latest_report)
        
        st.markdown("<hr/>", unsafe_allow_html=True)
        
        # 3. Sources Used Section
        if sources:
            st.markdown("<h3>Sources Used</h3>", unsafe_allow_html=True)
            sources_html = '<div class="sources-grid">'
            for src in sources:
                sources_html += render_source_card(src)
            sources_html += '</div>'
            st.markdown(sources_html, unsafe_allow_html=True)
            st.markdown("<hr/>", unsafe_allow_html=True)
            
        # 4. Download Buttons
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="Download Markdown",
                data=latest_report,
                file_name="research_report.md",
                mime="text/markdown",
                key="download_md_latest"
            )
        with col_d2:
            try:
                pdf_file = generate_pdf(latest_report, insights)
                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name="research_report.pdf",
                    mime="application/pdf",
                    key="download_pdf_latest"
                )
            except Exception as e:
                st.error(f"PDF Error: {e}")
                
        st.markdown("<hr/>", unsafe_allow_html=True)
        
        # 5. Follow-Up Chat
        st.markdown("<h3>Follow-up Chat</h3>", unsafe_allow_html=True)
        for chat in st.session_state["chat_history"]:
            with st.chat_message("user"):
                st.write(chat["question"])
            with st.chat_message("assistant"):
                st.write(chat["answer"])
        
        follow_up = st.text_input("Ask a question about this report...", key="follow_up_input")
        if st.button("Send", key="send_followup"):
            if follow_up.strip():
                answer = chat_with_report(
                    latest_report,
                    follow_up,
                    st.session_state["chat_history"]
                )
                st.session_state["chat_history"].append({
                    "question": follow_up,
                    "answer": answer
                })
                st.rerun()
                
        st.markdown("<hr/>", unsafe_allow_html=True)