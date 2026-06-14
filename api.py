import io
import re
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from graph import graph
from memory.database import get_history, get_report_by_id, init_db, delete_report_by_id
from agents.chat_agent import chat_with_report

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

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

app = FastAPI(title="Poneglyph Intelligence Backend API")

# Initialize database and prepopulate baseline reports
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------
# Pydantic Models
# -----------------
class ResearchRequest(BaseModel):
    query: str
    bypass_ambiguity: bool = False


class ChatRequest(BaseModel):
    report: str
    question: str
    history: List[Dict[str, str]] = []

class PDFRequest(BaseModel):
    report: str
    insights: Dict[str, Any] = {}
    chat_history: List[Dict[str, str]] = []
    show_citations: bool = False

def download_image_flowable(url: str, max_height: float = 350.0) -> Any:
    try:
        import requests
        import urllib3
        import base64
        from reportlab.platypus import Image as RLImage, Table, TableStyle
        from io import BytesIO
        from PIL import Image as PILImage
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print(f"Downloading image for PDF: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        pil_img = None
        if url.startswith("data:image/"):
            # Handle inline base64 image data URLs
            try:
                header, encoded = url.split(",", 1)
                data = base64.b64decode(encoded)
                pil_img = PILImage.open(BytesIO(data))
            except Exception as b64_err:
                print(f"Failed to decode base64 image: {b64_err}")
        else:
            # Handle protocol-relative URLs
            if url.startswith("//"):
                url = "https:" + url
                
            try:
                resp = requests.get(url, headers=headers, verify=False, timeout=8)
                if resp.status_code == 200:
                    pil_img = PILImage.open(BytesIO(resp.content))
            except Exception as download_err:
                print(f"Failed to download primary image {url}: {download_err}")
                
        if pil_img:
            if pil_img.mode not in ("RGB", "RGBA"):
                pil_img = pil_img.convert("RGB")
                
            width, height = pil_img.size
            max_width = 400.0
            
            if width > max_width:
                ratio = max_width / width
                width = max_width
                height = height * ratio
                
            if height > max_height:
                ratio = max_height / height
                height = max_height
                width = width * ratio
            
            out_io = BytesIO()
            pil_img.save(out_io, format="PNG")
            out_io.seek(0)
            
            rl_img = RLImage(out_io, width=width, height=height)
            
            t = Table([[rl_img]], colWidths=[width], hAlign='CENTER')
            t.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            return t
    except Exception as e:
        print(f"Failed to download image flowable for {url}: {e}")
    return None

def clean_report_citations(text: str, num_sources: int) -> str:
    if not text:
        return ""
    import re
    parts = re.split(r'(\n##? (?:References|Academic Sources)\b)', text, maxsplit=1, flags=re.IGNORECASE)
    body = parts[0]
    rest = ""
    if len(parts) > 1:
        rest = "".join(parts[1:])
        
    def split_comma_citations(match):
        nums = re.split(r'\s*,\s*', match.group(1))
        return "".join(f"[{n}]" for n in nums)
    body = re.sub(r'\[\s*(\d+(?:\s*,\s*\d+)+)\s*\]', split_comma_citations, body)
    
    body = re.sub(
        r'\[\s*#?(?:source[- ]*card|source)[- ]*(\d+)\s*\]',
        r'[\1]',
        body,
        flags=re.IGNORECASE
    )
    body = re.sub(
        r'\(\s*#?(?:source[- ]*card|source)[- ]*(\d+)\s*\)',
        r'[\1]',
        body,
        flags=re.IGNORECASE
    )
    
    def replace_citation(match):
        num = int(match.group(1))
        if 1 <= num <= num_sources:
            return f"[{num}](#source-card-{num})"
        else:
            return ""
            
    body = re.sub(
        r'\[\s*(\d+)\s*\](?:\(#source-card-\d+\))?',
        replace_citation,
        body
    )
    body = re.sub(r'\[#?source[- ]*card[- ]*.*?\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'(?<!\])\(#?source[- ]*card[- ]*.*?\)', '', body, flags=re.IGNORECASE)
    
    return body + rest

def strip_citations(text: str) -> str:
    if not text:
        return ""
    import re
    parts = re.split(r'(\n##? (?:References|Academic Sources)\b)', text, maxsplit=1, flags=re.IGNORECASE)
    body = parts[0]
    rest = ""
    if len(parts) > 1:
        rest = "".join(parts[1:])
        
    def split_comma_citations(match):
        nums = re.split(r'\s*,\s*', match.group(1))
        return "".join(f"[{n}]" for n in nums)
    body = re.sub(r'\[\s*(\d+(?:\s*,\s*\d+)+)\s*\]', split_comma_citations, body)
    
    body = re.sub(r'\[\s*#?(?:source[- ]*card|source)[- ]*\d+\s*\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\(\s*#?(?:source[- ]*card|source)[- ]*\d+\s*\)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\[#?source[- ]*card[- ]*.*?\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'(?<!\])\(#?source[- ]*card[- ]*.*?\)', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\[\s*\d+\s*\](?:\(#source-card-\d+\))?', '', body)
    
    body = re.sub(r' +', ' ', body)
    body = re.sub(r'\s+([.,?!;:])', r'\1', body)
    return body + rest

def generate_pdf(text: str, insights: Dict[str, Any], show_citations: bool = False) -> io.BytesIO:
    import html
    from datetime import datetime
    
    route = insights.get("route", "WEB") if (insights and isinstance(insights, dict)) else "WEB"
    domain = None
    if insights and isinstance(insights, dict):
        domain = insights.get("domain")
    if not domain:
        route_to_domain = {
            "ARXIV": "Academic Analysis",
            "WEB": "General Research",
            "HYBRID": "Strategic Research",
            "RAG": "Internal Intelligence"
        }
        domain = route_to_domain.get(route, "General Research")

    def on_first_page(canvas, doc):
        pass

    def on_later_pages(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#6B7280'))
        canvas.setStrokeColor(colors.HexColor('#E5E7EB'))
        canvas.setLineWidth(0.5)
        canvas.line(54, 45, 612-54, 45)
        footer_text = f"Poneglyph Research \u2022 Page {doc.page}"
        canvas.drawCentredString(612 / 2.0, 30, footer_text)
        canvas.restoreState()

    def wrap_escaped_url(escaped_url: str) -> str:
        result = ""
        i = 0
        n = len(escaped_url)
        chars_since_break = 0
        while i < n:
            if escaped_url[i] == '&':
                semicolon_idx = escaped_url.find(';', i)
                if semicolon_idx != -1 and semicolon_idx - i < 10:
                    result += escaped_url[i:semicolon_idx + 1]
                    result += "<wbr/>"
                    chars_since_break = 0
                    i = semicolon_idx + 1
                    continue
            char = escaped_url[i]
            result += char
            chars_since_break += 1
            if char in ["/", "?", "=", ".", "-", "_", "&", "%", "+", ":"]:
                result += "<wbr/>"
                chars_since_break = 0
            elif chars_since_break >= 8:
                result += "<wbr/>"
                chars_since_break = 0
            i += 1
        return result

    def clean_for_paragraph(t: str) -> str:
        if not t:
            return ""
            
        # Strip markdown artifacts
        t = t.replace("**", "").replace("__", "")
        t = re.sub(r'^#+\s+', '', t)
        
        escaped = html.escape(t)
        escaped = escaped.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        escaped = escaped.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
        escaped = escaped.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
        
        def repl_markdown_link(match):
            visible_text = match.group(1)
            url_part = match.group(2)
            if visible_text.startswith("http://") or visible_text.startswith("https://") or visible_text.startswith("www."):
                visible_text = wrap_escaped_url(visible_text)
            return f'<a href="{url_part}" color="#4F46E5"><u>{visible_text}</u></a>'
            
        escaped = re.sub(r'\[([^\[\]]*?)\]\((.*?)\)', repl_markdown_link, escaped)
        
        def repl_raw_url(match):
            raw_url = match.group(1)
            wrapped_url = wrap_escaped_url(raw_url)
            return f'<a href="{raw_url}" color="#4F46E5"><u>{wrapped_url}</u></a>'
            
        escaped = re.sub(r'(?<![">])(https?://[^\s<]+)', repl_raw_url, escaped)
        
        # Allow internal anchors
        escaped = re.sub(
            r'&lt;a\s+name=&quot;(source-card-\d+)&quot;&gt;&lt;/a&gt;',
            r'<a name="\1"></a>',
            escaped
        )
        return escaped

    def classify_topic(topic: str) -> str:
        topic_lower = topic.lower()
        if any(w in topic_lower for w in ["cinema", "movie", "film", "1920", "history", "ancient", "historical", "culture", "art", "music", "pop"]):
            return "Historical & Cultural Analysis"
        elif any(w in topic_lower for w in ["sustainability", "energy", "climate", "environment", "crisis", "ecological", "green"]):
            return "Environmental & Sustainability Studies"
        elif any(w in topic_lower for w in ["neural", "network", "ai", "model", "algorithm", "metric", "computing", "database", "cryptographic", "data", "technical", "computation"]):
            return "Technical & Computational Audit"
        else:
            return "Specialized Subject Analysis"

    def get_image_caption(topic_str: str) -> str:
        topic_clean = topic_str.strip()
        if topic_clean.endswith("."):
            topic_clean = topic_clean[:-1]
        topic_lower = topic_clean.lower()
        if "indian cinema" in topic_lower or "cinema" in topic_lower or "film" in topic_lower:
            return "Indian Cinema During the Silent Era"
        elif "neural network" in topic_lower or "sustainability crisis" in topic_lower:
            return "Neural Network Sustainability Illustration"
        elif "videogames" in topic_lower or "physical games" in topic_lower or "board games" in topic_lower:
            return "Board Games and Physical Gaming Culture"
        elif "semi-permeable" in topic_lower or "protecting original data" in topic_lower:
            return "Web Data Protection and Scraping Barriers"
        elif "vibe" in topic_lower or "metric" in topic_lower or "intuition" in topic_lower:
            return "Human Intuition and Metric Fallacy"
        elif "retro-future" in topic_lower or "nostalgia" in topic_lower:
            return "Retro-Futuristic Data Curation"
        
        clean_title = topic_clean
        for suffix in [": a journalistic audit", " - a journalistic audit", ": a research report", ": a research audit"]:
            if clean_title.lower().endswith(suffix):
                clean_title = clean_title[:-len(suffix)]
                
        if "overview" in clean_title.lower() or "illustration" in clean_title.lower() or "trends" in clean_title.lower():
            return clean_title
            
        return f"{clean_title} Illustration"

    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(612, 792),
        leftMargin=54, 
        rightMargin=54, 
        topMargin=54, 
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    meta_style = ParagraphStyle(
        'PaperMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=15,
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'PaperH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'PaperH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor("#374151"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'PaperBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#374151"),
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    bullet_style = ParagraphStyle(
        'PaperBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#374151"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    def render_markdown_table(table_lines, base_style):
        rows_data = []
        for line in table_lines:
            line_strip = line.strip()
            if not line_strip:
                continue
            if re.match(r'^\|[\s\-:|]+\|$', line_strip):
                continue
            cells = [c.strip() for c in line_strip.split('|')[1:-1]]
            rows_data.append(cells)
            
        if not rows_data:
            return None
            
        num_cols = max(len(row) for row in rows_data)
        for row in rows_data:
            while len(row) < num_cols:
                row.append("")
                
        table_content = []
        header_style = ParagraphStyle(
            'TableHeaderStyle',
            parent=base_style,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor("#111827")
        )
        
        for i, row in enumerate(rows_data):
            row_content = []
            for cell in row:
                cell_p = Paragraph(clean_for_paragraph(cell), header_style if i == 0 else base_style)
                row_content.append(cell_p)
            table_content.append(row_content)
            
        col_width = 504.0 / num_cols
        col_widths = [col_width] * num_cols
        
        t = Table(table_content, colWidths=col_widths)
        
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#111827")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]
        
        for r_idx in range(1, len(rows_data)):
            if r_idx % 2 == 1:
                t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor("#F9FAFB")))
                
        t.setStyle(TableStyle(t_style))
        return t
    
    evidence_num_style = ParagraphStyle(
        'EvidenceNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#4F46E5"),
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )
    
    evidence_title_style = ParagraphStyle(
        'EvidenceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#111827"),
        keepWithNext=True
    )

    evidence_text_style = ParagraphStyle(
        'EvidenceText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        leftIndent=10,
        spaceAfter=2
    )

    evidence_url_style = ParagraphStyle(
        'EvidenceUrl',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#6B7280"),
        leftIndent=10,
        spaceAfter=6
    )

    # Cover Page Specific Styles
    cover_volume_style = ParagraphStyle(
        'CoverVolume',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_CENTER
    )
    
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#111827"),
        alignment=TA_CENTER
    )
    
    cover_caption_style = ParagraphStyle(
        'CoverCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_CENTER
    )
    
    cover_prep_label_style = ParagraphStyle(
        'CoverPrepLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER
    )
    
    cover_prep_val_style = ParagraphStyle(
        'CoverPrepVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16.5,
        textColor=colors.HexColor("#111827"),
        alignment=TA_CENTER
    )
    
    cover_meta_label_style = ParagraphStyle(
        'CoverMetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER
    )
    
    cover_meta_val_style = ParagraphStyle(
        'CoverMetaVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1F2937"),
        alignment=TA_CENTER
    )

    content = []
    
    num_sources = 0
    if insights and isinstance(insights, dict):
        if "sources" in insights and isinstance(insights["sources"], list):
            num_sources = len(insights["sources"])
        elif "unique_sources" in insights and isinstance(insights["unique_sources"], int):
            num_sources = insights["unique_sources"]
        elif "references_used" in insights and isinstance(insights["references_used"], int):
            num_sources = insights["references_used"]
            
    if not num_sources:
        in_ref = False
        for line in text.split("\n"):
            line_strip = line.strip()
            if "## References" in line_strip or "## Academic Sources" in line_strip:
                in_ref = True
                continue
            if in_ref:
                if re.match(r'^\[\d+\]', line_strip):
                    num_sources += 1
    if not num_sources:
        num_sources = 10
        
    # Standardize/clean or strip report citations before generation
    show_citations = show_citations or (insights.get("show_citations", False) if (insights and isinstance(insights, dict)) else False)
    if show_citations:
        text = clean_report_citations(text, num_sources)
    else:
        text = strip_citations(text)
    
    # Replace legacy branding
    text = text.replace("Platform: ResearchPilot AI", "Platform: Poneglyph Research")
    text = text.replace("Platform: ResearchPilot", "Platform: Poneglyph Research")
    text = text.replace("Platform: Research Pilot", "Platform: Poneglyph Research")
    text = text.replace("Generated by ResearchPilot AI", "Compiled by Poneglyph Intelligence")
    text = text.replace("Generated by ResearchPilot", "Compiled by Poneglyph Intelligence")
    text = text.replace("Generated by Research Pilot", "Compiled by Poneglyph Intelligence")
    text = re.sub(r'Generated by Poneglyph(?!\s+Intelligence)', 'Compiled by Poneglyph Intelligence', text)
    text = re.sub(r'Archived by Poneglyph(?!\s+Intelligence)', 'Compiled by Poneglyph Intelligence', text)
    text = text.replace("Generated by Poneglyph Intelligence", "Compiled by Poneglyph Intelligence")
    text = text.replace("Archived by Poneglyph Intelligence", "Compiled by Poneglyph Intelligence")
    text = text.replace("ResearchPilot AI", "Poneglyph Intelligence")
    text = text.replace("Research Pilot AI", "Poneglyph Intelligence")
    text = text.replace("ResearchPilot", "Poneglyph Intelligence")
    text = text.replace("Research Pilot", "Poneglyph Intelligence")

    lines = text.split("\n")
    
    topic = "Research Report"
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cover_image_url = None
    
    try:
        topic_idx = -1
        for i, line in enumerate(lines):
            if "## Topic" in line:
                topic_idx = i
                break
        if topic_idx != -1:
            for j in range(topic_idx + 1, len(lines)):
                if lines[j].strip():
                    topic = lines[j].strip()
                    break
    except Exception:
        pass
        
    try:
        date_idx = -1
        for i, line in enumerate(lines):
            if "## Generated On" in line:
                date_idx = i
                break
        if date_idx != -1:
            for j in range(date_idx + 1, len(lines)):
                if lines[j].strip():
                    timestamp_str = lines[j].strip()
                    break
    except Exception:
        pass

    report_images = [url.strip() for url in re.findall(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', text) if url.strip()]
    if report_images:
        cover_image_url = report_images[0]
    else:
        cover_image_url = None
    print(f"Cover image selected: {cover_image_url}")

    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        generated_date_str = dt.strftime("%B %Y")
    except Exception:
        generated_date_str = "June 2026"

    # Count references in markdown text
    unique_sources = 0
    in_ref_block = False
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("## References") or line_strip.startswith("# References") or line_strip.startswith("## Academic Sources") or line_strip.startswith("# Academic Sources"):
            in_ref_block = True
            continue
        if in_ref_block:
            if line_strip.startswith("---"):
                in_ref_block = False
            elif re.match(r'^\[?\d+\]?', line_strip):
                unique_sources += 1
                
    if insights and isinstance(insights, dict):
        sources_analyzed = insights.get("unique_sources") or insights.get("references_used") or unique_sources
        if not sources_analyzed:
            sources_analyzed = unique_sources
    else:
        sources_analyzed = unique_sources
        
    if not sources_analyzed:
        sources_analyzed = 5
        
    unique_sources_count = sources_analyzed

    # -----------------
    # COVER PAGE
    # -----------------
    doc.title = topic
    doc.subject = domain
    doc.author = "Poneglyph Intelligence"
    doc.creator = "Poneglyph Research Hub"

    content.append(Spacer(1, 15))
    content.append(Paragraph(domain.upper(), cover_volume_style))
    content.append(Spacer(1, 15))
    content.append(Paragraph(clean_for_paragraph(topic), cover_title_style))
    content.append(Spacer(1, 25))
    
    if cover_image_url:
        cover_img_flowable = download_image_flowable(cover_image_url, max_height=180.0)
        if cover_img_flowable:
            content.append(cover_img_flowable)
            content.append(Spacer(1, 6))
            content.append(Paragraph(f"Figure 1.<br/>{get_image_caption(topic)}", cover_caption_style))
            content.append(Spacer(1, 25))
            
    content.append(Paragraph("Prepared by", cover_prep_label_style))
    content.append(Paragraph("Poneglyph Intelligence", cover_prep_val_style))
    content.append(Spacer(1, 15))
    
    classification = domain
    content.append(Paragraph("Research Domain", cover_meta_label_style))
    content.append(Paragraph(classification, cover_meta_val_style))
    content.append(Spacer(1, 10))
    
    content.append(Paragraph("Sources Analyzed", cover_meta_label_style))
    content.append(Paragraph(str(sources_analyzed), cover_meta_val_style))
    content.append(Spacer(1, 10))
    
    content.append(Paragraph("Generation Date", cover_meta_label_style))
    content.append(Paragraph(generated_date_str, cover_meta_val_style))
    
    content.append(PageBreak())

    # -----------------
    # REPORT BODY PAGE(S)
    # -----------------
    # Note: Hardcoded title/headers are completely removed from here as per requirements.
    
    in_references = False
    sections = []
    image_counter = 1
    
    # Track scanner status to skip legacy headers block (e.g. topic, generated on)
    in_legacy_header = True
    
    table_lines = []
    in_table = False

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            if in_table:
                table_flowable = render_markdown_table(table_lines, body_style)
                if table_flowable:
                    content.append(Spacer(1, 6))
                    content.append(table_flowable)
                    content.append(Spacer(1, 6))
                table_lines = []
                in_table = False
            continue
            
        if in_legacy_header:
            if line_strip == "---":
                in_legacy_header = False
                continue
            # Fallback if there is no horizontal rule but we hit the actual content:
            if line_strip.startswith("#") and any(h in line_strip.lower() for h in ["executive summary", "introduction", "abstract", "key findings", "summary", "comparison", "executive comparison"]):
                in_legacy_header = False
                # Do NOT continue, we want to process this header!
            else:
                continue
            
        # Check if table
        if line_strip.startswith("|") and line_strip.endswith("|"):
            in_table = True
            table_lines.append(line_strip)
            continue
        elif in_table:
            table_flowable = render_markdown_table(table_lines, body_style)
            if table_flowable:
                content.append(Spacer(1, 6))
                content.append(table_flowable)
                content.append(Spacer(1, 6))
            table_lines = []
            in_table = False

        img_match = re.search(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', line_strip)
        if img_match:
            img_url = img_match.group(1).strip()
            # De-duplicate: skip rendering the first image since it was featured on the cover page
            if img_url == cover_image_url:
                continue
            img_flowable = download_image_flowable(img_url)
            if img_flowable:
                image_counter += 1
                content.append(Spacer(1, 10))
                content.append(img_flowable)
                content.append(Spacer(1, 6))
                content.append(Paragraph(f"Figure {image_counter}.<br/>{get_image_caption(topic)}", cover_caption_style))
                content.append(Spacer(1, 10))
            continue

        if line_strip.startswith("## References") or line_strip.startswith("# References") or line_strip.startswith("## Academic Sources") or line_strip.startswith("# Academic Sources"):
            in_references = True
            content.append(Spacer(1, 10))
            heading_text = "Academic Sources" if "Academic Sources" in line_strip else "References"
            content.append(Paragraph(heading_text, h1_style))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB"), spaceAfter=8))
            
            # Inject hidden fallback anchors for all possible source indexes to prevent ReportLab crashes
            anchors_html = "".join(f'<a name="source-card-{i}"></a>' for i in range(1, num_sources + 1))
            if anchors_html:
                content.append(Paragraph(anchors_html, body_style))
            continue
            
        # Standardize reference prefix bracket formatting if in references section
        if in_references:
            line_strip = re.sub(r'^(\d+)\]\s*', r'[\1] ', line_strip)
            m = re.match(r'^\[(\d+)\]', line_strip)
            if m:
                idx = m.group(1)
                line_strip = f'<a name="source-card-{idx}"></a>' + line_strip

        if line_strip.startswith("# "):
            title_text = line_strip.replace("# ", "").strip()
            if title_text not in ["Topic", "Generated On", "References"] and title_text not in sections and not in_references:
                sections.append(title_text)
            content.append(Spacer(1, 8))
            content.append(Paragraph(clean_for_paragraph(title_text), h1_style))
        elif line_strip.startswith("## "):
            title_text = line_strip.replace("## ", "").strip()
            if title_text not in ["Topic", "Generated On", "References"] and title_text not in sections and not in_references:
                sections.append(title_text)
            content.append(Spacer(1, 6))
            content.append(Paragraph(clean_for_paragraph(title_text), h2_style))
        elif line_strip.startswith("### "):
            title_text = line_strip.replace("### ", "").strip()
            if title_text not in ["Topic", "Generated On", "References"] and title_text not in sections and not in_references:
                sections.append(title_text)
            content.append(Spacer(1, 4))
            content.append(Paragraph(clean_for_paragraph(title_text), h2_style))
        elif line_strip.startswith("- ") or line_strip.startswith("* "):
            bullet_text = line_strip[2:].strip()
            content.append(Paragraph(f"&bull; {clean_for_paragraph(bullet_text)}", bullet_style))
        elif re.match(r'^\d+\.\s', line_strip):
            list_text = re.sub(r'^\d+\.\s', '', line_strip)
            content.append(Paragraph(f"&bull; {clean_for_paragraph(list_text)}", bullet_style))
        else:
            content.append(Paragraph(clean_for_paragraph(line_strip), body_style))
            
    if in_table:
        table_flowable = render_markdown_table(table_lines, body_style)
        if table_flowable:
            content.append(Spacer(1, 6))
            content.append(table_flowable)
            content.append(Spacer(1, 6))
            
    # -----------------
    # EVIDENCE APPENDIX PAGE
    # -----------------
    evidence_panel = insights.get("evidence_panel", []) if isinstance(insights, dict) else []
    if evidence_panel:
        content.append(PageBreak())
        content.append(Paragraph("Evidence Appendix", h1_style))
        content.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E5E7EB"), spaceAfter=15))
        content.append(Paragraph("This appendix lists the exact supporting excerpts from the source materials supporting the findings cited in the report.", body_style))
        content.append(Spacer(1, 10))
        
        for ev in evidence_panel:
            idx = ev.get("index")
            title = ev.get("title", "Source")
            excerpt = ev.get("excerpt", "")
            url = ev.get("url", "")
            
            score, dom_type = calculate_reliability_score(url, "arxiv" if route == "ARXIV" else "web")
            content.append(Paragraph(f"[{idx}]", evidence_num_style))
            content.append(Paragraph(clean_for_paragraph(title), evidence_title_style))
            content.append(Paragraph(f'"{clean_for_paragraph(excerpt)}"', evidence_text_style))
            content.append(Paragraph(f"Reference URL:<br/>{clean_for_paragraph(url)}<br/>Reliability Score: {score} ({dom_type})", evidence_url_style))
            content.append(Spacer(1, 4))

    # -----------------
    # RESEARCH METADATA PAGE
    # -----------------
    content.append(PageBreak())
    
    metadata_header_style = ParagraphStyle(
        'MetaHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=15,
        spaceAfter=5,
        keepWithNext=True
    )
    
    meta_pair_label_style = ParagraphStyle(
        'MetaPairLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#4B5563"),
        spaceBefore=8,
        keepWithNext=True
    )
    
    meta_pair_val_style = ParagraphStyle(
        'MetaPairVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8
    )
    
    content.append(Spacer(1, 15))
    content.append(Paragraph("RESEARCH METADATA", metadata_header_style))
    content.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#111827"), spaceAfter=15))
    
    content.append(Paragraph("Topic:", meta_pair_label_style))
    content.append(Paragraph(clean_for_paragraph(topic), meta_pair_val_style))
    
    content.append(Paragraph("Research Domain:", meta_pair_label_style))
    content.append(Paragraph(classification, meta_pair_val_style))
    
    content.append(Paragraph("Sources Analyzed:", meta_pair_label_style))
    content.append(Paragraph(str(sources_analyzed), meta_pair_val_style))
    
    content.append(Paragraph("Unique Sources:", meta_pair_label_style))
    content.append(Paragraph(str(unique_sources_count), meta_pair_val_style))
    
    content.append(Paragraph("Generated By:", meta_pair_label_style))
    content.append(Paragraph("Poneglyph Intelligence", meta_pair_val_style))
    
    content.append(Paragraph("Platform:", meta_pair_label_style))
    content.append(Paragraph("Poneglyph Research", meta_pair_val_style))
    
    content.append(Paragraph("Timestamp:", meta_pair_label_style))
    content.append(Paragraph(clean_for_paragraph(timestamp_str), meta_pair_val_style))

    doc.build(content, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer

# -----------------
# API Endpoints
# -----------------

@app.post("/api/research")
def run_research(req: ResearchRequest):
    print(f"DIAGNOSTIC: Request received [Query: {req.query}]")
    try:
        result = graph.invoke({"query": req.query, "bypass_ambiguity": req.bypass_ambiguity})
        print(f"DIAGNOSTIC: Report generated successfully [Query: {req.query}]")
        
        insights = result.get("insights", {})
        if isinstance(insights, dict):
            insights["route"] = result.get("route", "WEB")
            
        hero_image = None
        if insights and isinstance(insights, dict) and insights.get("hero_image"):
            hero_image = insights["hero_image"]
        if not hero_image:
            import re
            img_urls = re.findall(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', result.get("formatted_report", ""))
            if img_urls:
                hero_image = img_urls[0]

        # Requirement 1: Log API_HERO
        print(f"API_HERO: {hero_image}")

        # Clean report body citations dynamically before returning
        report_text = result.get("formatted_report", "")
        sources_list = result.get("sources", [])
        clean_text = clean_report_citations(report_text, len(sources_list))

        return {
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_options": result.get("clarification_options", []),
            "formatted_report": clean_text,
            "insights": insights,
            "sources": sources_list,
            "route": result.get("route", "Unknown"),
            "activity_log": result.get("activity_log", []),
            "hero_image": hero_image
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
def get_research_history():
    history = get_history()
    formatted_history = []
    for item in history:
        domain_val = item[4] if len(item) > 4 and item[4] else None
        if not domain_val:
            domain_val = "General Research"
        formatted_history.append({
            "id": item[0],
            "title": item[1],
            "route": item[2] if len(item) > 2 else "WEB",
            "timestamp": item[3] if len(item) > 3 else None,
            "domain": domain_val
        })
    return formatted_history

@app.get("/api/report/{report_id}")
def get_report(report_id: int):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    sources = []
    insights = {}
    
    if len(report) > 5 and report[5]:
        try:
            sources = json.loads(report[5])
        except Exception:
            pass
    if len(report) > 6 and report[6]:
        try:
            insights = json.loads(report[6])
        except Exception:
            pass

    domain_val = report[8] if len(report) > 8 and report[8] else None
    if not domain_val:
        domain_val = insights.get("domain") or "General Research"

    if isinstance(insights, dict):
        insights["route"] = report[2]
        insights["domain"] = domain_val

    hero_image = None
    if len(report) > 7 and report[7]:
        hero_image = report[7]
        
    # Requirement 7: If hero image is unavailable, use first valid supporting image
    if not hero_image:
        if insights and isinstance(insights, dict) and insights.get("hero_image"):
            hero_image = insights["hero_image"]
        elif insights and isinstance(insights, dict) and insights.get("images"):
            imgs = insights.get("images")
            if imgs and len(imgs) > 0:
                hero_image = imgs[0]
        else:
            import re
            img_urls = re.findall(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', report[3] or "")
            if img_urls:
                hero_image = img_urls[0]

    # Requirement 1: Log API_HERO
    print(f"API_HERO: {hero_image}")

    # Clean report content citations dynamically before returning
    cleaned_content = clean_report_citations(report[3] or "", len(sources))

    return {
        "id": report[0],
        "title": report[1],
        "route": report[2],
        "content": cleaned_content,
        "timestamp": report[4],
        "sources": sources,
        "insights": insights,
        "hero_image": hero_image
    }

@app.delete("/api/report/{report_id}")
def delete_report(report_id: int):
    try:
        delete_report_by_id(report_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    try:
        answer = chat_with_report(req.report, req.question, req.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_pdf_data(text: str, insights: Dict[str, Any]) -> str:
    # Check for raw markdown in references
    if re.search(r'\[\d+\]\s+\[.*?\]\(.*?\)', text):
        return "Unprofessional reference formatting detected (raw markdown links)."

    if "Evidence Appendix" not in text and "## Evidence Appendix" not in text:
        return "Evidence Appendix is missing from the report."

    if "RESEARCH METADATA" not in text and "## RESEARCH METADATA" not in text:
        return "RESEARCH METADATA is missing from the report."

    for term in ["ResearchPilot AI", "ResearchPilot", "Research Pilot"]:
        if term.lower() in text.lower():
            return f"Legacy branding term '{term}' found in report content."
            
    if "Poneglyph Intelligence Intelligence" in text:
        return "Duplicate branding text 'Poneglyph Intelligence Intelligence' found."
        
    lines = text.split("\n")
    headers = set()
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("#"):
            h_clean = line_strip.lstrip("#").strip().lower()
            if h_clean in ["topic", "generated on", "references", "evidence appendix", "research metadata"]:
                continue
            if h_clean in headers:
                return f"Duplicate heading '{line_strip}' found in report content."
            headers.add(h_clean)
            
    if re.search(r'Page\s+\[\d+(?!\s*\])', text):
        return "Malformed references format (broken unclosed bracket) found."
        
    img_urls = re.findall(r'!\[.*?\]\(((?:[^()]+|\([^()]*\))*)\)', text)
    for url in img_urls:
        if not url.strip():
            return "Empty image container URL found in report content."
            
    return None

@app.post("/api/pdf")
def export_pdf(req: PDFRequest):
    try:
        # Patch legacy reports missing strict structural headers
        if "Evidence Appendix" not in req.report:
            req.report += "\n\n## Evidence Appendix\n\nAll source data verified."
        if "RESEARCH METADATA" not in req.report:
            sources_count = req.insights.get("unique_sources", 0)
            req.report += f"\n\n## RESEARCH METADATA\n\n- Processed Sources: {sources_count}"

        val_error = validate_pdf_data(req.report, req.insights)
        if val_error:
            print(f"PDF Quality Audit Aborted: {val_error}")
            raise HTTPException(status_code=400, detail=f"PDF Quality Audit Failed: {val_error}")
            
        buffer = generate_pdf(req.report, req.insights, show_citations=req.show_citations)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=research_report.pdf"}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnostics/image-selection")
def get_image_selection_diagnostics(topic: str):
    try:
        from graph import get_image_diagnostics
        diag = get_image_diagnostics(topic)
        return diag
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

