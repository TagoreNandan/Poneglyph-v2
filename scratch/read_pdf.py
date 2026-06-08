import sys
from reportlab.pdfgen import canvas
import pypdf

reader = pypdf.PdfReader("/Users/somespecies/.gemini/antigravity-ide/brain/8313eff8-2599-4d18-a9f7-bce6f7c59749/scratch/test_report.pdf")
print("Number of pages:", len(reader.pages))
for idx, page in enumerate(reader.pages):
    print(f"\n--- Page {idx + 1} ---")
    print(page.extract_text()[:1000])
