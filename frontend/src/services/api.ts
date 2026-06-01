import axios from 'axios';
import type {
  User,
  AccountOverview,
  Trade,
  Position,
  StockQuote,
  StockHistory,
  KLineData,
  TradeCreate,
} from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// 账户API
export const accountApi = {
  createUser: (username: string, initialCapital: number) =>
    api.post<User>('/api/account/users', {
      username,
      initial_capital: initialCapital,
    }),

  getUser: (userId: number) =>
    api.get<User>(`/api/account/users/${userId}`),

  getAccountOverview: (userId: number) =>
    api.get<AccountOverview>(`/api/account/users/${userId}/overview`),
};

// 交易API
export const tradeApi = {
  buy: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/api/trades/buy', trade, {
      params: { user_id: userId },
    }),

  sell: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/api/trades/sell', trade, {
      params: { user_id: userId },
    }),

  getHistory: (userId: number, stockCode?: string) =>
    api.get<Trade[]>('/api/trades/history', {
      params: { user_id: userId, stock_code: stockCode },
    }),

  getPositions: (userId: number) =>
    api.get<Position[]>('/api/trades/positions', {
      params: { user_id: userId },
    }),
};

// 股票数据API
export const stockApi = {
  getQuote: (stockCode: string) =>
    api.get<StockQuote>(`/api/stocks/${stockCode}/quote`),

  getHistory: (stockCode: string, days: number = 30) =>
    api.get<StockHistory[]>(`/api/stocks/${stockCode}/history`, {
      params: { days },
    }),

  getKlineData: (stockCode: string, days: number = 60) =>
    api.get<KLineData>(`/api/stocks/${stockCode}/kline`, {
      params: { days },
    }),

  search: (keyword: string) =>
    api.get<Array<{ stock_code: string; stock_name: string }>>('/api/stocks/search', {
      params: { keyword },
    }),
};

export default api;
