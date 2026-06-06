import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Search, ChevronRight, Download, FileText, Activity, AlertTriangle, AlertCircle, ArrowRight, MessageSquare, Loader } from 'lucide-react';
import { fetchHistory, fetchReport, generateResearch, continueResearch, sendChat, downloadPDF } from './api';
import './index.css';

function App() {
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeReport, setActiveReport] = useState(null);
  const [activeReportId, setActiveReportId] = useState(null);
  const [historySearch, setHistorySearch] = useState('');
  const [insights, setInsights] = useState(null);
  const [sources, setSources] = useState([]);
  
  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');

  // Continue Research
  const [continueQuery, setContinueQuery] = useState('');

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

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    setActiveReport(null);
    setActiveReportId(null);
    setInsights(null);
    setSources([]);
    setChatHistory([]);
    
    try {
      const data = await generateResearch(query);
      setActiveReport(data.formatted_report);
      setInsights(data.insights);
      setSources(data.sources || []);
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
      setInsights(null);
      setSources([]);
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

  const handleContinueResearch = async (e) => {
    e.preventDefault();
    if (!continueQuery.trim() || !activeReport) return;
    
    setIsLoading(true);
    try {
      const data = await continueResearch(activeReport, continueQuery);
      setActiveReport(data.formatted_report);
      setInsights(data.insights);
      setSources(data.sources || []);
      setContinueQuery('');
    } catch (err) {
      console.error(err);
    }
    setIsLoading(false);
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
        
        <button className="new-research-btn" onClick={() => { setActiveReport(null); setActiveReportId(null); setQuery(''); }}>
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
          </div>
        ) : (
          <div className="dashboard">
            {/* INSIGHTS */}
            {insights && insights.confidence_score && (
              <>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <span className="metric-title">Confidence</span>
                    <span className="metric-value">{Math.round(insights.confidence_score * 100)}%</span>
                    <div className="metric-progress-bg">
                      <div className="metric-progress-fill" style={{ width: `${insights.confidence_score * 100}%`, background: 'linear-gradient(90deg, #6366F1, #8B5CF6)' }}></div>
                    </div>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Source Quality</span>
                    <span className="metric-value">{Math.round(insights.source_quality * 100)}%</span>
                    <div className="metric-progress-bg">
                      <div className="metric-progress-fill" style={{ width: `${insights.source_quality * 100}%`, background: 'linear-gradient(90deg, #8B5CF6, #06B6D4)' }}></div>
                    </div>
                  </div>
                  <div className="metric-card">
                    <span className="metric-title">Coverage</span>
                    <span className="metric-value">{Math.round(insights.coverage_score * 100)}%</span>
                    <div className="metric-progress-bg">
                      <div className="metric-progress-fill" style={{ width: `${insights.coverage_score * 100}%`, background: 'linear-gradient(90deg, #06B6D4, #3B82F6)' }}></div>
                    </div>
                  </div>
                </div>

                <div className="alerts-grid">
                  <div className="alert-card">
                    <div className="alert-header gap"><AlertCircle size={18} /> Research Gaps</div>
                    <ul className="alert-list">
                      {insights.research_gaps?.length > 0 ? insights.research_gaps.map((g, i) => <li key={i}>{g}</li>) : <li>No significant gaps identified.</li>}
                    </ul>
                  </div>
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
              <button className="btn-secondary" onClick={() => downloadPDF(activeReport, insights)}><Download size={18} /> PDF</button>
            </div>

            {/* SOURCES */}
            {sources?.length > 0 && (
              <div className="sources-section">
                <h3 style={{ fontSize: 18, marginBottom: 12 }}>Sources</h3>
                <div className="sources-grid">
                  {sources.map((url, i) => (
                    <a key={i} href={url} target="_blank" rel="noreferrer" className="source-card">
                      <div className="source-domain">{extractDomain(url)}</div>
                      <div className="source-url">{url}</div>
                      <ChevronRight className="source-icon" size={16} />
                    </a>
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
                    <div className="chat-bubble assistant">
                      {msg.answer === '...' ? <Loader size={16} className="spinner" style={{border: 'none', borderTop: 'none', borderRight: '2px solid white'}} /> : <ReactMarkdown>{msg.answer}</ReactMarkdown>}
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
            
            {/* CONTINUE RESEARCH */}
            <div className="chat-section" style={{ marginTop: 24 }}>
              <h3 style={{ fontSize: 18, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}><Search size={20} /> Continue Research</h3>
              <form onSubmit={handleContinueResearch} className="chat-input-wrapper">
                <input 
                  type="text" 
                  className="chat-input" 
                  placeholder="Explore a specific aspect in more detail..." 
                  value={continueQuery}
                  onChange={e => setContinueQuery(e.target.value)}
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
