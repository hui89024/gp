export interface User {
  id: number;
  username: string;
  initial_capital: number;
  current_capital: number;
  created_at: string;
}

export interface AccountOverview {
  total_assets: number;
  available_capital: number;
  market_value: number;
  total_pnl: number;
  today_pnl: number;
}

export interface Trade {
  id: number;
  stock_code: string;
  stock_name: string;
  trade_type: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  commission: number;
  total_amount: number;
  strategy_tag?: string;
  trade_time: string;
}

export interface Position {
  id: number;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  unrealized_pnl: number;
  market_value: number;
}

export interface StockQuote {
  stock_code: string;
  stock_name: string;
  current_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  amount: number;
  change_percent: number;
  change_amount: number;
  timestamp: string;
}

export interface StockHistory {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
}

export interface KLineData {
  dates: string[];
  opens: number[];
  highs: number[];
  lows: number[];
  closes: number[];
  volumes: number[];
}

export interface TradeCreate {
  stock_code: string;
  stock_name: string;
  price: number;
  quantity: number;
  strategy_tag?: string;
}

export interface PredictionSignal {
  stock_code: string;
  stock_name: string;
  current_price: number;
  predicted_direction: 'UP' | 'DOWN';
  predicted_price: number;
  confidence: number;
  signal_strength: 'STRONG' | 'MEDIUM' | 'WEAK';
  model_type: string;
  prediction_date: string;
}

export interface ModelPerformance {
  model_type: string;
  total_predictions: number;
  correct_predictions: number;
  accuracy: number;
  avg_confidence: number;
}

export interface DailyReviewSummary {
  date: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  win_rate: number;
}

export interface WeeklyReviewSummary {
  week_start: string;
  week_end: string;
  total_trades: number;
  total_pnl: number;
  win_rate: number;
  best_trade: any;
  worst_trade: any;
  daily_summaries: DailyReviewSummary[];
}

export interface StrategyAnalysis {
  strategy_tag: string;
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl_per_trade: number;
  profit_loss_ratio: number;
}

export interface BehaviorAnalysis {
  avg_holding_days: number;
  max_position_size: number;
  trade_frequency: number;
  emotional_trades: number;
  overtrading_days: number;
}

export interface ComprehensiveReview {
  daily_summary: DailyReviewSummary;
  weekly_summary: WeeklyReviewSummary | null;
  strategy_analysis: StrategyAnalysis[];
  behavior_analysis: BehaviorAnalysis;
  recommendations: string[];
}

export interface Prediction {
  id: number;
  stock_code: string;
  model_type: string;
  predicted_direction: string;
  predicted_price: number;
  confidence: number;
  actual_result: string | null;
  actual_price: number | null;
  prediction_date: string;
  target_date: string;
  created_at: string;
}

// 自动交易相关类型
export interface StrategyConfig {
  id: number;
  user_id: number;
  strategy_name: string;
  strategy_type: 'PREDICTION' | 'MA' | 'RSI' | 'RULE';
  config: Record<string, any>;
  enabled: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface AutoTradeTask {
  id: number;
  user_id: number;
  execution_mode: 'POLLING' | 'REALTIME' | 'BATCH';
  interval_minutes: number | null;
  watchlist: string[];
  enabled: boolean;
  last_run_at: string | null;
  created_at: string;
}

export interface RiskConfig {
  id: number;
  user_id: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  max_position_pct: number;
  max_total_position_pct: number;
  max_daily_trades: number;
  max_weekly_trades: number;
  max_daily_loss: number;
  max_single_trade: number;
}

export interface AutoTradeLog {
  id: number;
  user_id: number;
  task_id: number | null;
  signal_source: string | null;
  stock_code: string | null;
  stock_name: string | null;
  direction: string | null;
  price: number | null;
  quantity: number | null;
  confidence: number | null;
  risk_check_passed: boolean | null;
  risk_check_reason: string | null;
  execution_result: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AutoTradingStatus {
  running: boolean;
  active_tasks: number;
  active_strategies: number;
  today_trades: number;
  today_pnl: number;
}

export interface AutoTradingStatistics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl_per_trade: number;
  max_win: number;
  max_loss: number;
}
