import urllib.parse
from ui.theme import ICONS, COLORS

def render_hero():
    """Renders the premium centered hero landing page layout."""
    return f"""
    <div class="hero-container">
        <div style="margin-bottom: 24px;">{ICONS['logo_icon'].replace('width="28"', 'width="48"').replace('height="28"', 'height="48"')}</div>
        <div class="hero-title">ResearchPilot AI</div>
        <div class="hero-subtitle">Autonomous Multi-Agent Research Platform</div>
        <div class="hero-explanation">
            Transform web data and local knowledge bases into comprehensive, 
            publication-ready research reports using AI-powered workflows.
        </div>
    </div>
    """

def render_compact_header():
    """Renders the compact header for the dashboard view."""
    return f"""
    <div class="compact-header">
        {ICONS['logo_icon']}
        <div class="compact-title">ResearchPilot AI</div>
    </div>
    """

def render_metric_card(title, value_pct, start_color="#6366F1", end_color="#8B5CF6"):
    """Generates a custom glassmorphism metric card with progress bar."""
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value_pct}%</div>
        <div class="metric-progress-bg">
            <div class="metric-progress-fill" style="width: {value_pct}%; background: linear-gradient(90deg, {start_color}, {end_color});"></div>
        </div>
    </div>
    """

def render_source_card(url):
    """Generates a clickable source URL card with external link icon and domain extractor."""
    if not url:
        return ""
        
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or "Local Resource"
        if not domain and url.upper() == "RAG":
            domain = "Knowledge Base"
        elif domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        domain = "Resource Link"
        
    return f"""
    <a href="{url}" target="_blank" class="source-card-link">
        <div class="source-card">
            <div class="source-domain">{domain}</div>
            <div class="source-url">{url}</div>
            <div class="source-icon">
                {ICONS['external_link']}
            </div>
        </div>
    </a>
    """

def render_gap_alert(text):
    """Renders an elegant cyan gap alert card."""
    return f"""
    <div class="insight-alert alert-gap">
        <div class="alert-gap-icon">
            {ICONS['gap']}
        </div>
        <div class="insight-alert-text">{text}</div>
    </div>
    """

def render_contradiction_alert(text):
    """Renders a danger-themed contradiction alert card."""
    return f"""
    <div class="insight-alert alert-contradiction">
        <div class="alert-contradiction-icon">
            {ICONS['contradiction']}
        </div>
        <div class="insight-alert-text">{text}</div>
    </div>
    """

def render_status_badge(agent_name, status):
    """Renders status badges for the system agents inside the sidebar."""
    status_lower = status.lower()
    
    if "waiting" in status_lower:
        badge_class = "status-waiting"
        icon_svg = ICONS['status_waiting']
    elif "running" in status_lower:
        badge_class = "status-running"
        icon_svg = ICONS['status_running']
    else:
        badge_class = "status-complete"
        icon_svg = ICONS['status_complete']
        
    return f"""
    <div class="agent-status-row">
        <span class="agent-name">{agent_name}</span>
        <span class="status-badge {badge_class}">
            {icon_svg} {status}
        </span>
    </div>
    """
