import sys
import os

# Adjust path to import backend modules
sys.path.append("/Users/somespecies/Desktop/main projects/researchpilot for anti-gra")

from api import generate_pdf

def test_pdf_with_broken_image():
    print("Testing generate_pdf with a broken image link...")
    report_text = """# Test Report
## Topic
Test Topic
## Generated On
2026-06-08 12:00:00
---
![Image](https://invalid-domain-name-that-should-fail-to-resolve-12345.com/broken.png)
This is body text.
## References
[1] [Test Source](http://example.com)
"""
    insights = {
        "word_count": 50,
        "references_used": 1,
        "unique_sources": 1,
        "average_source_freshness": 2026.0,
        "citation_density": 0.05,
        "evidence_coverage": 0.5,
        "evidence_panel": []
    }
    
    try:
        pdf_buffer = generate_pdf(report_text, insights)
        pdf_bytes = pdf_buffer.getvalue()
        print(f"PDF generated successfully! Size: {len(pdf_bytes)} bytes.")
        
        # Save output PDF to scratch directory for manual inspection if needed
        output_path = "/Users/somespecies/Desktop/main projects/researchpilot for anti-gra/scratch/test_output.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved test PDF to: {output_path}")
        
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_pdf_with_broken_image()
