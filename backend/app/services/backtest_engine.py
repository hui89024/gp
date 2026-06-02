import akshare as ak
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from enum import Enum


class StrategyType(str, Enum):
    MA = "MA"
    RSI = "RSI"
    MACD = "MACD"


@dataclass
class BacktestConfig:
    """回测配置"""
    strategy_name: str
    strategy_type: str
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 100000.0
    stock_codes: List[str] = field(default_factory=list)
    commission_rate: float = 0.0003
    stamp_tax_rate: float = 0.001
    slippage: float = 0.001


@dataclass
class TradeRecord:
    """交易记录"""
    stock_code: str
    direction: str  # BUY / SELL
    price: float
    quantity: int
    amount: float
    commission: float
    tax: float
    trade_date: str
    reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    total_trades: int = 0
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)


class BacktestEngine:
    """回测引擎"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.capital = config.initial_capital
        self.position = 0
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.holding_shares: Dict[str, int] = {}
        self.avg_cost: Dict[str, float] = {}

    def _fetch_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq"
            )
            if df.empty:
                return pd.DataFrame()

            df = df.rename(columns={
                "日期": "date", "开盘": "open", "最高": "high",
                "最低": "low", "收盘": "close", "成交量": "volume", "成交额": "amount"
            })
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            print(f"获取{stock_code}历史数据失败: {e}")
            return pd.DataFrame()

    def _calc_commission(self, amount: float, direction: str) -> tuple:
        """计算手续费和印花税"""
        commission = max(amount * self.config.commission_rate, 5.0)
        tax = amount * self.config.stamp_tax_rate if direction == "SELL" else 0.0
        return commission, tax

    def _execute_buy(self, stock_code: str, price: float, date_str: str, reason: str = ""):
        """执行买入"""
        actual_price = price * (1 + self.config.slippage)
        affordable = int(self.capital / (actual_price * 100)) * 100
        if affordable <= 0:
            return

        quantity = min(affordable, 5000)
        amount = actual_price * quantity
        commission, tax = self._calc_commission(amount, "BUY")
        total_cost = amount + commission + tax

        if total_cost > self.capital:
            return

        self.capital -= total_cost
        self.holding_shares[stock_code] = self.holding_shares.get(stock_code, 0) + quantity

        if stock_code in self.avg_cost:
            old_qty = self.holding_shares[stock_code] - quantity
            self.avg_cost[stock_code] = (self.avg_cost[stock_code] * old_qty + actual_price * quantity) / self.holding_shares[stock_code]
        else:
            self.avg_cost[stock_code] = actual_price

        trade = TradeRecord(
            stock_code=stock_code, direction="BUY", price=actual_price,
            quantity=quantity, amount=amount, commission=commission,
            tax=tax, trade_date=date_str, reason=reason
        )
        self.trades.append(trade)

    def _execute_sell(self, stock_code: str, price: float, date_str: str, reason: str = ""):
        """执行卖出"""
        if stock_code not in self.holding_shares or self.holding_shares[stock_code] <= 0:
            return

        actual_price = price * (1 - self.config.slippage)
        quantity = self.holding_shares[stock_code]
        amount = actual_price * quantity
        commission, tax = self._calc_commission(amount, "SELL")
        net_amount = amount - commission - tax

        self.capital += net_amount
        self.holding_shares[stock_code] = 0
        if stock_code in self.avg_cost:
            del self.avg_cost[stock_code]

        trade = TradeRecord(
            stock_code=stock_code, direction="SELL", price=actual_price,
            quantity=quantity, amount=amount, commission=commission,
            tax=tax, trade_date=date_str, reason=reason
        )
        self.trades.append(trade)

    def _calc_portfolio_value(self, prices: Dict[str, float]) -> float:
        """计算当前总资产"""
        value = self.capital
        for code, shares in self.holding_shares.items():
            if shares > 0 and code in prices:
                value += shares * prices[code]
        return value

    # ---------- 策略信号生成 ----------

    def _generate_ma_signal(self, df: pd.DataFrame, short_window: int, long_window: int):
        """生成均线信号"""
        df["ma_short"] = df["close"].rolling(window=short_window).mean()
        df["ma_long"] = df["close"].rolling(window=long_window).mean()
        df["signal"] = 0
        df.loc[df["ma_short"] > df["ma_long"], "signal"] = 1
        df.loc[df["ma_short"] <= df["ma_long"], "signal"] = -1
        return df

    def _generate_rsi_signal(self, df: pd.DataFrame, period: int, overbought: float, oversold: float):
        """生成RSI信号"""
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["signal"] = 0
        df.loc[df["rsi"] < oversold, "signal"] = 1
        df.loc[df["rsi"] > overbought, "signal"] = -1
        return df

    def _generate_macd_signal(self, df: pd.DataFrame, fast: int, slow: int, signal_period: int):
        """生成MACD信号"""
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        df["signal"] = 0
        df.loc[df["macd"] > df["macd_signal"], "signal"] = 1
        df.loc[df["macd"] <= df["macd_signal"], "signal"] = -1
        return df

    # ---------- 主回测逻辑 ----------

    def run(self) -> BacktestResult:
        """执行回测"""
        all_data: Dict[str, pd.DataFrame] = {}

        for code in self.config.stock_codes:
            df = self._fetch_stock_data(code, self.config.start_date, self.config.end_date)
            if df.empty:
                continue

            params = self.config.strategy_params
            stype = self.config.strategy_type
            if stype == "MA":
                df = self._generate_ma_signal(df, params.get("short_window", 5), params.get("long_window", 20))
            elif stype == "RSI":
                df = self._generate_rsi_signal(df, params.get("period", 14), params.get("overbought", 70), params.get("oversold", 30))
            elif stype == "MACD":
                df = self._generate_macd_signal(df, params.get("fast", 12), params.get("slow", 26), params.get("signal_period", 9))
            else:
                df = self._generate_ma_signal(df, params.get("short_window", 5), params.get("long_window", 20))

            all_data[code] = df

        if not all_data:
            return BacktestResult()

        # 合并所有交易日期
        all_dates = set()
        for df in all_data.values():
            all_dates.update(df["date"].tolist())
        all_dates = sorted(all_dates)

        # 逐日回测
        for trade_date in all_dates:
            date_str = trade_date.strftime("%Y-%m-%d") if hasattr(trade_date, "strftime") else str(trade_date)
            current_prices: Dict[str, float] = {}

            for code, df in all_data.items():
                row = df[df["date"] == trade_date]
                if row.empty:
                    continue
                row = row.iloc[0]
                current_prices[code] = row["close"]
                signal = int(row.get("signal", 0))

                if signal == 1 and code not in self.holding_shares:
                    self._execute_buy(code, row["close"], date_str, reason="策略买入信号")
                elif signal == -1 and self.holding_shares.get(code, 0) > 0:
                    self._execute_sell(code, row["close"], date_str, reason="策略卖出信号")

            equity = self._calc_portfolio_value(current_prices)
            self.equity_curve.append({"date": date_str, "equity": round(equity, 2)})

        # 计算统计指标
        result = self._calc_statistics()
        return result

    def _calc_statistics(self) -> BacktestResult:
        """计算回测统计"""
        result = BacktestResult()
        result.trades = [
            {
                "stock_code": t.stock_code, "direction": t.direction,
                "price": round(t.price, 2), "quantity": t.quantity,
                "amount": round(t.amount, 2), "commission": round(t.commission, 2),
                "tax": round(t.tax, 2), "trade_date": t.trade_date, "reason": t.reason,
            }
            for t in self.trades
        ]
        result.equity_curve = self.equity_curve
        result.total_trades = len(self.trades)

        if not self.equity_curve:
            return result

        initial = self.config.initial_capital
        final_equity = self.equity_curve[-1]["equity"]
        result.total_return = round((final_equity - initial) / initial, 4)

        # 年化收益
        start = datetime.strptime(self.equity_curve[0]["date"], "%Y-%m-%d")
        end = datetime.strptime(self.equity_curve[-1]["date"], "%Y-%m-%d")
        days = (end - start).days
        if days > 0:
            result.annual_return = round((1 + result.total_return) ** (365 / days) - 1, 4)

        # 最大回撤
        equities = [p["equity"] for p in self.equity_curve]
        peak = equities[0]
        max_dd = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        result.max_drawdown = round(max_dd, 4)

        # Sharpe比率
        if len(equities) > 1:
            returns = pd.Series(equities).pct_change().dropna()
            if returns.std() > 0:
                result.sharpe_ratio = round((returns.mean() / returns.std()) * np.sqrt(252), 2)

        # 胜率和盈亏比
        sell_trades = [t for t in self.trades if t.direction == "SELL"]
        if sell_trades:
            profits = []
            losses = []
            for t in sell_trades:
                buy_price = self.avg_cost.get(t.stock_code, t.price)
                pnl = (t.price - buy_price) * t.quantity - t.commission - t.tax
                if pnl > 0:
                    profits.append(pnl)
                else:
                    losses.append(abs(pnl))

            total_closed = len(sell_trades)
            result.win_rate = round(len(profits) / total_closed, 4) if total_closed > 0 else 0.0
            avg_profit = np.mean(profits) if profits else 0
            avg_loss = np.mean(losses) if losses else 0
            result.profit_loss_ratio = round(avg_profit / avg_loss, 2) if avg_loss > 0 else 0.0

        return result
