import akshare as ak
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult


class DataService:
    """股票数据服务"""

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """
        获取股票实时行情

        Args:
            stock_code: 股票代码 (如 000001)

        Returns:
            实时行情数据
        """
        try:
            df = ak.stock_zh_a_spot_em()
            stock = df[df["代码"] == stock_code]

            if stock.empty:
                return None

            row = stock.iloc[0]
            return StockQuote(
                stock_code=stock_code,
                stock_name=row["名称"],
                current_price=float(row["最新价"]),
                open_price=float(row["今开"]),
                high_price=float(row["最高"]),
                low_price=float(row["最低"]),
                close_price=float(row["最新价"]),
                volume=int(row["成交量"]),
                amount=float(row["成交额"]),
                change_percent=float(row["涨跌幅"]),
                change_amount=float(row["涨跌额"]),
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"获取行情失败: {e}")
            return None

    def get_stock_history(
        self, stock_code: str, days: int = 30
    ) -> List[StockHistory]:
        """
        获取股票历史数据

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            历史数据列表
        """
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

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
            print(f"获取历史数据失败: {e}")
            return []

    def search_stocks(self, keyword: str) -> List[StockSearchResult]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词

        Returns:
            搜索结果列表
        """
        try:
            df = ak.stock_zh_a_spot_em()
            matches = df[
                df["名称"].str.contains(keyword, na=False) |
                df["代码"].str.contains(keyword, na=False)
            ].head(10)

            results = []
            for _, row in matches.iterrows():
                results.append(StockSearchResult(
                    stock_code=row["代码"],
                    stock_name=row["名称"],
                    market=row.get("市场", "A股")
                ))

            return results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def get_kline_data(self, stock_code: str, days: int = 60) -> dict:
        """
        获取K线数据（用于前端图表）

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            K线数据字典
        """
        history = self.get_stock_history(stock_code, days)

        return {
            "dates": [h.date for h in history],
            "opens": [h.open for h in history],
            "highs": [h.high for h in history],
            "lows": [h.low for h in history],
            "closes": [h.close for h in history],
            "volumes": [h.volume for h in history]
        }
