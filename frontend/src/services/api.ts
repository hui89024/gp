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
  PredictionSignal,
  ModelPerformance,
  Prediction,
  DailyReviewSummary,
  WeeklyReviewSummary,
  StrategyAnalysis,
  BehaviorAnalysis,
  ComprehensiveReview,
  StrategyConfig,
  AutoTradeTask,
  RiskConfig,
  AutoTradeLog,
  AutoTradingStatus,
  AutoTradingStatistics,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// 账户API
export const accountApi = {
  createUser: (username: string, initialCapital: number) =>
    api.post<User>('/account/users', {
      username,
      initial_capital: initialCapital,
    }),

  getUser: (userId: number) =>
    api.get<User>(`/account/users/${userId}`),

  getAccountOverview: (userId: number) =>
    api.get<AccountOverview>(`/account/users/${userId}/overview`),
};

// 交易API
export const tradeApi = {
  buy: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/trades/buy', trade, {
      params: { user_id: userId },
    }),

  sell: (userId: number, trade: TradeCreate) =>
    api.post<Trade>('/trades/sell', trade, {
      params: { user_id: userId },
    }),

  getHistory: (userId: number, stockCode?: string) =>
    api.get<Trade[]>('/trades/history', {
      params: { user_id: userId, stock_code: stockCode },
    }),

  getPositions: (userId: number) =>
    api.get<Position[]>('/trades/positions', {
      params: { user_id: userId },
    }),
};

// 股票数据API
export const stockApi = {
  getQuote: (stockCode: string) =>
    api.get<StockQuote>(`/stocks/${stockCode}/quote`),

  getHistory: (stockCode: string, days: number = 30) =>
    api.get<StockHistory[]>(`/stocks/${stockCode}/history`, {
      params: { days },
    }),

  getKlineData: (stockCode: string, days: number = 60) =>
    api.get<KLineData>(`/stocks/${stockCode}/kline`, {
      params: { days },
    }),

  search: (keyword: string) =>
    api.get<Array<{ stock_code: string; stock_name: string }>>('/stocks/search', {
      params: { keyword },
    }),
};

// 预测API
export const predictionApi = {
  train: (stockCode: string, days: number = 180) =>
    api.post(`/predictions/train/${stockCode}`, null, { params: { days } }),

  getSignal: (stockCode: string) =>
    api.get<PredictionSignal>(`/predictions/signal/${stockCode}`),

  getMultipleSignals: (stockCodes: string[]) =>
    api.get<PredictionSignal[]>('/predictions/signals', {
      params: { stock_codes: stockCodes.join(',') },
    }),

  getPerformance: (modelType: string = 'LSTM') =>
    api.get<ModelPerformance>('/predictions/performance', {
      params: { model_type: modelType },
    }),

  getHistory: (stockCode: string, limit: number = 30) =>
    api.get<Prediction[]>('/predictions/history', {
      params: { stock_code: stockCode, limit },
    }),
};

// 复盘API
export const reviewApi = {
  generate: (userId: number) =>
    api.post(`/reviews/generate/${userId}`),

  getDailySummary: (userId: number) =>
    api.get<DailyReviewSummary>(`/reviews/daily/${userId}`),

  getWeeklySummary: (userId: number) =>
    api.get<WeeklyReviewSummary>(`/reviews/weekly/${userId}`),

  getStrategyAnalysis: (userId: number) =>
    api.get<StrategyAnalysis[]>(`/reviews/strategies/${userId}`),

  getBehaviorAnalysis: (userId: number) =>
    api.get<BehaviorAnalysis>(`/reviews/behavior/${userId}`),

  getComprehensiveReview: (userId: number) =>
    api.get<ComprehensiveReview>(`/reviews/comprehensive/${userId}`),

  updateNotes: (reviewId: number, userId: number, notes: string, lessons: string) =>
    api.put(`/reviews/notes/${reviewId}`, null, {
      params: { user_id: userId, notes, lessons },
    }),
};

// 自动交易API
export const autoTradingApi = {
  createStrategy: (userId: number, data: { strategy_name: string; strategy_type: string; config: Record<string, any> }) =>
    api.post<StrategyConfig>('/auto-trading/strategies', data, { params: { user_id: userId } }),

  getStrategies: (userId: number) =>
    api.get<StrategyConfig[]>('/auto-trading/strategies', { params: { user_id: userId } }),

  updateStrategy: (strategyId: number, userId: number, data: Partial<StrategyConfig>) =>
    api.put<StrategyConfig>(`/auto-trading/strategies/${strategyId}`, data, { params: { user_id: userId } }),

  deleteStrategy: (strategyId: number, userId: number) =>
    api.delete(`/auto-trading/strategies/${strategyId}`, { params: { user_id: userId } }),

  createTask: (userId: number, data: { execution_mode: string; interval_minutes?: number; watchlist: string[] }) =>
    api.post<AutoTradeTask>('/auto-trading/tasks', data, { params: { user_id: userId } }),

  getTasks: (userId: number) =>
    api.get<AutoTradeTask[]>('/auto-trading/tasks', { params: { user_id: userId } }),

  startTask: (taskId: number, userId: number) =>
    api.post(`/auto-trading/tasks/${taskId}/start`, null, { params: { user_id: userId } }),

  stopTask: (taskId: number, userId: number) =>
    api.post(`/auto-trading/tasks/${taskId}/stop`, null, { params: { user_id: userId } }),

  getRiskConfig: (userId: number) =>
    api.get<RiskConfig>('/auto-trading/risk-config', { params: { user_id: userId } }),

  updateRiskConfig: (userId: number, data: Partial<RiskConfig>) =>
    api.put<RiskConfig>('/auto-trading/risk-config', data, { params: { user_id: userId } }),

  getStatus: (userId: number) =>
    api.get<AutoTradingStatus>('/auto-trading/status', { params: { user_id: userId } }),

  getStatistics: (userId: number) =>
    api.get<AutoTradingStatistics>('/auto-trading/statistics', { params: { user_id: userId } }),

  getLogs: (userId: number, limit: number = 50) =>
    api.get<AutoTradeLog[]>('/auto-trading/logs', { params: { user_id: userId, limit } }),
};

export default api;
