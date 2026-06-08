import sys
import os

workspace_dir = "/Users/somespecies/Desktop/main projects/researchpilot for anti-gra"
sys.path.append(workspace_dir)
os.chdir(workspace_dir)

from api import generate_pdf, validate_pdf_data
import json

report_text = """# Research Report
## Topic
Growth of Indian cinema in the 20's

## Generated On
2026-06-07 18:00:00

---
![Image](https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop)

• **Erosion of Physical Media's Traditional Advantages:**
The conventional benefits...

## References
[1] Phalke Wikipedia
wikipedia.org
https://wikipedia.org/wiki/Dadasaheb_Phalke
"""

insights = {"unique_sources": 4}

val = validate_pdf_data(report_text, insights)
if val:
    print(f"Validation failed: {val}")
else:
    print("Validation passed.")
    try:
        print("Generating PDF...")
        buf = generate_pdf(report_text, insights)
        print("Success! PDF generated.")
        with open("scratch/test_new_format.pdf", "wb") as f:
            f.write(buf.read())
    except Exception as e:
        import traceback
        print("FAILED with exception:")
        traceback.print_exc()
