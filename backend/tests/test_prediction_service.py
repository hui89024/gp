import pytest
from app.services.prediction_service import PredictionService


@pytest.fixture
def prediction_service(db_session):
    return PredictionService(db_session)


def test_train_model(prediction_service):
    """测试模型训练"""
    result = prediction_service.train_model("000001", days=90)
    assert "success" in result


def test_model_performance(prediction_service):
    """测试模型性能统计"""
    performance = prediction_service.get_model_performance("LSTM")
    assert performance.model_type == "LSTM"
    assert performance.total_predictions >= 0
