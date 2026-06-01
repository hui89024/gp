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
