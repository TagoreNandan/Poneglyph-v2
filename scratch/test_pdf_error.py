import sys
import os

workspace_dir = "/Users/somespecies/Desktop/main projects/researchpilot for anti-gra"
sys.path.append(workspace_dir)
os.chdir(workspace_dir)

from api import generate_pdf
import json

report_text = """# Research Report
## Topic
Growth of Indian cinema in the 20's

## Generated On
2026-06-07 18:00:00

---
![Image](https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop)

This is a test report about the growth of Indian cinema. It contains & characters and links: [Source](https://wikipedia.org/wiki/Dadasaheb_Phalke?param=1&param2=2).

## References
[1] [Phalke Wikipedia](https://wikipedia.org/wiki/Dadasaheb_Phalke?param=1&param2=2)
"""

try:
    print("Generating PDF...")
    buf = generate_pdf(report_text, {})
    print("Success! PDF generated.")
    with open("scratch/test_out_new.pdf", "wb") as f:
        f.write(buf.read())
except Exception as e:
    import traceback
    print("FAILED with exception:")
    traceback.print_exc()
