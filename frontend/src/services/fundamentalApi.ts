import axios from 'axios';

const API_BASE = '/api/fundamental';

export const fundamentalApi = {
  getReport: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/report`),
  getIndicators: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/indicators`),
  getCompanyInfo: (stockCode: string) => axios.get(`${API_BASE}/${stockCode}/company`),
};
