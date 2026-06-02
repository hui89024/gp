import efinance as ef
from typing import List, Optional
from datetime import datetime

from app.schemas.stock import StockQuote, StockHistory


class EFinanceSource:
    """efinance 数据源（东方财富）"""

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情 - 优先使用实时行情接口，回退到日K线"""
        try:
            # 优先使用实时行情接口
            df = ef.stock.get_realtime_quotes([stock_code])
            if df is not None and not df.empty:
                row = df.iloc[0]
                price = float(row.get("最新价", 0))
                if price > 0:
                    return StockQuote(
                        stock_code=stock_code,
                        stock_name=str(row.get("股票名称", "")),
                        current_price=price,
                        open_price=float(row.get("今开", 0)),
                        high_price=float(row.get("最高", 0)),
                        low_price=float(row.get("最低", 0)),
                        close_price=price,
                        volume=int(row.get("成交量", 0)),
                        amount=float(row.get("成交额", 0)),
                        change_percent=float(row.get("涨跌幅", 0)),
                        change_amount=float(row.get("涨跌额", 0)),
                        timestamp=datetime.now()
                    )
        except Exception as e:
            print(f"efinance实时行情失败，尝试日K线回退: {e}")

        # 回退：使用日K线最新一条数据
        try:
            df = ef.stock.get_quote_history(stock_code, klt=101)
            if df is not None and not df.empty:
                row = df.iloc[-1]
                return StockQuote(
                    stock_code=stock_code,
                    stock_name=str(row.get("股票名称", "")),
                    current_price=float(row["收盘"]),
                    open_price=float(row["开盘"]),
                    high_price=float(row["最高"]),
                    low_price=float(row["最低"]),
                    close_price=float(row["收盘"]),
                    volume=int(row["成交量"]),
                    amount=float(row["成交额"]),
                    change_percent=float(row.get("涨跌幅", 0)),
                    change_amount=float(row.get("涨跌额", 0)),
                    timestamp=datetime.now()
                )
        except Exception as e:
            print(f"efinance日K线回退也失败: {e}")

        return None

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[StockHistory]:
        """获取历史数据"""
        try:
            df = ef.stock.get_quote_history(stock_code, klt=101)
            if df is None or df.empty:
                return []
            df = df.tail(days)
            history = []
            for _, row in df.iterrows():
                history.append(StockHistory(
                    date=str(row["日期"]),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=int(row["成交量"]),
                    amount=float(row["成交额"])
                ))
            return history
        except Exception as e:
            print(f"efinance获取历史数据失败: {e}")
            return []

    def get_realtime_quotes(self, stock_codes: List[str]) -> List[dict]:
        """批量获取实时行情"""
        try:
            df = ef.stock.get_realtime_quotes(stock_codes)
            results = []
            for _, row in df.iterrows():
                results.append({
                    "stock_code": row["股票代码"],
                    "stock_name": row["股票名称"],
                    "current_price": float(row["最新价"]),
                    "change_percent": float(row["涨跌幅"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"])
                })
            return results
        except Exception as e:
            print(f"efinance批量行情失败: {e}")
            return []
