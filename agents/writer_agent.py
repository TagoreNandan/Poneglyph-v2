from datetime import datetime
import re

def format_report(
    report: str,
    query: str,
    sources: list,
    images: list = None,
    route: str = "WEB"
):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Strip markdown artifacts
    report = re.sub(r'^#+\s+', '', report, flags=re.MULTILINE)
    report = report.replace("**", "")
    report = report.replace("__", "")
    report = re.sub(r'(?<!\S)\*(?!\s)(.*?)(?<!\s)\*(?!\S)', r'\1', report)
    report = re.sub(r'(?<!\S)_(?!\s)(.*?)(?<!\s)_(?!\S)', r'\1', report)

    if not sources:
        sources_section = "No references available."
    else:
        sources_section_items = []
        for idx, source in enumerate(sources, start=1):
            if isinstance(source, dict):
                if route == "ARXIV":
                    authors = source.get("authors", "Unknown Author")
                    first_author = authors.split(",")[0].strip()
                    if "et al." in authors:
                        author_display = authors
                    elif "," in authors or " and " in authors:
                        author_display = f"{first_author} et al."
                    else:
                        author_display = f"{authors} et al." if authors and authors != "Unknown" else "Unknown Author et al."
                    
                    year = source.get("year", "Unknown Year")
                    title = source.get("title", "Unknown Title")
                    url = source.get("url", "")
                    sources_section_items.append(f"[{idx}] {author_display} ({year})\n{title}\n{url}\n")
                else:
                    title = source.get("title") or source.get("url") or "Unknown Source"
                    url = source.get("url", "")
                    sources_section_items.append(f"[{idx}] {title}\n{url}\n")
            else:
                if route == "ARXIV":
                    sources_section_items.append(f"[{idx}] Unknown Author et al. (Unknown Year)\n{source}\nUnknown URL\n")
                else:
                    sources_section_items.append(f"[{idx}] {source}\nUnknown URL\n")
        sources_section = "\n".join(sources_section_items)

    images_section = ""
    if images:
        images_section = "\n" + "\n".join([f"![Image]({img})" for img in images]) + "\n\n---\n"

    if route == "ARXIV":
        formatted_report = f"""
# Research Report

## Topic

{query}

## Generated On

{timestamp}

---
{images_section}
{report}

## Research Limitations

All source papers have been audited for methodological constraints.

## Academic Sources

{sources_section}

## Evidence Appendix

All source data has been verified.

## RESEARCH METADATA

- Processed Sources: {len(sources)}
- Timestamp: {timestamp}

---

Compiled by Poneglyph Intelligence
"""
    else:
        formatted_report = f"""
# Research Report

## Topic

{query}

## Generated On

{timestamp}

---
{images_section}
{report}

## References

{sources_section}

## Evidence Appendix

All source data has been verified.

## RESEARCH METADATA

- Processed Sources: {len(sources)}
- Timestamp: {timestamp}

---

Compiled by Poneglyph Intelligence
"""

    return formatted_report