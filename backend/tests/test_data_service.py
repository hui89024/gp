import pytest
from app.services.data_service import DataService


@pytest.fixture
def data_service():
    return DataService()


def test_get_stock_quote(data_service):
    """测试获取实时行情"""
    quote = data_service.get_stock_quote("000001")
    assert quote is not None
    assert quote.stock_code == "000001"
    assert quote.current_price > 0


def test_get_stock_history(data_service):
    """测试获取历史数据"""
    history = data_service.get_stock_history("000001", days=30)
    assert len(history) > 0
    assert len(history) <= 30
    assert history[0].close > 0


def test_search_stocks(data_service):
    """测试股票搜索"""
    results = data_service.search_stocks("平安")
    assert len(results) > 0
    assert any("平安" in r.stock_name for r in results)
