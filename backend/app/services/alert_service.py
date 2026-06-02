from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.alert_record import AlertRecord


class AlertService:
    """告警服务"""

    def __init__(self, db: Session):
        self.db = db
        self.notifiers = {
            "dingtalk": DingTalkNotifier(),
            "email": EmailNotifier(),
        }
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> List[Dict]:
        """加载默认告警规则"""
        return [
            {
                "name": "单日亏损告警",
                "condition": lambda ctx: ctx.get("daily_loss_pct", 0) < -0.03,
                "severity": "WARNING",
                "channels": ["dingtalk"],
                "message": "单日亏损超过3%"
            },
            {
                "name": "连续亏损告警",
                "condition": lambda ctx: ctx.get("consecutive_losses", 0) >= 3,
                "severity": "CRITICAL",
                "channels": ["dingtalk", "email"],
                "message": "连续亏损{consecutive_losses}次"
            },
            {
                "name": "熔断触发告警",
                "condition": lambda ctx: ctx.get("circuit_breaker_triggered", False),
                "severity": "CRITICAL",
                "channels": ["dingtalk", "email"],
                "message": "风控熔断已触发: {reason}"
            },
        ]

    def check_and_alert(self, user_id: int, context: Dict[str, Any]):
        """检查并发送告警"""
        for rule in self.rules:
            try:
                if rule["condition"](context):
                    message = rule["message"].format(**context)
                    self._send_alert(user_id, rule["name"], rule["severity"],
                                   message, rule["channels"])
            except Exception as e:
                print(f"告警规则执行失败: {e}")

    def _send_alert(self, user_id: int, rule_name: str, severity: str,
                   message: str, channels: List[str]):
        """发送告警"""
        record = AlertRecord(
            user_id=user_id,
            rule_name=rule_name,
            severity=severity,
            message=message,
            channels=channels,
            sent=True,
            sent_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()

        for channel in channels:
            notifier = self.notifiers.get(channel)
            if notifier:
                try:
                    notifier.send(user_id, message, severity)
                except Exception as e:
                    print(f"发送{channel}通知失败: {e}")

    def get_records(self, user_id: int, limit: int = 50) -> List[AlertRecord]:
        """获取告警记录"""
        return self.db.query(AlertRecord).filter(
            AlertRecord.user_id == user_id
        ).order_by(AlertRecord.created_at.desc()).limit(limit).all()

    def test_alert(self, user_id: int, channel: str) -> bool:
        """测试告警"""
        notifier = self.notifiers.get(channel)
        if not notifier:
            return False
        try:
            notifier.send(user_id, "这是一条测试告警", "INFO")
            return True
        except Exception:
            return False


class DingTalkNotifier:
    """钉钉通知"""

    def send(self, user_id: int, message: str, severity: str):
        print(f"[钉钉] [{severity}] {message}")


class EmailNotifier:
    """邮件通知"""

    def send(self, user_id: int, message: str, severity: str):
        print(f"[邮件] [{severity}] {message}")
