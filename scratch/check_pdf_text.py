import sys
import pypdf

pdf_path = "scratch/test_out.pdf"
reader = pypdf.PdfReader(pdf_path)
print("Number of pages:", len(reader.pages))
for idx, page in enumerate(reader.pages):
    print(f"\n=== Page {idx + 1} ===")
    print(page.extract_text()[:1500])
