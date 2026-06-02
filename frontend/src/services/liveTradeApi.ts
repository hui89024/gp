import axios from 'axios';

const API_BASE = '/api/live-trades';

export interface LiveTrade {
  id: number;
  stock_code: string;
  stock_name: string | null;
  trade_type: string;
  price: number;
  quantity: number;
  total_amount: number;
  commission: number;
  broker_order_id: string | null;
  status: string;
  strategy_tag: string | null;
  trade_time: string;
}

export interface TradeRequest {
  stock_code: string;
  stock_name: string;
  price: number;
  quantity: number;
  strategy_tag?: string;
}

export const liveTradeApi = {
  buy: (data: TradeRequest) => axios.post<LiveTrade>(`${API_BASE}/buy`, data),
  sell: (data: TradeRequest) => axios.post<LiveTrade>(`${API_BASE}/sell`, data),
  cancel: (orderId: string) => axios.post(`${API_BASE}/cancel/${orderId}`),
  positions: () => axios.get(`${API_BASE}/positions`),
  balance: () => axios.get(`${API_BASE}/balance`),
  history: (stockCode?: string, limit = 50) =>
    axios.get<LiveTrade[]>(`${API_BASE}/history`, { params: { stock_code: stockCode, limit } }),
};
