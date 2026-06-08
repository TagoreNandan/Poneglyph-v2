import sys
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

doc = SimpleDocTemplate("scratch/test_wbr_out.pdf", pagesize=(612, 792), leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
styles = getSampleStyleSheet()

url_style = ParagraphStyle(
    'UrlStyle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8,
    leading=10,
    textColor=colors.HexColor("#6B7280")
)

# Insert <wbr/> after characters
url = "https://silentfilmcalendar.org/reviews/operational-energy-footprints?param1=long_query_string_to_force_line_wrapping&param2=another_long_query_parameter_value_to_ensure_it_does_not_overflow"
wrapped_url = ""
for char in url:
    wrapped_url += char
    if char in ["/", "?", "&", "=", ".", "-", "_"]:
        wrapped_url += "<wbr/>"

content = []
content.append(Paragraph(f'<a href="{url}" color="#4F46E5"><u>{wrapped_url}</u></a>', url_style))

doc.build(content)
print("PDF with wbr built successfully!")
