import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, Archive, Folder, Settings, Download, FileText, Activity, AlertCircle, ArrowRight, MessageSquare, Loader, X, ExternalLink, ChevronRight, HelpCircle, ShieldAlert } from 'lucide-react';
import { fetchHistory, fetchReport, generateResearch, sendChat, downloadPDF } from './api';
import './index.css';

// Client-side report parser to map metadata and separate images (Goal & Step 4 Rules)
const parseReportMarkdown = (markdown, fallbackTopic = '') => {
  if (!markdown) return { topic: '', date: '', body: '', references: '', images: [] };

  // 1. Extract all image URLs
  const imgRegex = /!\[.*?\]\((.*?)\)/g;
  const images = [];
  let match;
  while ((match = imgRegex.exec(markdown)) !== null) {
    images.push(match[1]);
  }

  // 2. Clean markdown text of image links
  let cleaned = markdown.replace(/!\[.*?\]\((.*?)\)/g, '');

  let topic = fallbackTopic;
  let date = '';
  let body = cleaned;
  let references = '';

  // 3. Divide content using '---' as divider
  const parts = cleaned.split('---');
  if (parts.length >= 2) {
    const headerPart = parts[0] || '';
    
    const topicMatch = headerPart.match(/## Topic\s*([\s\S]*?)(?=## Generated On|$)/i);
    if (topicMatch && topicMatch[1]) {
      topic = topicMatch[1].trim();
    }

    const dateMatch = headerPart.match(/## Generated On\s*([\s\S]*?)$/i);
    if (dateMatch && dateMatch[1]) {
      date = dateMatch[1].trim();
    }

    const remaining = parts.slice(1).join('---');
    const refIndex = remaining.lastIndexOf('## References');
    if (refIndex !== -1) {
      body = remaining.substring(0, refIndex).trim();
      references = remaining.substring(refIndex).trim();
    } else {
      body = remaining.trim();
    }
  } else {
    // Fallback split
    const refIndex = cleaned.lastIndexOf('## References');
    if (refIndex !== -1) {
      body = cleaned.substring(0, refIndex).trim();
      references = cleaned.substring(refIndex).trim();
    }
  }

  // Strip leading headers like "# Research Report" from body if present
  body = body.replace(/^#\s+Research\s+Report\s*/i, '').trim();

  return { topic, date, body, references, images };
};

const staticFeaturedReport = {
  id: "featured-sustainability",
  title: "The Neural Network Sustainability Crisis: A Journalistic Audit",
  route: "WEB",
  content: `# Research Report

## Topic

The Neural Network Sustainability Crisis: A Journalistic Audit

## Generated On

2026-06-07 12:00:00

---

![Image](https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop)

### Executive Summary
The rapid scale-up of generative neural networks has triggered a quiet sustainability crisis. While public focus remains on operational carbon emissions from data centers, a deeper threat lies in the linguistic and cognitive ecosystem: the dilution of original data layers. This audit explores the dual crises of physical energy resource depletion and training data degradation.

### 1. Physical Sustainability and Energy Constraints
Data centers powering frontier models consume vast amounts of electricity and water. As of 2026, training a single next-generation foundation model requires gigawatt-hour scale footprints, straining local grids [1]. In regions like Ireland and Virginia, data center demand threatens grid stability, forcing operators to invest in dedicated nuclear power or grid-scale battery arrays [2].

### 2. The Semantic Sustainability Crisis (Model Collapse)
Linguistic sustainability is equally threatened. As AI-generated content saturates the web, future models are inevitably trained on their own outputs. This recursive training loop induces "model collapse" — a degenerative process where models lose representation of rare or nuanced linguistic structures, leading to cognitive simplification and homogenized outputs [3][4]. Protecting original, human-crafted data layers has become the digital equivalent of preserving seed vaults.

## References

[1] Marfa Institute for Digital Humanities (2025). *Operational energy footprints of generative foundations*. [Source Link](https://silentfilmcalendar.org/reviews/operational-energy-footprints)
[2] Vance, E. (2026). *Recursive loops: The linguistic debt of automated web scraping*. [Source Link](https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt)
[3] Kyoto Archive Lab (2025). *Artisanal data layers: The protection of human expression*. [Source Link](https://www.wfcn.co/ccp/article/artisanal-data-layers)
[4] Carter, R. et al. (2024). *Model collapse in recursive architectures*. [Source Link](https://en.as.com/meristation/news/model-collapse-recursive)`,
  sources: [
    {
      title: "Operational energy footprints of generative foundations",
      url: "https://silentfilmcalendar.org/reviews/operational-energy-footprints"
    },
    {
      title: "Recursive loops: The linguistic debt of automated web scraping",
      url: "https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt"
    },
    {
      title: "Artisanal data layers: The protection of human expression",
      url: "https://www.wfcn.co/ccp/article/artisanal-data-layers"
    },
    {
      title: "Model collapse in recursive architectures",
      url: "https://en.as.com/meristation/news/model-collapse-recursive"
    }
  ],
  insights: {
    word_count: 280,
    references_used: 4,
    unique_sources: 4,
    average_source_freshness: 2025.0,
    citation_density: 0.08,
    evidence_coverage: 0.75,
    evidence_panel: [
      {
        index: 1,
        title: "Operational energy footprints of generative foundations",
        url: "https://silentfilmcalendar.org/reviews/operational-energy-footprints",
        excerpt: "Training next-generation foundation models requires gigawatt-hour scale footprints, straining local grids."
      },
      {
        index: 2,
        title: "Recursive loops: The linguistic debt of automated web scraping",
        url: "https://www.slideshare.net/slideshow/recursive-loops-linguistic-debt",
        excerpt: "Operator demand threatens grid stability, forcing investment in dedicated energy grids."
      },
      {
        index: 3,
        title: "Artisanal data layers: The protection of human expression",
        url: "https://www.wfcn.co/ccp/article/artisanal-data-layers",
        excerpt: "As AI-generated content saturates the web, future models are inevitably trained on their own outputs."
      },
      {
        index: 4,
        title: "Model collapse in recursive architectures",
        url: "https://en.as.com/meristation/news/model-collapse-recursive",
        excerpt: "Recursive training loops induce model collapse, losing representation of rare structures."
      }
    ]
  }
};

function App() {
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeReport, setActiveReport] = useState(null);
  const [activeReportId, setActiveReportId] = useState(null);
  const [route, setRoute] = useState(null);
  const [activityLog, setActivityLog] = useState([]);
  const [activeTopic, setActiveTopic] = useState('');
  const [timestamp, setTimestamp] = useState('');
  const [historySearch, setHistorySearch] = useState('');
  const [insights, setInsights] = useState(null);
  const [sources, setSources] = useState([]);
  const [error, setError] = useState(null);
  
  // Navigation
  const [activeNav, setActiveNav] = useState('archives');
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);

  const [bypassClarification, setBypassClarification] = useState(() => {
    return localStorage.getItem('bypassClarification') === 'true';
  });

  const searchInputRef = useRef(null);

  useEffect(() => {
    const handlePopState = (event) => {
      if (event.state) {
        const state = event.state;
        setActiveNav(state.activeNav ?? 'archives');
        setActiveReport(state.activeReport ?? null);
        setActiveReportId(state.activeReportId ?? null);
        setActiveTopic(state.activeTopic ?? '');
        setRoute(state.route ?? null);
        setInsights(state.insights ?? null);
        setSources(state.sources ?? []);
        setSelectedCollection(state.selectedCollection ?? null);
        setTimestamp(state.timestamp ?? '');
      } else {
        setActiveNav('archives');
        setActiveReport(null);
        setActiveReportId(null);
        setActiveTopic('');
        setRoute(null);
        setInsights(null);
        setSources([]);
        setSelectedCollection(null);
        setTimestamp('');
      }
    };

    window.addEventListener('popstate', handlePopState);
    
    if (!window.history.state) {
      window.history.replaceState({
        activeNav: 'archives',
        activeReportId: null,
        activeReport: null,
        activeTopic: '',
        route: null,
        insights: null,
        sources: [],
        selectedCollection: null,
        timestamp: ''
      }, "");
    }

    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  const handleBypassToggle = (val) => {
    setBypassClarification(val);
    localStorage.setItem('bypassClarification', val ? 'true' : 'false');
  };

  const getReportCategory = (item) => {
    if (!item || !item.title) return 'Culture';
    const title = item.title.toLowerCase();
    
    if (item.route === 'ARXIV' || title.includes('arxiv') || title.includes('paper') || title.includes('scientific')) {
      return 'Academic';
    }
    if (title.includes('history') || title.includes('ancient') || title.includes('retro') || title.includes('nostalgia') || title.includes('decade') || title.includes('1920') || title.includes('century') || title.includes('cinema')) {
      return 'History';
    }
    if (title.includes('neural') || title.includes('sustainability') || title.includes('web') || title.includes('cryptographic') || title.includes('data') || title.includes('quantum') || title.includes('crispr') || title.includes('technology') || title.includes('model') || title.includes('network') || title.includes('algorithmic') || title.includes('linux')) {
      return 'Technology';
    }
    if (title.includes('cinema') || title.includes('movie') || title.includes('film') || title.includes('pop') || title.includes('music') || title.includes('entertainment') || title.includes('autobots') || title.includes('decepticons')) {
      return 'Entertainment';
    }
    return 'Culture';
  };

  // Follow-up chat drawer open/close
  const [chatOpen, setChatOpen] = useState(false);

  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [clarificationOptions, setClarificationOptions] = useState([]);
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [manualTopic, setManualTopic] = useState('');
  const [addedQuestions, setAddedQuestions] = useState(new Set());

  // Scroll progress tracker
  const [scrollProgress, setScrollProgress] = useState(0);

  const chatEndRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const loadHistory = async () => {
    try {
      const data = await fetchHistory();
      setHistory(data ?? []);
    } catch (err) {
      console.error(err);
      setHistory([]);
    }
  };

  const handleScroll = (e) => {
    const target = e.target;
    const totalHeight = target.scrollHeight - target.clientHeight;
    if (totalHeight > 0) {
      const progress = (target.scrollTop / totalHeight) * 100;
      setScrollProgress(progress);
    } else {
      setScrollProgress(0);
    }
  };

  const handleArchiveClick = async (topicTitle) => {
    const match = (history || []).find(
      (item) => item && item.title && item.title.toLowerCase().trim() === topicTitle.toLowerCase().trim()
    );
    if (match) {
      await handleSelectHistory(match.id);
    } else {
      await handleGenerate(null, topicTitle);
    }
  };

  const handleGenerate = async (e, forcedQuery = null, bypass_ambiguity = null) => {
    e?.preventDefault();
    const q = forcedQuery || query;
    if (!q.trim()) return;
    
    setQuery(q);
    setError(null);
    setIsLoading(true);
    setActiveReport(null);
    setActiveReportId(null);
    setInsights(null);
    setSources([]);
    setChatHistory([]);
    setClarificationOptions([]);
    setAddedQuestions(new Set());
    setScrollProgress(0);
    setChatOpen(false);
    
    const shouldBypass = bypass_ambiguity !== null ? bypass_ambiguity : bypassClarification;
    
    try {
      const data = await generateResearch(q, shouldBypass);
      
      if (data.needs_clarification) {
        setClarificationOptions(data.clarification_options || []);
        setIsLoading(false);
        return;
      }
      
      if (!data.formatted_report || 
          data.formatted_report.includes("Research generation failed") || 
          data.formatted_report.includes("temporarily unavailable") || 
          data.formatted_report.includes("No report was generated")) {
        setError("Report generation temporarily unavailable. All research providers are currently busy or unavailable. Please try again later.");
        setIsLoading(false);
        return;
      }
      
      setActiveNav('archives');
      setActiveReport(data.formatted_report);
      setInsights(data.insights);
      setSources(data.sources || []);
      setRoute(data.route || null);
      setActivityLog(data.activity_log || []);
      setActiveTopic(q);
      
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      setTimestamp(timeStr);
      
      window.history.pushState({
        activeNav: 'archives',
        activeReportId: null,
        activeReport: data.formatted_report,
        activeTopic: q,
        route: data.route || null,
        insights: data.insights || null,
        sources: data.sources || [],
        selectedCollection: selectedCollection,
        timestamp: timeStr
      }, "");
      
      loadHistory();
    } catch (err) {
      console.error(err);
      setError("Report generation temporarily unavailable. All research providers are currently busy or unavailable. Please try again later.");
    }
    setIsLoading(false);
  };

  const handleSelectHistory = async (id) => {
    setError(null);
    setIsLoading(true);
    setScrollProgress(0);
    setChatOpen(false);
    
    const nextNav = activeNav;
    
    try {
      const report = await fetchReport(id);
      
      const newTimestamp = report.timestamp ? new Date(report.timestamp).toLocaleDateString([], {year: 'numeric', month: 'long', day: 'numeric'}) : '';
      
      setActiveReport(report.content);
      setActiveReportId(id);
      setRoute(report.route || null);
      setActivityLog([]);
      setInsights(report.insights || null);
      setActiveTopic(report.title || '');
      setAddedQuestions(new Set());
      setTimestamp(newTimestamp);
      setSources(report.sources || []);
      setChatHistory([]);
      
      window.history.pushState({
        activeNav: nextNav,
        activeReportId: id,
        activeReport: report.content,
        activeTopic: report.title || '',
        route: report.route || null,
        insights: report.insights || null,
        sources: report.sources || [],
        selectedCollection: selectedCollection,
        timestamp: newTimestamp
      }, "");
    } catch (err) {
      console.error(err);
      setError("Failed to load the requested report. Please try again later.");
    }
    setIsLoading(false);
  };

  const handleFeaturedClick = () => {
    setError(null);
    setIsLoading(false);
    setScrollProgress(0);
    setChatOpen(false);
    setActiveNav('archives');
    
    const report = staticFeaturedReport;
    setActiveReport(report.content);
    setActiveReportId(report.id);
    setRoute(report.route);
    setActivityLog([]);
    setInsights(report.insights);
    setActiveTopic(report.title);
    setAddedQuestions(new Set());
    setTimestamp("June 8, 2026");
    setSources(report.sources);
    setChatHistory([]);
    
    window.history.pushState({
      activeNav: 'archives',
      activeReportId: report.id,
      activeReport: report.content,
      activeTopic: report.title,
      route: report.route,
      insights: report.insights,
      sources: report.sources,
      selectedCollection: selectedCollection,
      timestamp: "June 8, 2026"
    }, "");
  };

  const handleNavClick = (nav) => {
    setActiveNav(nav);
    setActiveReport(null);
    setActiveReportId(null);
    setError(null);
    window.history.pushState({
      activeNav: nav,
      activeReportId: null,
      activeReport: null,
      activeTopic: '',
      route: null,
      insights: null,
      sources: [],
      selectedCollection: null,
      timestamp: ''
    }, "");
  };

  const handleSelectCollection = (name) => {
    setSelectedCollection(name);
    window.history.pushState({
      activeNav: 'collections',
      activeReportId: null,
      activeReport: null,
      activeTopic: '',
      route: null,
      insights: null,
      sources: [],
      selectedCollection: name,
      timestamp: ''
    }, "");
  };

  const handleNewSearch = () => {
    setActiveReport(null);
    setActiveReportId(null);
    setQuery('');
    setError(null);
    setActiveNav('archives');
    window.history.pushState({
      activeNav: 'archives',
      activeReportId: null,
      activeReport: null,
      activeTopic: '',
      route: null,
      insights: null,
      sources: [],
      selectedCollection: null,
      timestamp: ''
    }, "");
    setTimeout(() => {
      searchInputRef.current?.focus();
    }, 50);
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !activeReport) return;
    
    const userMsg = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { question: userMsg, answer: '...' }]);
    
    try {
      const res = await sendChat(activeReport, userMsg, chatHistory.filter(c => c.answer !== '...'));
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].answer = res.answer;
        return newHist;
      });
    } catch (err) {
      console.error(err);
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].answer = 'Error: Failed to reach agent.';
        return newHist;
      });
    }
  };

  const handleAddFollowUpToReport = (question, answer) => {
    if (addedQuestions.has(question)) return;
    
    setAddedQuestions(prev => {
      const next = new Set(prev);
      next.add(question);
      return next;
    });

    setActiveReport(prevReport => {
      const refHeader = "## References";
      const index = prevReport.lastIndexOf(refHeader);
      
      const qaSection = `### Follow-up\n**Question:** ${question}\n\n**Answer:**\n${answer}\n\n`;
      
      if (index !== -1) {
        return prevReport.substring(0, index) + qaSection + prevReport.substring(index);
      } else {
        return prevReport + "\n\n" + qaSection;
      }
    });
  };

  const handleDownloadMarkdown = () => {
    const blob = new Blob([activeReport], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'research_report.md';
    link.click();
    URL.revokeObjectURL(url);
  };

  const extractDomain = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch {
      return 'Knowledge Base';
    }
  };

  const getDynamicTrendingTopics = () => {
    const defaultTopics = [
      "History of Linux",
      "Climate Change",
      "CRISPR",
      "Quantum Computing",
      "Autobots vs Decepticons"
    ];
    if (!history || history.length === 0) {
      return defaultTopics;
    }
    const historyTitles = history.map(h => h.title).filter(Boolean);
    const merged = Array.from(new Set([...historyTitles, ...defaultTopics]));
    return merged.slice(0, 5);
  };

  const trendingTopics = getDynamicTrendingTopics();

  const groupHistory = (historyItems) => {
    const today = [];
    const yesterday = [];
    const thisWeek = [];
    const older = [];

    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfYesterday = new Date(startOfToday);
    startOfYesterday.setDate(startOfYesterday.getDate() - 1);
    const startOfThisWeek = new Date(startOfToday);
    startOfThisWeek.setDate(startOfThisWeek.getDate() - 7);

    (historyItems || []).forEach(item => {
      if (!item.timestamp) {
        older.push(item);
        return;
      }
      const parsedTime = item.timestamp.includes('T') ? item.timestamp : item.timestamp.replace(' ', 'T') + 'Z';
      const itemDate = new Date(parsedTime);
      if (itemDate >= startOfToday) {
        today.push(item);
      } else if (itemDate >= startOfYesterday) {
        yesterday.push(item);
      } else if (itemDate >= startOfThisWeek) {
        thisWeek.push(item);
      } else {
        older.push(item);
      }
    });

    return { today, yesterday, thisWeek, older };
  };

  const formatDateToShort = (timestampStr) => {
    if (!timestampStr) return "RECENT ENTRY";
    try {
      const parsedTime = timestampStr.includes('T') ? timestampStr : timestampStr.replace(' ', 'T') + 'Z';
      const d = new Date(parsedTime);
      const day = String(d.getDate()).padStart(2, '0');
      const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
      const month = months[d.getMonth()];
      const year = d.getFullYear();
      return `${day} ${month} ${year}`;
    } catch {
      return "RECENT ENTRY";
    }
  };

  const getRecentReportDesc = (route) => {
    if (route === 'ARXIV') return "Academic literature search and citation index.";
    if (route === 'HYBRID') return "Comparative matrix analysis and web search.";
    if (route === 'WEB') return "Web registry insights and historical timelines.";
    if (route === 'RAG') return "Local database context and vector indexing.";
    return "Cached research insights and source logs.";
  };

  const getCleanedHistory = () => {
    if (!history) return [];
    
    const seenTitles = new Set();
    const cleaned = [];
    
    for (const item of history) {
      if (!item || !item.title) continue;
      
      const titleLower = item.title.toLowerCase().trim();
      
      const isFailed = (
        titleLower.includes("failed") ||
        titleLower.includes("error") ||
        titleLower.includes("temporarily unavailable") ||
        titleLower.includes("no report was generated")
      );
      if (isFailed) continue;
      
      if (seenTitles.has(titleLower)) continue;
      
      seenTitles.add(titleLower);
      cleaned.push(item);
    }
    
    return cleaned.slice(0, 15);
  };

  const renderHistoryView = () => {
    const cleaned = getCleanedHistory();
    const filtered = cleaned.filter(item => 
      item && item.title && item.title.toLowerCase().includes((historySearch || '').toLowerCase())
    );

    return (
      <div className="history-view-container" style={{ animation: 'fadeIn 0.3s ease-out' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px', letterSpacing: '-0.02em' }}>Research History</h1>
        <p style={{ color: 'var(--on-surface-variant)', fontSize: '14px', marginBottom: '24px' }}>
          Review and search all previously generated intelligence reports.
        </p>

        <input 
          type="text" 
          placeholder="Search history records..." 
          value={historySearch}
          onChange={e => setHistorySearch(e.target.value)}
          style={{
            width: '100%',
            maxWidth: '480px',
            background: 'var(--surface-container-lowest)',
            border: '1px solid var(--outline)',
            color: 'var(--on-background)',
            padding: '12px 16px',
            fontSize: '14px',
            outline: 'none',
            marginBottom: '32px',
            transition: 'border-color 0.2s'
          }}
          className="history-search-input-main"
        />

        <div className="history-view-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filtered.length === 0 ? (
            <p style={{ fontStyle: 'italic', color: 'var(--on-surface-variant)', fontSize: '13px' }}>No reports found in history.</p>
          ) : (
            filtered.map(item => {
              let dateStr = "";
              if (item.timestamp) {
                const parsedTime = item.timestamp.includes('T') ? item.timestamp : item.timestamp.replace(' ', 'T') + 'Z';
                dateStr = new Date(parsedTime).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
              }
              return (
                <div 
                  key={item.id} 
                  className="history-view-row"
                  onClick={() => handleSelectHistory(item.id)}
                  style={{
                    padding: '20px',
                    border: '1px solid var(--outline)',
                    background: 'var(--surface-container-low)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--on-background)' }}>{item.title}</span>
                    <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Route: {item.route || 'WEB'}</span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)' }}>{dateStr || "Recent"}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };


  const renderCollectionsView = () => {
    const categories = [
      { name: 'Academic', label: 'Academic & Technical', desc: 'Formal papers retrieved from arXiv, including computer science, ML, and physics architectures.', color: '#4F46E5' },
      { name: 'History', label: 'Historical & Archival', desc: 'Historic audits, vintage datasets, and computer science history timelines.', color: '#059669' },
      { name: 'Technology', label: 'System Technology', desc: 'Neural network sustainability, data scaling, and infrastructure reports.', color: '#2563EB' },
      { name: 'Culture', label: 'Cultural & Humanistic', desc: 'Metrics of intuition, artistic expression, and digital design philosophy.', color: '#D97706' },
      { name: 'Entertainment', label: 'Pop Culture & Media', desc: 'Audits of modern cinema, entertainment media, and pop-culture topics.', color: '#DB2777' },
    ];

    if (selectedCollection) {
      const filteredItems = (history || []).filter(item => getReportCategory(item) === selectedCollection);
      return (
        <div className="collections-container">
          <div className="collections-header-row" style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
            <button className="back-collection-btn" onClick={() => {
              if (window.history.state && window.history.state.selectedCollection) {
                window.history.back();
              } else {
                setSelectedCollection(null);
              }
            }}>
              &larr; Back to Folders
            </button>
            <h1>{categories.find(c => c.name === selectedCollection)?.label}</h1>
          </div>
          <p className="collections-subtitle">Viewing items in this library classification.</p>
          
          <div className="collection-items-list" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredItems.length === 0 ? (
              <p style={{ fontStyle: 'italic', color: 'var(--on-surface-variant)', fontSize: '13px' }}>No reports categorized in this folder yet.</p>
            ) : (
              filteredItems.map(item => {
                let dateStr = "";
                if (item.timestamp) {
                  const parsedTime = item.timestamp.includes('T') ? item.timestamp : item.timestamp.replace(' ', 'T') + 'Z';
                  dateStr = new Date(parsedTime).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
                }
                return (
                  <div 
                    key={item.id} 
                    className="collection-item-row"
                    onClick={() => handleSelectHistory(item.id)}
                    style={{
                      padding: '16px',
                      border: '1px solid var(--outline)',
                      background: 'var(--surface-container-low)',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div className="collection-item-info" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className="collection-item-title" style={{ fontWeight: 700, fontSize: '14px' }}>{item.title}</span>
                    </div>
                    <span className="collection-item-date" style={{ fontSize: '11px', color: 'var(--on-surface-variant)' }}>{dateStr || "Recent"}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="collections-container">
        <h1>Research Collections</h1>
        <p className="collections-subtitle">Grouped archives categorized by intelligence domains.</p>
        
        <div className="collections-grid">
          {categories.map(cat => {
            const count = (history || []).filter(h => getReportCategory(h) === cat.name).length;
            return (
              <div 
                key={cat.name} 
                className="collection-folder-card"
                onClick={() => handleSelectCollection(cat.name)}
                style={{ cursor: 'pointer' }}
              >
                <div className="folder-icon-row">
                  <Folder size={32} style={{ color: cat.color }} />
                  <span className="folder-count">{count} {count === 1 ? 'archive' : 'archives'}</span>
                </div>
                <h3>{cat.label}</h3>
                <p>{cat.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Defensive parsing and data binding
  const reportData = parseReportMarkdown(activeReport, activeTopic);
  const totalReports = history?.length ?? 0;
  const activeQueries = history ? new Set(history.map(item => item.title)).size : 0;
  const duplicationRate = totalReports > 0 ? (((totalReports - activeQueries) / totalReports) * 100).toFixed(1) + "%" : "0%";
  
  const recentReports = getCleanedHistory()
    .filter(item => item && item.title && !item.title.includes("Neural Network Sustainability Crisis"))
    .slice(0, 3);

  // Previous/Next page bindings in history
  const activeIndex = (history || []).findIndex(item => item && item.id === activeReportId);
  const prevReportItem = activeIndex > 0 ? history[activeIndex - 1] : null;
  const nextReportItem = activeIndex !== -1 && activeIndex < (history || []).length - 1 ? history[activeIndex + 1] : null;

    const renderHomeView = () => {
    return (
      <div className="home-container">
              
              {/* Header Search widget */}
              <div className="hero-search">
                <h1>Search the Archive.</h1>
                <form onSubmit={handleGenerate} className="search-bar-underlined">
                  <input 
                    ref={searchInputRef}
                    type="text" 
                    className="search-input-underlined" 
                    placeholder="Inquire about the future..." 
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    autoFocus
                  />
                  <button type="submit" className="search-submit-btn">
                    <ArrowRight size={22} />
                  </button>
                </form>
              </div>

              {/* Suggestions */}
              {clarificationOptions && clarificationOptions.length > 0 && (
                <div className="clarification-dialog">
                  <h3>Did you mean:</h3>
                  {!showOtherInput ? (
                    <div className="clarification-options">
                      {clarificationOptions.map((opt, i) => (
                        <button 
                          key={i} 
                          className="clarification-btn"
                          onClick={() => {
                            if (opt === "Other") {
                              setShowOtherInput(true);
                            } else {
                              handleGenerate(null, opt, true);
                            }
                          }}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="manual-topic-input">
                      <p style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px' }}>Specify Research Focus</p>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <input 
                           type="text" 
                          value={manualTopic}
                          onChange={(e) => setManualTopic(e.target.value)}
                          placeholder="Type query..."
                          style={{
                            flex: 1,
                            padding: '10px 12px',
                            border: '1px solid var(--outline)',
                            background: 'var(--surface-container-lowest)',
                            color: 'var(--on-background)',
                            outline: 'none'
                          }}
                        />
                        <button 
                          className="trending-chip" 
                          onClick={() => {
                            setShowOtherInput(false);
                            setClarificationOptions([]);
                            handleGenerate(null, manualTopic, true);
                          }}
                        >
                          Research
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Error Block */}
              {error && (
                <div className="error-panel">
                  <div className="error-header">
                    <AlertCircle size={16} />
                    <span>Research System Error</span>
                  </div>
                  <div className="error-body">{error}</div>
                </div>
              )}

              {/* Removed Trending Section to reduce clutter */}

              {/* MAGAZINE LAYOUT SPLIT */}
              <div className="magazine-layout-grid">
                
                {/* Left side: Featured article & archives */}
                <div className="magazine-left">
                  
                  {/* Featured Article Card */}
                  <div className="featured-card" style={{ cursor: 'pointer' }} onClick={handleFeaturedClick}>
                    <div className="featured-card-content">
                      <div className="featured-card-tag-row">
                        <span className="featured-tag">SHOWCASE ARCHIVE</span>
                        <span className="featured-vol">Vol. 01 / No. 05</span>
                      </div>
                      <h2 className="featured-title">The Neural Network Sustainability Crisis: A Journalistic Audit</h2>
                      <p className="featured-excerpt">
                        An in-depth exploration of physical energy resource depletion and training data degradation under model collapse recursive loops.
                      </p>
                      <div className="featured-author-row">
                        <div className="featured-author-avatar"></div>
                        <span className="featured-author">BY ARCHIVAL INTELLIGENCE</span>
                        <div className="featured-arrow-icon">
                          <ArrowRight size={18} />
                        </div>
                      </div>
                    </div>
                    <div className="featured-card-image" style={{ backgroundImage: "url('https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=600&auto=format&fit=crop')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
                      <div className="grayscale-art-mask"></div>
                    </div>
                  </div>

                  {/* Recent Archival Entries list (renders database reports or fallbacks) */}
                  <div className="recent-reports-section" style={{ marginTop: '40px' }}>
                    <h4 className="section-label">RECENT ARCHIVAL ENTRIES</h4>
                    <div className="recent-reports-list">
                      {recentReports.length > 0 ? (
                        recentReports.map((item, i) => (
                          <div 
                            key={i} 
                            className="archive-entry-row" 
                            style={{ cursor: 'pointer' }}
                            onClick={() => handleSelectHistory(item.id)}
                          >
                            <span className="archive-entry-date">{formatDateToShort(item.timestamp)}</span>
                            <div className="archive-entry-content">
                              <h3 className="archive-entry-title">{item.title}</h3>
                              <p className="archive-entry-description">{getRecentReportDesc(item.route)}</p>
                            </div>
                          </div>
                        ))
                      ) : (
                        <>
                          <div className="archive-entry-row" style={{ cursor: 'pointer' }} onClick={() => handleArchiveClick("The Semi-Permeable Web: Protecting Original Data Layers")}>
                            <span className="archive-entry-date">05 DEC 2024</span>
                            <div className="archive-entry-content">
                              <h3 className="archive-entry-title">The Semi-Permeable Web: Protecting Original Data Layers</h3>
                              <p className="archive-entry-description">Exploration of cryptographic methods to prevent automated scraping from diluting artisanal data...</p>
                            </div>
                          </div>
                          <div className="archive-entry-row" style={{ cursor: 'pointer' }} onClick={() => handleArchiveClick("Quantifying the 'Vibe': Why Metrics Fail Human Intuition")}>
                            <span className="archive-entry-date">02 DEC 2024</span>
                            <div className="archive-entry-content">
                              <h3 className="archive-entry-title">Quantifying the 'Vibe': Why Metrics Fail Human Intuition</h3>
                              <p className="archive-entry-description">A critique of algorithmic sentiment analysis in the age of ironic post-modern communication...</p>
                            </div>
                          </div>
                          <div className="archive-entry-row" style={{ cursor: 'pointer' }} onClick={() => handleArchiveClick("Retro-Future datasets and the curation of nostalgia")}>
                            <span className="archive-entry-date">28 NOV 2024</span>
                            <div className="archive-entry-content">
                              <h3 className="archive-entry-title">Retro-Future datasets and the curation of nostalgia</h3>
                              <p className="archive-entry-description">How early digital aesthetics are being reconstructed as gold-standard training data for Gen Alpha...</p>
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right side: Sidebar information cards */}
                <div className="magazine-right">
                  
                  {/* Archive Statistics widgets */}
                  <div className="info-panel-card">
                    <h5 className="info-panel-title">ARCHIVE STATISTICS</h5>
                    <div className="info-panel-body">
                      <div className="stat-line">
                        <span className="stat-label">Total Records</span>
                        <span className="stat-val">{totalReports}</span>
                      </div>
                      <div className="stat-line">
                        <span className="stat-label">Active Queries</span>
                        <span className="stat-val">{activeQueries}</span>
                      </div>
                      <div className="stat-line">
                        <span className="stat-label">Duplication Rate</span>
                        <span className="stat-val colored">{duplicationRate}</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>

            </div>
    );
  };

  const renderReportView = () => {
    return (
      <div className="report-container">
              
              {/* CENTER COLUMN (Reading Layout) */}
              <div className="report-center-column">
                <button 
                  className="report-back-btn" 
                  onClick={() => {
                    if (window.history.state && window.history.state.activeReportId !== null) {
                      window.history.back();
                    } else {
                      setActiveReport(null);
                      setActiveReportId(null);
                      window.history.pushState({
                        activeNav: 'archives',
                        activeReportId: null,
                        activeReport: null,
                        activeTopic: '',
                        route: null,
                        insights: null,
                        sources: [],
                        selectedCollection: null,
                        timestamp: ''
                      }, "");
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: 'none',
                    border: 'none',
                    color: 'var(--on-surface-variant)',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 500,
                    marginBottom: '16px',
                    padding: '0'
                  }}
                >
                  &larr; Back
                </button>
                <span className="report-category-tag">
                  {route === 'ARXIV' ? 'ACADEMIC ANALYSIS VOL. VII' : 'ECONOMIC ANALYSIS VOL. IV'}
                </span>
                <h1 className="report-header-title">{reportData.topic || activeTopic}</h1>
                <div className="report-header-date">
                  Poneglyph Intelligence &bull; {reportData.date || timestamp || "October 24, 2023"}
                </div>

                {/* Suppressed raw inline images - render one hero image at the top */}
                {reportData.images && reportData.images.length > 0 && (
                  <img 
                    src={reportData.images[0]} 
                    className="report-hero-image" 
                    alt="Research Hero Illustration" 
                  />
                )}

                {/* Main report body text (images are hidden, citations custom-rendered) */}
                <div className="report-body-content">
                  <ReactMarkdown
                    components={{
                      img: () => null, // Suppress raw markdown images inline
                      a: ({ href, children }) => {
                        // Custom citation badge styling (e.g. [1] -> violet badge)
                        const text = String(children);
                        const isCitation = /^[\[]?\d+[\]]?$/.test(text);
                        if (isCitation) {
                          const num = text.replace(/[\[\]]/g, '');
                          return (
                            <a 
                              href={href} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="citation-inline-badge"
                            >
                              {num.padStart(2, '0')}
                            </a>
                          );
                        }
                        return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
                      }
                    }}
                  >
                    {reportData.body}
                  </ReactMarkdown>
                </div>

                {/* Render additional images as a neat 2-column gallery grid at the bottom */}
                {reportData.images && reportData.images.length > 1 && (
                  <div className="report-gallery-grid">
                    {reportData.images.slice(1).map((imgUrl, i) => (
                      <img 
                        key={i} 
                        src={imgUrl} 
                        className="report-gallery-image" 
                        alt={`Additional research evidence ${i + 1}`} 
                      />
                    ))}
                  </div>
                )}

                {/* Report References at the bottom */}
                {reportData.references && (
                  <>
                    <hr className="report-references-divider" />
                    <div className="report-body-content">
                      <ReactMarkdown
                        components={{
                          a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer">{children}</a>
                        }}
                      >
                        {reportData.references}
                      </ReactMarkdown>
                    </div>
                  </>
                )}

                {/* Previous/Next Chapter Navigation (Goal layout) */}
                <div className="chapter-navigation-row">
                  {prevReportItem ? (
                    <button 
                      className="chapter-nav-btn prev"
                      onClick={() => handleSelectHistory(prevReportItem.id)}
                    >
                      <span className="nav-dir-lbl">PREVIOUS ARCHIVE</span>
                      <span className="nav-title-lbl">{prevReportItem.title}</span>
                    </button>
                  ) : (
                    <div className="chapter-nav-placeholder" />
                  )}

                  {nextReportItem ? (
                    <button 
                      className="chapter-nav-btn next"
                      onClick={() => handleSelectHistory(nextReportItem.id)}
                    >
                      <span className="nav-dir-lbl">NEXT ARCHIVE</span>
                      <span className="nav-title-lbl">{nextReportItem.title}</span>
                    </button>
                  ) : (
                    <div className="chapter-nav-placeholder" />
                  )}
                </div>
              </div>

              {/* RIGHT EVIDENCE RAIL */}
              <div className="right-evidence-rail">
                
                {/* Actions widgets */}
                <div className="rail-actions">
                  <button 
                    className="pdf-export-btn"
                    onClick={() => downloadPDF(activeReport, insights, chatHistory.filter(c => c.answer !== '...'))}
                  >
                    <Download size={16} /> Export PDF Report
                  </button>
                  <button 
                    className="chat-toggle-btn"
                    onClick={() => setChatOpen(true)}
                  >
                    <MessageSquare size={16} /> Open Chat Assistant
                  </button>
                </div>

                {/* Quality Metrics statistic rows */}
                {insights && insights.word_count !== undefined && (
                  <div className="compact-stats-container">
                    <div className="compact-stat-row">
                      <span className="compact-stat-lbl">References Used</span>
                      <span className="compact-stat-val">{insights.references_used ?? 'N/A'}</span>
                    </div>
                    <div className="compact-stat-row">
                      <span className="compact-stat-lbl">Unique Sources</span>
                      <span className="compact-stat-val">{insights.unique_sources ?? 'N/A'}</span>
                    </div>
                    <div className="compact-stat-row">
                      <span className="compact-stat-lbl">Source Freshness</span>
                      <span className="compact-stat-val">{insights.average_source_freshness ?? 'N/A'}</span>
                    </div>
                    <div className="compact-stat-row">
                      <span className="compact-stat-lbl">Citation Density</span>
                      <span className="compact-stat-val">
                        {typeof insights.citation_density === 'number'
                          ? `${(insights.citation_density * 100).toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="compact-stat-row">
                      <span className="compact-stat-lbl">Evidence Coverage</span>
                      <span className="compact-stat-val">
                        {typeof insights.evidence_coverage === 'number'
                          ? `${(insights.evidence_coverage * 100).toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Supporting Excerpts Evidence Cards list */}
                {insights?.evidence_panel?.length > 0 && (
                  <div className="rail-panel">
                    <h5 className="rail-panel-title">Primary Evidence</h5>
                    <div className="rail-cards-list">
                      {insights.evidence_panel.map((ev, i) => (
                        <div key={i} className="rail-evidence-card">
                          <div className="rail-evidence-top">
                            <span className="rail-evidence-idx">{String(ev.index).padStart(2, '0')}</span>
                            <span className="rail-evidence-title" title={ev.title}>{ev.title}</span>
                            <a href={ev.url} target="_blank" rel="noreferrer" className="rail-evidence-link-icon">
                              <ExternalLink size={12} />
                            </a>
                          </div>
                          <div className="rail-evidence-text">
                            "{ev.excerpt}"
                          </div>
                          <a 
                            href={ev.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            className="rail-evidence-url"
                            title={ev.url}
                          >
                            {ev.url}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reference Sources links */}
                {sources?.length > 0 && (
                  <div className="rail-panel">
                    <h5 className="rail-panel-title">Cited Sources</h5>
                    <div className="rail-cards-list">
                      {sources.map((source, i) => (
                        <a 
                          key={i} 
                          href={source.url || source} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="rail-source-card"
                        >
                          <div className="rail-source-info">
                            <span className="rail-source-title">{source.title || extractDomain(source.url || source)}</span>
                            <span className="rail-source-domain">{source.url || source}</span>
                          </div>
                          <ChevronRight size={14} style={{ color: 'var(--on-surface-variant)', flexShrink: 0 }} />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>

            </div>
    );
  };

  return (
    <div className="app-container">
      {/* Top scroll tracker progress bar */}
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }} />

      {/* PERSISTENT LEFT NAVIGATION SIDEBAR */}
      <div className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-title">Poneglyph Research</span>
        </div>
        
        {/* Main Navigation Links */}
        <div className="nav-section">
          <button 
            className={`nav-item ${activeNav === 'history' ? 'active' : ''}`}
            onClick={() => handleNavClick('history')}
          >
            <Activity size={15} /> History
          </button>
          <button 
            className={`nav-item ${activeNav === 'archives' ? 'active' : ''}`}
            onClick={() => handleNavClick('archives')}
          >
            <Archive size={15} /> Archives
          </button>
          <button 
            className={`nav-item ${activeNav === 'collections' ? 'active' : ''}`}
            onClick={() => handleNavClick('collections')}
          >
            <Folder size={15} /> Collections
          </button>
        </div>

        {/* Archives/History selection list */}
        <h4 className="sidebar-history-title">Saved Archives</h4>
        <input 
          type="text" 
          className="history-search-input" 
          placeholder="Filter archives..." 
          value={historySearch}
          onChange={e => setHistorySearch(e.target.value)}
        />

        <div className="history-list">
          {totalReports === 0 ? (
            <p style={{ fontSize: 11, color: 'var(--on-surface-variant)', fontStyle: 'italic', padding: '0 8px' }}>No records saved.</p>
          ) : (
            (() => {
              const filtered = getCleanedHistory().filter(item => item && item.title && item.title.toLowerCase().includes((historySearch || '').toLowerCase()));
              const groups = groupHistory(filtered);
              
              const renderGroup = (title, items) => {
                if (!items || items.length === 0) return null;
                return (
                  <div className="history-group-section">
                    <h5 className="history-group-header">{title}</h5>
                    {items.map(item => {
                      let timeStr = "";
                      if (item.timestamp) {
                        const parsedTime = item.timestamp.includes('T') ? item.timestamp : item.timestamp.replace(' ', 'T') + 'Z';
                        const dateObj = new Date(parsedTime);
                        if (title === "Today") {
                          timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                        } else {
                          timeStr = dateObj.toLocaleDateString([], { month: 'short', day: 'numeric' });
                        }
                      }
                      return (
                        <button 
                          key={item.id} 
                          className={`history-item ${activeReportId === item.id ? 'active' : ''}`} 
                          onClick={() => handleSelectHistory(item.id)}
                          title={item.title}
                        >
                          <div className="history-item-left" style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0, flex: 1 }}>
                            <span className="history-item-title" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.title}</span>
                          </div>
                          {timeStr && <span className="history-item-time">{timeStr}</span>}
                        </button>
                      );
                    })}
                  </div>
                );
              };

              return (
                <>
                  {renderGroup("Today", groups.today)}
                  {renderGroup("Yesterday", groups.yesterday)}
                  {renderGroup("This Week", groups.thisWeek)}
                  {renderGroup("Older", groups.older)}
                </>
              );
            })()
          )}
        </div>

      </div>

      {/* TOP NAVIGATION BAR & CONTENT WORKSPACE */}
      <div className="main-viewport-wrapper">
        
        {/* PONEGLYPH TOP NAVIGATION */}
        <header className="poneglyph-header">
          <div className="header-left">
            <span className="logo-text" onClick={() => handleNavClick('archives')}>Poneglyph</span>
          </div>
          <div className="header-right">
            <button className="new-search-btn" onClick={handleNewSearch}>
              New Search
            </button>
            <div className="profile-btn" onClick={() => setProfileOpen(true)}>
              <svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" strokeWidth="2" fill="none">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
          </div>
        </header>

        {/* WORKSPACE AREA */}
        <div className="main-content" onScroll={handleScroll}>
          {isLoading ? (
            <div className="loader">
              <div className="spinner"></div>
              <p>Agents are synthesizing data...</p>
            </div>
          ) : activeReport ? (
            renderReportView()
          ) : activeNav === 'collections' ? (
            renderCollectionsView()
          ) : activeNav === 'history' ? (
            renderHistoryView()
          ) : (
            renderHomeView()
          )}
        </div>
      </div>

      {/* SLIDE-OUT CHAT ASSISTANT DRAWER PANEL */}
      {chatOpen && (
        <div 
          className="chat-drawer-backdrop" 
          onClick={() => setChatOpen(false)} 
        />
      )}
      <div className={`chat-drawer ${chatOpen ? 'open' : ''}`}>
        <div className="chat-drawer-header">
          <span className="chat-drawer-title">Research Assistant</span>
          <button className="chat-drawer-close" onClick={() => setChatOpen(false)}>
            <X size={20} />
          </button>
        </div>
        
        <div className="chat-drawer-body">
          {chatHistory.length === 0 ? (
            <p style={{ fontSize: '13px', color: 'var(--on-surface-variant)', fontStyle: 'italic', textAlign: 'center', marginTop: '24px' }}>
              Ask follow-up questions regarding the loaded report findings.
            </p>
          ) : null}
          {chatHistory.map((msg, i) => (
            <React.Fragment key={i}>
              <div className="chat-bubble user">{msg.question}</div>
              <div className="chat-bubble assistant">
                {msg.answer === '...' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Loader size={14} className="spinner" style={{ width: 14, height: 14, border: '2px solid var(--surface-dim)', borderTopColor: 'var(--primary)' }} />
                    <span style={{ fontSize: '12px', color: 'var(--on-surface-variant)', fontStyle: 'italic' }}>Synthesizing...</span>
                  </div>
                ) : (
                  <>
                    <ReactMarkdown
                      components={{
                        a: ({ href, children }) => <a href={href} target="_blank" rel="noreferrer">{children}</a>
                      }}
                    >
                      {msg.answer}
                    </ReactMarkdown>
                    <button 
                      className="trending-chip" 
                      style={{ 
                        marginTop: '10px', 
                        padding: '4px 10px', 
                        fontSize: '10px',
                        opacity: addedQuestions.has(msg.question) ? 0.5 : 1,
                        cursor: addedQuestions.has(msg.question) ? 'default' : 'pointer'
                      }}
                      onClick={() => handleAddFollowUpToReport(msg.question, msg.answer)}
                      disabled={addedQuestions.has(msg.question)}
                    >
                      {addedQuestions.has(msg.question) ? "Added" : "Add to Report"}
                    </button>
                  </>
                )}
              </div>
            </React.Fragment>
          ))}
          <div ref={chatEndRef} />
        </div>

        <form onSubmit={handleChatSubmit} className="chat-drawer-input-form">
          <input 
            type="text" 
            className="chat-drawer-input" 
            placeholder="Ask a question..." 
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
          />
          <button type="submit" className="chat-drawer-submit">
            <ArrowRight size={18} />
          </button>
        </form>
      </div>

      {/* PROFILE MODAL OVERLAY */}
      {profileOpen && (
        <div 
          className="profile-modal-backdrop" 
          onClick={() => setProfileOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
            animation: 'fadeIn 0.2s ease-out'
          }}
        >
          <div 
            className="profile-modal-content"
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--surface-container-low)',
              border: '1px solid var(--outline)',
              width: '100%',
              maxWidth: '380px',
              padding: '28px',
              position: 'relative',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)'
            }}
          >
            <button 
              onClick={() => setProfileOpen(false)}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'none',
                border: 'none',
                color: 'var(--on-surface-variant)',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={18} />
            </button>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <div 
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'var(--primary-container)',
                  color: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px',
                  fontWeight: 700,
                  marginBottom: '16px',
                  border: '1px solid var(--outline)'
                }}
              >
                GR
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--on-background)', marginBottom: '4px', fontFamily: 'Inter, sans-serif' }}>Guest Researcher</h2>
              <p style={{ fontSize: '12px', color: 'var(--on-surface-variant)', marginBottom: '24px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Archival Access Role</p>
              
              <div 
                style={{
                  width: '100%',
                  borderTop: '1px solid var(--outline)',
                  paddingTop: '20px',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '16px'
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary)' }}>{totalReports}</div>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--on-surface-variant)', fontWeight: 700, marginTop: '4px', letterSpacing: '0.05em' }}>Total Reports</div>
                </div>
                <div style={{ textAlign: 'center', borderLeft: '1px solid var(--outline)' }}>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--primary)' }}>5</div>
                  <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--on-surface-variant)', fontWeight: 700, marginTop: '4px', letterSpacing: '0.05em' }}>Collections</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
