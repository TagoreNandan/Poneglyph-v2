from datetime import datetime
import re

def calculate_reliability_score(url: str, source_type: str = "web") -> tuple:
    if not url:
        return 70, "Corporate Blog"
    
    url_lower = url.lower()
    domain = url_lower.split("://")[-1].split("/")[0].split("?")[0]
    if domain.startswith("www."):
        domain = domain[4:]
        
    DOMAIN_RELIABILITY = {
        "openai.com": 95,
        "anthropic.com": 95,
        "deepmind.google": 95,
        "nature.com": 98,
        "arxiv.org": 90,
        "reuters.com": 95,
        "bloomberg.com": 95,
        "wsj.com": 90,
        "ft.com": 90,
        "coursera.org": 80,
        "github.com": 80,
        "reddit.com": 45,
        "youtube.com": 50
    }
    
    reliability = None
    if domain in DOMAIN_RELIABILITY:
        reliability = DOMAIN_RELIABILITY[domain]
    else:
        for d, r in DOMAIN_RELIABILITY.items():
            if domain == d or domain.endswith("." + d):
                reliability = r
                break
                
    if reliability is None:
        if ".gov" in domain:
            reliability = 95
        elif ".edu" in domain or source_type == "arxiv":
            reliability = 90
        else:
            reliability = 70
            
    official_domains = ["openai.com", "anthropic.com", "google.com", "microsoft.com", "nvidia.com", "tesla.com", "deepmind.google", "sec.gov"]
    academic_domains = ["arxiv.org", "nature.com", "science.org", "coursera.org"]
    news_domains = ["reuters.com", "bloomberg.com", "ft.com", "wsj.com", "cnbc.com", "cnn.com"]
    tech_domains = ["techcrunch.com", "theverge.com", "wired.com", "github.com"]
    community_domains = ["medium.com", "substack.com", "reddit.com", "youtube.com"]
    social_domains = ["instagram.com", "tiktok.com", "facebook.com", "twitter.com", "x.com", "pinterest.com"]

    dom_type = "Community"
    if any(d in domain for d in official_domains) or ".gov" in domain:
        dom_type = "Official"
    elif any(d in domain for d in academic_domains) or ".edu" in domain or source_type == "arxiv":
        dom_type = "Academic"
    elif any(d in domain for d in news_domains):
        dom_type = "Major News"
    elif any(d in domain for d in tech_domains):
        dom_type = "Technology Publication"
    elif any(d in domain for d in community_domains) or any(x in domain for x in ["forum", "forums", "community", "stackexchange", "stackoverflow", "fandom", "quora"]):
        dom_type = "Community"
    elif any(d in domain for d in social_domains):
        dom_type = "Social Media"
        
    return reliability, dom_type

def clean_report_citations(text: str, num_sources: int) -> str:
    if not text:
        return ""
        
    # Split into body and references/sources section using split to keep references section intact
    parts = re.split(r'(\n##? (?:References|Academic Sources)\b)', text, maxsplit=1, flags=re.IGNORECASE)
    body = parts[0]
    rest = ""
    if len(parts) > 1:
        rest = "".join(parts[1:])
        
    # Helper to split comma-separated inline citations, e.g. [1, 2] -> [1][2]
    def split_comma_citations(match):
        nums = re.split(r'\s*,\s*', match.group(1))
        return "".join(f"[{n}]" for n in nums)
    body = re.sub(r'\[\s*(\d+(?:\s*,\s*\d+)+)\s*\]', split_comma_citations, body)
    
    # Standardize source-card variations to simple brackets:
    # 1. [source-card-1] or [#source-card-1] -> [1]
    body = re.sub(
        r'\[\s*#?(?:source[- ]*card|source)[- ]*(\d+)\s*\]',
        r'[\1]',
        body,
        flags=re.IGNORECASE
    )
    # 2. (source-card-1) or (#source-card-1) -> [1]
    body = re.sub(
        r'\(\s*#?(?:source[- ]*card|source)[- ]*(\d+)\s*\)',
        r'[\1]',
        body,
        flags=re.IGNORECASE
    )
    
    # Standardize/convert raw [X] or [X](#source-card-X)
    def replace_citation(match):
        num = int(match.group(1))
        if 1 <= num <= num_sources:
            return f"[{num}](#source-card-{num})"
        else:
            # If citation cannot be resolved (out of bounds), remove it
            return ""
            
    # Match any [X] or [X](#source-card-X)
    body = re.sub(
        r'\[\s*(\d+)\s*\](?:\(#source-card-\d+\))?',
        replace_citation,
        body
    )
    
    # Strip any remaining unresolved source-card text/placeholders
    body = re.sub(r'\[#?source[- ]*card[- ]*.*?\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'(?<!\])\(#?source[- ]*card[- ]*.*?\)', '', body, flags=re.IGNORECASE)
    
    return body + rest

def format_report(
    report: str,
    query: str,
    sources: list,
    images: list = None,
    route: str = "WEB",
    verified_claims: list = None
):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    from agents.research_agent import classify_report_type
    category = classify_report_type(query)
    preserve_markdown = True

    if not preserve_markdown:
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

    verification_section = ""
    if verified_claims:
        counts = {"SUPPORTED": 0, "WEAK": 0, "DISPUTED": 0, "UNVERIFIED": 0}
        for vc in verified_claims:
            status = vc.get("status", "UNVERIFIED").upper()
            counts[status] = counts.get(status, 0) + 1
            
        verification_section = f"""
## Verification Summary

* {counts['SUPPORTED']} Supported
* {counts['WEAK']} Weak
* {counts['DISPUTED']} Disputed
* {counts['UNVERIFIED']} Unverified
"""

        disputed_list = [vc for vc in verified_claims if vc.get("status") == "DISPUTED"]
        if disputed_list:
            disputed_section_items = []
            for dc in disputed_list:
                claim_text = dc.get("claim", "")
                evidence_text = "; ".join(dc.get("evidence", [])) if dc.get("evidence") else "No evidence retrieved."
                disputed_section_items.append(
                    f"* **Claim**: {claim_text}\n  * **Status**: **[DISPUTED]**\n  * **Evidence**: {evidence_text}"
                )
            verification_section += "\n## Disputed Claims\n\n" + "\n".join(disputed_section_items) + "\n"

        verification_section += "\n## Verified Claims Detail\n\n"
        for vc in verified_claims:
            status = vc.get("status", "UNVERIFIED").upper()
            badge = f"**[{status}]**"
            claim_text = vc.get("claim", "")
            verification_section += f"* {badge} {claim_text}\n"
            
            vc_sources = vc.get("sources", [])
            if vc_sources:
                prim = vc_sources[0]
                prim_title = prim.get("title") or "Source"
                prim_url = prim.get("url") or ""
                score, dom_type = calculate_reliability_score(prim_url, "arxiv" if route == "ARXIV" else "web")
                verification_section += f"  * *Verification Source*: [{prim_title}]({prim_url}) | **Reliability: {score}** ({dom_type})\n"
        
        verification_section += "\n"

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
{verification_section}
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
{verification_section}
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

    formatted_report = clean_report_citations(formatted_report, len(sources) if sources else 0)
    return formatted_report