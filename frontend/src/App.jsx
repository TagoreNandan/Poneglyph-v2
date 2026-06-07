import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, ChevronRight, Download, FileText, Activity, AlertTriangle, AlertCircle, ArrowRight, MessageSquare, Loader } from 'lucide-react';
import { fetchHistory, fetchReport, generateResearch, sendChat, downloadPDF } from './api';
import './index.css';

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
  
  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [clarificationOptions, setClarificationOptions] = useState([]);
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [manualTopic, setManualTopic] = useState('');
  const [addedQuestions, setAddedQuestions] = useState(new Set());



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
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async (e, forcedQuery = null, bypass_ambiguity = false) => {
    e?.preventDefault();
    const q = forcedQuery || query;
    if (!q.trim()) return;
    
    setQuery(q);
    
    setIsLoading(true);
    setActiveReport(null);
    setActiveReportId(null);
    setInsights(null);
    setSources([]);
    setChatHistory([]);
    setClarificationOptions([]);
    setAddedQuestions(new Set());
    
    try {
      const data = await generateResearch(q, bypass_ambiguity);
      
      if (data.needs_clarification) {
        setClarificationOptions(data.clarification_options || []);
        setIsLoading(false);
        return;
      }
      
      setActiveReport(data.formatted_report);
      setInsights(data.insights);
      setSources(data.sources || []);
      setRoute(data.route || null);
      setActivityLog(data.activity_log || []);
      setActiveTopic(query);
      
      const now = new Date();
      setTimestamp(now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
      
      loadHistory();
    } catch (err) {
      console.error(err);
      alert('Error generating report. Is the backend running?');
    }
    setIsLoading(false);
  };

  const handleSelectHistory = async (id) => {
    setIsLoading(true);
    try {
      const report = await fetchReport(id);
      setActiveReport(report.content);
      setActiveReportId(id);
      setRoute(report.route || null);
      setActivityLog([]);
      setInsights(report.insights || null);
      setActiveTopic(report.title || '');
      setAddedQuestions(new Set());
      
      if (report.timestamp) {
        const d = new Date(report.timestamp);
        setTimestamp(d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}));
      } else {
        setTimestamp('');
      }
      setSources(report.sources || []);
      setChatHistory([]);
    } catch (err) {
      console.error(err);
    }
    setIsLoading(false);
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

  return (
    <div className="app-container">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="sidebar-header">
          <Activity color="#6366F1" size={24} />
          <span className="sidebar-title">ResearchPilot</span>
        </div>
        
        <button className="new-research-btn" onClick={() => { setActiveReport(null); setActiveReportId(null); setQuery(''); setAddedQuestions(new Set()); }}>
          <Search size={16} /> New Research
        </button>

        <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Recent Research</h4>
        
        <input 
          type="text" 
          className="history-search-input" 
          placeholder="Filter history..." 
          value={historySearch}
          onChange={e => setHistorySearch(e.target.value)}
        />

        <div className="history-list">
          {history.length === 0 ? <p style={{ fontSize: 13, color: '#666' }}>No history yet.</p> : null}
          {history
            .filter(item => item.title.toLowerCase().includes(historySearch.toLowerCase()))
            .slice(0, historySearch ? history.length : 15)
            .map(item => (
            <button 
              key={item.id} 
              className={`history-item ${activeReportId === item.id ? 'active' : ''}`} 
              onClick={() => handleSelectHistory(item.id)}
              title={item.title}
            >
              {item.title}
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="main-content">
        
        {isLoading ? (
          <div className="loader">
            <div className="spinner"></div>
            <p style={{ color: 'var(--text-muted)' }}>Agents are synthesizing data...</p>
          </div>
        ) : !activeReport ? (
          <div className="hero-search">
            <h1>What do you want to know?</h1>
            <p>Transform web data and local knowledge bases into comprehensive reports.</p>
            
            <form onSubmit={handleGenerate} className="search-bar">
              <input 
                type="text" 
                className="search-input" 
                placeholder="E.g., Quantum computing breakthroughs in 2024..." 
                value={query}
                onChange={e => setQuery(e.target.value)}
                autoFocus
              />
              <button type="submit" className="search-submit">
                <ArrowRight size={20} />
              </button>
            </form>

            {clarificationOptions && clarificationOptions.length > 0 && (
              <div className="clarification-dialog">
                <h3 style={{ marginBottom: 12 }}>Did you mean:</h3>
                
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
                    <p style={{ marginBottom: 8 }}>Please specify your topic</p>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input 
                        type="text" 
                        value={manualTopic}
                        onChange={(e) => setManualTopic(e.target.value)}
                        placeholder="Type here..."
                        style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '1px solid #444', background: '#222', color: '#fff' }}
                      />
                      <button 
                        className="btn-primary" 
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
          </div>
        ) : (
          <div className="dashboard">
            {/* METADATA BAR */}
            <div className="metadata-bar">
              <div className="metadata-item">
                <span className="metadata-label">Topic:</span>
                <span className="metadata-value">{activeTopic}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Route:</span>
                {route ? <span className="route-badge-small">[{route}]</span> : <span className="metadata-value">Unknown</span>}
              </div>
              {timestamp && (
                <div className="metadata-item">
                  <span className="metadata-label">Generated:</span>
                  <span className="metadata-value">{timestamp}</span>
                </div>
              )}
            </div>

            {activityLog && activityLog.length > 0 && (
              <details className="activity-log-panel">
                <summary>Agent Activity Log</summary>
                <div className="log-entries">
                  {activityLog.map((log, i) => (
                    <div key={i} className="log-item">
                      <span className="log-action">
                        ✓ {log.agent.replace(' Agent', '')} &rarr; {log.action.replace('Classified query as ', '')}
                      </span>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {insights && insights.word_count !== undefined && (
              <>
                <div className="metrics-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
                  <div className="metric-card">
                    <span className="metric-title">References Used</span>
                    <span className="metric-value">{insights.references_used ?? 'N/A'}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Unique Sources</span>
                    <span className="metric-value">{insights.unique_sources ?? 'N/A'}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Avg Source Freshness</span>
                    <span className="metric-value">{insights.average_source_freshness ?? 'N/A'}</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Citation Density</span>
                    <span className="metric-value">
                      {typeof insights.citation_density === 'number'
                        ? `${(insights.citation_density * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Evidence Coverage</span>
                    <span className="metric-value">
                      {typeof insights.evidence_coverage === 'number'
                        ? `${(insights.evidence_coverage * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="alerts-grid">
                  <div className="alert-card">
                    <div className="alert-header contra"><AlertTriangle size={18} /> Contradictions</div>
                    <ul className="alert-list">
                      {insights.contradictions?.length > 0 ? insights.contradictions.map((c, i) => <li key={i}>{c}</li>) : <li>No contradictions found.</li>}
                    </ul>
                  </div>
                </div>
              </>
            )}

            {/* REPORT VIEWER */}
            <div className="report-viewer">
              <ReactMarkdown>{activeReport}</ReactMarkdown>
            </div>

            <div className="actions-row" style={{ marginBottom: 32 }}>
              <button className="btn-secondary" onClick={handleDownloadMarkdown}><FileText size={18} /> Markdown</button>
              <button className="btn-secondary" onClick={() => downloadPDF(activeReport, insights, chatHistory.filter(c => c.answer !== '...'))}><Download size={18} /> PDF</button>
            </div>

            {/* SOURCES */}
            {sources?.length > 0 && (
              <div className="sources-section">
                <h3 style={{ fontSize: 18, marginBottom: 12 }}>Sources</h3>
                <div className="sources-grid">
                  {sources.map((source, i) => (
                    <a key={i} href={source.url || source} target="_blank" rel="noreferrer" className="source-card">
                      <div className="source-domain">{source.title || extractDomain(source.url || source)}</div>
                      <div className="source-url">{source.url || source}</div>
                      <ChevronRight className="source-icon" size={16} />
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* EVIDENCE PANEL */}
            {insights?.evidence_panel?.length > 0 && (
              <div className="sources-section" style={{ marginBottom: 32 }}>
                <h3 style={{ fontSize: 18, marginBottom: 16 }}>Source Evidence Panel</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {insights.evidence_panel.map((ev, i) => (
                    <div key={i} style={{
                      background: 'var(--bg-panel)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '12px',
                      padding: '18px',
                      backdropFilter: 'blur(12px)',
                      display: 'flex',
                      gap: '16px'
                    }}>
                      <div style={{
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: '#a5b4fc',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: '13px',
                        flexShrink: 0
                      }}>
                        [{ev.index}]
                      </div>
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <div style={{ fontWeight: '600', fontSize: '14.5px', color: 'var(--text-main)' }}>
                          {ev.title}
                        </div>
                        <div style={{ 
                          fontSize: '13.5px', 
                          color: 'var(--text-muted)', 
                          fontStyle: 'italic', 
                          borderLeft: '3px solid var(--primary)', 
                          paddingLeft: '12px',
                          margin: '6px 0',
                          lineHeight: '1.5'
                        }}>
                          "{ev.excerpt}"
                        </div>
                        <a href={ev.url} target="_blank" rel="noreferrer" style={{ 
                          fontSize: '12px', 
                          color: 'var(--primary)', 
                          textDecoration: 'none',
                          wordBreak: 'break-all'
                        }}>
                          {ev.url}
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CHAT */}
            <div className="chat-section">
              <h3 style={{ fontSize: 18, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}><MessageSquare size={20} /> Ask Follow-up Questions</h3>
              
              <div className="chat-history">
                {chatHistory.map((msg, i) => (
                  <React.Fragment key={i}>
                    <div className="chat-bubble user">{msg.question}</div>
                    <div className="chat-bubble assistant" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                      {msg.answer === '...' ? (
                        <Loader size={16} className="spinner" style={{border: 'none', borderTop: 'none', borderRight: '2px solid white'}} />
                      ) : (
                        <>
                          <ReactMarkdown>{msg.answer}</ReactMarkdown>
                          <button 
                            className="btn-secondary" 
                            style={{ 
                              marginTop: '8px', 
                              padding: '5px 10px', 
                              fontSize: '11px',
                              opacity: addedQuestions.has(msg.question) ? 0.5 : 1,
                              cursor: addedQuestions.has(msg.question) ? 'default' : 'pointer'
                            }}
                            onClick={() => handleAddFollowUpToReport(msg.question, msg.answer)}
                            disabled={addedQuestions.has(msg.question)}
                          >
                            {addedQuestions.has(msg.question) ? "Added to Report" : "Add to Report"}
                          </button>
                        </>
                      )}
                    </div>
                  </React.Fragment>
                ))}
                <div ref={chatEndRef} />
              </div>

              <form onSubmit={handleChatSubmit} className="chat-input-wrapper">
                <input 
                  type="text" 
                  className="chat-input" 
                  placeholder="Ask a question about the report..." 
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                />
                <button type="submit" className="search-submit">
                  <ArrowRight size={18} />
                </button>
              </form>
            </div>
            


          </div>
        )}
      </div>
    </div>
  );
}

export default App;
