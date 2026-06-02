import akshare as ak
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.fundamental_data import FundamentalData


class FundamentalService:
    """基本面数据服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_financial_report(self, stock_code: str) -> dict:
        """获取财务报表（资产负债表、利润表、现金流量表）"""
        cached = self._get_cached(stock_code, "financial_report")
        if cached:
            return cached

        try:
            balance = ak.stock_balance_sheet_by_report_em(symbol=stock_code)
            income = ak.stock_profit_sheet_by_report_em(symbol=stock_code)
            cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)

            data = {
                "balance_sheet": balance.head(4).to_dict(orient="records") if not balance.empty else [],
                "income_statement": income.head(4).to_dict(orient="records") if not income.empty else [],
                "cash_flow": cash_flow.head(4).to_dict(orient="records") if not cash_flow.empty else [],
            }
            self._save_cache(stock_code, "financial_report", data)
            return data
        except Exception as e:
            print(f"获取财务报表失败: {e}")
            return {}

    def get_financial_indicators(self, stock_code: str) -> dict:
        """获取财务指标"""
        cached = self._get_cached(stock_code, "financial_indicators")
        if cached:
            return cached

        try:
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            if df.empty:
                return {}
            row = df.iloc[0]
            data = {
                "pe_ratio": self._safe_float(row.get("市盈率(每股)")),
                "pb_ratio": self._safe_float(row.get("市净率")),
                "roe": self._safe_float(row.get("净资产收益率(%)")),
                "gross_margin": self._safe_float(row.get("销售毛利率(%)")),
                "net_margin": self._safe_float(row.get("销售净利率(%)")),
                "debt_ratio": self._safe_float(row.get("资产负债率(%)")),
            }
            self._save_cache(stock_code, "financial_indicators", data)
            return data
        except Exception as e:
            print(f"获取财务指标失败: {e}")
            return {}

    def get_company_info(self, stock_code: str) -> dict:
        """获取公司基本信息"""
        cached = self._get_cached(stock_code, "company_info")
        if cached:
            return cached

        try:
            df = ak.stock_individual_info_em(symbol=stock_code)
            if df.empty:
                return {}
            info = {}
            for _, row in df.iterrows():
                info[row["item"]] = row["value"]
            data = {
                "stock_code": stock_code,
                "company_name": info.get("股票简称", ""),
                "main_business": info.get("行业", ""),
                "industry": info.get("行业", ""),
                "total_market_cap": self._safe_float(info.get("总市值")),
                "circulating_market_cap": self._safe_float(info.get("流通市值")),
            }
            self._save_cache(stock_code, "company_info", data)
            return data
        except Exception as e:
            print(f"获取公司信息失败: {e}")
            return {}

    def _get_cached(self, stock_code: str, data_type: str) -> Optional[dict]:
        """从缓存获取数据（24小时内有效）"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        record = self.db.query(FundamentalData).filter(
            FundamentalData.stock_code == stock_code,
            FundamentalData.data_type == data_type,
            FundamentalData.updated_at >= cutoff
        ).first()
        if record:
            return record.data
        return None

    def _save_cache(self, stock_code: str, data_type: str, data: dict):
        """保存数据到缓存"""
        record = self.db.query(FundamentalData).filter(
            FundamentalData.stock_code == stock_code,
            FundamentalData.data_type == data_type,
        ).first()
        if record:
            record.data = data
            record.updated_at = datetime.utcnow()
        else:
            record = FundamentalData(
                stock_code=stock_code,
                data_type=data_type,
                data=data,
                report_date=datetime.utcnow().date()
            )
            self.db.add(record)
        self.db.commit()

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """安全转换为 float"""
        try:
            if value is None or value == "" or value == "--":
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
