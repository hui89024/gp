from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.strategy_config import StrategyConfig
from app.strategies.base import BaseStrategy, Signal
from app.strategies.prediction import PredictionStrategy
from app.strategies.ma_strategy import MAStrategy
from app.strategies.rsi_strategy import RSIStrategy


class StrategyEngine:
    """策略引擎"""

    def __init__(self, db: Session):
        self.db = db
        self.strategies: Dict[str, BaseStrategy] = {}

    def load_strategies(self, user_id: int):
        configs = self.db.query(StrategyConfig).filter(
            StrategyConfig.user_id == user_id,
            StrategyConfig.enabled == True
        ).all()

        for config in configs:
            strategy = self._create_strategy(config)
            if strategy:
                self.strategies[config.strategy_name] = strategy

    def _create_strategy(self, config: StrategyConfig) -> Optional[BaseStrategy]:
        strategy_map = {
            "PREDICTION": PredictionStrategy,
            "MA": MAStrategy,
            "RSI": RSIStrategy,
        }
        strategy_class = strategy_map.get(config.strategy_type)
        if strategy_class:
            return strategy_class(config=config.config, db_session=self.db)
        return None

    def get_all_signals(self, stock_codes: List[str]) -> List[Signal]:
        all_signals = []
        for strategy in self.strategies.values():
            try:
                signals = strategy.generate_signals(stock_codes)
                all_signals.extend(signals)
            except Exception as e:
                print(f"策略{strategy.name}执行失败: {e}")
        return all_signals

    def resolve_conflicts(self, signals: List[Signal]) -> List[Signal]:
        resolved = {}
        for signal in signals:
            key = signal.stock_code
            if key not in resolved or signal.confidence > resolved[key].confidence:
                resolved[key] = signal
        return list(resolved.values())

    def create_strategy_config(self, user_id: int, strategy_name: str, strategy_type: str, config: dict) -> StrategyConfig:
        strategy_config = StrategyConfig(
            user_id=user_id,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            config=config,
            enabled=True
        )
        self.db.add(strategy_config)
        self.db.commit()
        self.db.refresh(strategy_config)
        return strategy_config

    def update_strategy_config(self, config_id: int, user_id: int, updates: dict) -> Optional[StrategyConfig]:
        config = self.db.query(StrategyConfig).filter(
            StrategyConfig.id == config_id,
            StrategyConfig.user_id == user_id
        ).first()
        if not config:
            return None
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_strategy_config(self, config_id: int, user_id: int) -> bool:
        config = self.db.query(StrategyConfig).filter(
            StrategyConfig.id == config_id,
            StrategyConfig.user_id == user_id
        ).first()
        if not config:
            return False
        self.db.delete(config)
        self.db.commit()
        return True

    def get_strategy_configs(self, user_id: int) -> List[StrategyConfig]:
        return self.db.query(StrategyConfig).filter(StrategyConfig.user_id == user_id).all()
