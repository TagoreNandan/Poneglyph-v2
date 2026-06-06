import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const fetchHistory = async () => {
  const res = await axios.get(`${API_BASE}/history`);
  return res.data;
};

export const fetchReport = async (id) => {
  const res = await axios.get(`${API_BASE}/report/${id}`);
  return res.data;
};

export const generateResearch = async (query) => {
  const res = await axios.post(`${API_BASE}/research`, { query });
  return res.data;
};

export const continueResearch = async (original_report, deeper_query) => {
  const res = await axios.post(`${API_BASE}/research/continue`, {
    original_report, deeper_query
  });
  return res.data;
};

export const sendChat = async (report, question, history) => {
  const res = await axios.post(`${API_BASE}/chat`, {
    report, question, history
  });
  return res.data;
};

export const downloadPDF = async (report, insights) => {
  const res = await axios.post(`${API_BASE}/pdf`, { report, insights }, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'research_report.pdf');
  document.body.appendChild(link);
  link.click();
  link.remove();
};
