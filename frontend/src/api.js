import axios from 'axios';

const API_BASE = 'https://poneglyph-v2-production.up.railway.app/api';

export const fetchHistory = async () => {
  const res = await axios.get(`${API_BASE}/history`);
  return res.data;
};

export const fetchReport = async (id) => {
  const res = await axios.get(`${API_BASE}/report/${id}`);
  return res.data;
};

export const generateResearch = async (query, bypass_ambiguity = false) => {
  const res = await axios.post(`${API_BASE}/research`, { query, bypass_ambiguity });
  return res.data;
};



export const sendChat = async (report, question, history) => {
  const res = await axios.post(`${API_BASE}/chat`, {
    report, question, history
  });
  return res.data;
};

export const downloadPDF = async (report, insights, chatHistory) => {
  const res = await axios.post(`${API_BASE}/pdf`, { report, insights, chat_history: chatHistory }, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'research_report.pdf');
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const deleteReportApi = async (id) => {
  const res = await axios.delete(`${API_BASE}/report/${id}`);
  return res.data;
};
