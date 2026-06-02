from typing import List, Optional
from app.schemas.stock import StockQuote, StockHistory, StockSearchResult
from app.services.akshare_source import AKShareSource
from app.services.efinance_source import EFinanceSource
from app.config import settings


class DataService:
    """统一数据服务 - 双数据源互备"""

    def __init__(self):
        self._sources = {
            "akshare": AKShareSource(),
            "efinance": EFinanceSource(),
        }
        self._primary = settings.PRIMARY_DATA_SOURCE
        self._fallback = settings.FALLBACK_DATA_SOURCE

    def _get_sources(self):
        """按优先级返回数据源列表"""
        primary = self._sources.get(self._primary)
        fallback = self._sources.get(self._fallback)
        if primary and fallback:
            return [primary, fallback]
        return [self._sources["akshare"]]

    def get_stock_quote(self, stock_code: str) -> Optional[StockQuote]:
        """获取实时行情 - 自动切换数据源"""
        for source in self._get_sources():
            result = source.get_stock_quote(stock_code)
            if result:
                return result
        return None

    def get_stock_history(
        self, stock_code: str, days: int = 30
    ) -> List[StockHistory]:
        """获取历史数据 - 自动切换数据源"""
        for source in self._get_sources():
            result = source.get_stock_history(stock_code, days)
            if result:
                return result
        return []

    def search_stocks(self, keyword: str) -> List[StockSearchResult]:
        """搜索股票"""
        results = self._sources["akshare"].search_stocks(keyword)
        return [StockSearchResult(**r) for r in results]

    def get_kline_data(self, stock_code: str, days: int = 60) -> dict:
        """获取K线数据"""
        history = self.get_stock_history(stock_code, days)
        return {
            "dates": [h.date for h in history],
            "opens": [h.open for h in history],
            "highs": [h.high for h in history],
            "lows": [h.low for h in history],
            "closes": [h.close for h in history],
            "volumes": [h.volume for h in history]
        }
