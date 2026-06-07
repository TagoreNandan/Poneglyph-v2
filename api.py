import io
import re
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from graph import graph
from memory.database import get_history, get_report_by_id
from agents.chat_agent import chat_with_report

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

app = FastAPI(title="ResearchPilot AI Backend API")

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
        from reportlab.platypus import Image as RLImage
        from io import BytesIO
        from PIL import Image as PILImage
        
        print(f"Downloading image for PDF: {url}")
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            img_data = BytesIO(resp.content)
            pil_img = PILImage.open(img_data)
            width, height = pil_img.size
            max_width = 400.0
            if width > max_width:
                ratio = max_width / width
                width = max_width
                height = height * ratio
            
            img_data.seek(0)
            return RLImage(img_data, width=width, height=height)
    except Exception as e:
        print(f"Failed to download image flowable for {url}: {e}")
    return None

def generate_pdf(text: str, insights: Dict[str, Any]) -> io.BytesIO:
    buffer = io.BytesIO()
    
    # Letter size with 0.75 in (54 pt) margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(612, 792), # Letter size in points
        leftMargin=54, 
        rightMargin=54, 
        topMargin=54, 
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Academic Styles
    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#111827"), # Slate 900
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    meta_style = ParagraphStyle(
        'PaperMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4B5563"), # Slate 600
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
        textColor=colors.HexColor("#4F46E5"), # Indigo 600
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
            
        # Parse markdown images
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
            
        # Standard markdown mapping
        if line_strip.startswith("# "):
            title_text = line_strip.replace("# ", "").strip()
            content.append(Spacer(1, 8))
            content.append(Paragraph(title_text, h1_style))
        elif line_strip.startswith("## "):
            title_text = line_strip.replace("## ", "").strip()
            content.append(Spacer(1, 6))
            content.append(Paragraph(title_text, h2_style))
        elif line_strip.startswith("### "):
            title_text = line_strip.replace("### ", "").strip()
            content.append(Spacer(1, 4))
            content.append(Paragraph(title_text, h2_style))
        elif line_strip.startswith("- ") or line_strip.startswith("* "):
            bullet_text = line_strip[2:].strip()
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            bullet_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', bullet_text)
            content.append(Paragraph(f"&bull; {bullet_text}", bullet_style))
        elif re.match(r'^\d+\.\s', line_strip):
            list_text = re.sub(r'^\d+\.\s', '', line_strip)
            list_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', list_text)
            list_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', list_text)
            content.append(Paragraph(f"&bull; {list_text}", bullet_style))
        else:
            para_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_strip)
            para_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', para_text)
            content.append(Paragraph(para_text, body_style))
            
    # Evidence Appendix
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
            content.append(Paragraph(title, evidence_title_style))
            content.append(Paragraph(f'"{excerpt}"', evidence_text_style))
            content.append(Paragraph(f"URL: {url}", evidence_url_style))
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
            "title": item[1]
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
