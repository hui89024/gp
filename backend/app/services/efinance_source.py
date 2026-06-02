import efinance as ef
from typing import List, Optional
from datetime import datetime

from app.schemas.stock import StockQuote, StockHistory


class EFinanceSource:
    """efinance 数据源（东方财富）"""

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情"""
        try:
            df = ef.stock.get_quote_history(stock_code, klt=1)
            if df.empty:
                return None
            row = df.iloc[-1]
            return StockQuote(
                stock_code=stock_code,
                stock_name=row.get("股票名称", ""),
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
            print(f"efinance获取行情失败: {e}")
            return None

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[StockHistory]:
        """获取历史数据"""
        try:
            df = ef.stock.get_quote_history(stock_code, klt=101)
            if df.empty:
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
