import io
import re
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from graph import graph
from memory.database import get_history, get_report_by_id, init_db
from agents.chat_agent import chat_with_report

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

app = FastAPI(title="ResearchPilot AI Backend API")

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

def download_image_flowable(url: str) -> Any:
    try:
        import requests
        import urllib3
        import base64
        from reportlab.platypus import Image as RLImage, Table, TableStyle
        from io import BytesIO
        from PIL import Image as PILImage
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print(f"Downloading image for PDF: {url}")
        
        pil_img = None
        if url.startswith("data:image/"):
            # Handle inline base64 image data URLs
            try:
                header, encoded = url.split(",", 1)
                data = base64.b64decode(encoded)
                pil_img = PILImage.open(BytesIO(data))
            except Exception as b64_err:
                print(f"Failed to decode base64 image: {b64_err}")
                return None
        else:
            # Handle protocol-relative URLs
            if url.startswith("//"):
                url = "https:" + url
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, verify=False, timeout=8)
            if resp.status_code == 200:
                pil_img = PILImage.open(BytesIO(resp.content))
                
        if pil_img:
            if pil_img.mode not in ("RGB", "RGBA"):
                pil_img = pil_img.convert("RGB")
                
            width, height = pil_img.size
            max_width = 400.0
            max_height = 350.0
            
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

def generate_pdf(text: str, insights: Dict[str, Any]) -> io.BytesIO:
    import html
    
    def clean_for_paragraph(t: str) -> str:
        if not t:
            return ""
        escaped = html.escape(t)
        escaped = escaped.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
        escaped = escaped.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
        escaped = escaped.replace("&lt;u&gt;", "<u>").replace("&lt;/u&gt;", "</u>")
        escaped = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" color="#4F46E5"><u>\1</u></a>', escaped)
        return escaped

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

    content = []
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content.append(Paragraph("RESEARCH REPORT", title_style))
    content.append(Paragraph(f"Generated on: {timestamp} | Platform: ResearchPilot AI", meta_style))
    content.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#E5E7EB"), spaceAfter=15))
    
    lines = text.split("\n")
    in_references = False
    
    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue
            
        img_match = re.search(r'!\[.*?\]\((.*?)\)', line_strip)
        if img_match:
            img_url = img_match.group(1).strip()
            img_flowable = download_image_flowable(img_url)
            if img_flowable:
                content.append(Spacer(1, 10))
                content.append(img_flowable)
                content.append(Spacer(1, 10))
            continue

        if line_strip.startswith("## References") or line_strip.startswith("# References"):
            in_references = True
            content.append(Spacer(1, 10))
            content.append(Paragraph("References", h1_style))
            content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB"), spaceAfter=8))
            continue
            
        if line_strip.startswith("# "):
            title_text = line_strip.replace("# ", "").strip()
            content.append(Spacer(1, 8))
            content.append(Paragraph(clean_for_paragraph(title_text), h1_style))
        elif line_strip.startswith("## "):
            title_text = line_strip.replace("## ", "").strip()
            content.append(Spacer(1, 6))
            content.append(Paragraph(clean_for_paragraph(title_text), h2_style))
        elif line_strip.startswith("### "):
            title_text = line_strip.replace("### ", "").strip()
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
            
            content.append(Paragraph(f"[{idx}]", evidence_num_style))
            content.append(Paragraph(clean_for_paragraph(title), evidence_title_style))
            content.append(Paragraph(f'"{clean_for_paragraph(excerpt)}"', evidence_text_style))
            content.append(Paragraph(f"URL: {clean_for_paragraph(url)}", evidence_url_style))
            content.append(Spacer(1, 4))

    doc.build(content)
    buffer.seek(0)
    return buffer

# -----------------
# API Endpoints
# -----------------

@app.post("/api/research")
def run_research(req: ResearchRequest):
    try:
        result = graph.invoke({"query": req.query, "bypass_ambiguity": req.bypass_ambiguity})
        return {
            "needs_clarification": result.get("needs_clarification", False),
            "clarification_options": result.get("clarification_options", []),
            "formatted_report": result.get("formatted_report", ""),
            "insights": result.get("insights", {}),
            "sources": result.get("sources", []),
            "route": result.get("route", "Unknown"),
            "activity_log": result.get("activity_log", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
def get_research_history():
    history = get_history()
    formatted_history = []
    for item in history:
        formatted_history.append({
            "id": item[0],
            "title": item[1],
            "route": item[2] if len(item) > 2 else "WEB",
            "timestamp": item[3] if len(item) > 3 else None
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

    return {
        "id": report[0],
        "title": report[1],
        "route": report[2],
        "content": report[3],
        "timestamp": report[4],
        "sources": sources,
        "insights": insights
    }

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    try:
        answer = chat_with_report(req.report, req.question, req.history)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf")
def export_pdf(req: PDFRequest):
    try:
        buffer = generate_pdf(req.report, req.insights)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=research_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
