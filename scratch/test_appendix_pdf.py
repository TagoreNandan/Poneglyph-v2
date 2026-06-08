import sys
import os

workspace_dir = "/Users/somespecies/Desktop/main projects/researchpilot for anti-gra"
sys.path.append(workspace_dir)
os.chdir(workspace_dir)

from api import generate_pdf

report_text = """# Research Report
## Topic
Sustainability Crisis in Neural Networks

## Generated On
2026-06-08 12:00:00

---
This is a report text.
"""

insights = {
    "word_count": 100,
    "references_used": 1,
    "unique_sources": 1,
    "average_source_freshness": 2026.0,
    "citation_density": 0.05,
    "evidence_coverage": 0.5,
    "evidence_panel": [
        {
            "index": 1,
            "title": "Operational energy footprints of generative foundations",
            "url": "https://silentfilmcalendar.org/reviews/operational-energy-footprints?param1=long_query_string_to_force_line_wrapping&param2=another_long_query_parameter_value_to_ensure_it_does_not_overflow",
            "excerpt": "Training next-generation foundation models requires gigawatt-hour scale footprints, straining local grids."
        }
    ]
}

try:
    print("Generating PDF with Evidence Appendix...")
    buf = generate_pdf(report_text, insights)
    print("Success!")
    with open("scratch/test_appendix_out_new.pdf", "wb") as f:
        f.write(buf.read())
except Exception as e:
    import traceback
    traceback.print_exc()
