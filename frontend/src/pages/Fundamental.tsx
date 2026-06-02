import { useState } from 'react';
import { Card, Input, Descriptions, Spin, message, Row, Col, Empty } from 'antd';
import { fundamentalApi } from '../services/fundamentalApi';

function FundamentalPage() {
  const [stockCode, setStockCode] = useState('');
  const [company, setCompany] = useState<any>(null);
  const [indicators, setIndicators] = useState<any>(null);
  const [_report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async (code: string) => {
    if (!code) return;
    setLoading(true);
    try {
      const [compRes, indRes, repRes] = await Promise.all([
        fundamentalApi.getCompanyInfo(code),
        fundamentalApi.getIndicators(code),
        fundamentalApi.getReport(code),
      ]);
      setCompany(compRes.data);
      setIndicators(indRes.data);
      setReport(repRes.data);
    } catch {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="输入股票代码，如 000001"
          enterButton="查询"
          size="large"
          value={stockCode}
          onChange={e => setStockCode(e.target.value)}
          onSearch={loadData}
        />
      </Card>
      <Spin spinning={loading}>
        {!company && !indicators ? (
          <Empty description="请输入股票代码查询" />
        ) : (
          <Row gutter={16}>
            <Col span={12}>
              <Card title="公司信息">
                {company && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="股票代码">{company.stock_code}</Descriptions.Item>
                    <Descriptions.Item label="公司名称">{company.company_name}</Descriptions.Item>
                    <Descriptions.Item label="行业">{company.industry}</Descriptions.Item>
                    <Descriptions.Item label="总市值">{company.total_market_cap?.toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label="流通市值">{company.circulating_market_cap?.toLocaleString()}</Descriptions.Item>
                  </Descriptions>
                )}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="财务指标">
                {indicators && (
                  <Descriptions column={1} bordered size="small">
                    <Descriptions.Item label="市盈率(PE)">{indicators.pe_ratio?.toFixed(2) ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="市净率(PB)">{indicators.pb_ratio?.toFixed(2) ?? '-'}</Descriptions.Item>
                    <Descriptions.Item label="净资产收益率(ROE)">{indicators.roe?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="销售毛利率">{indicators.gross_margin?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="销售净利率">{indicators.net_margin?.toFixed(2) ?? '-'}%</Descriptions.Item>
                    <Descriptions.Item label="资产负债率">{indicators.debt_ratio?.toFixed(2) ?? '-'}%</Descriptions.Item>
                  </Descriptions>
                )}
              </Card>
            </Col>
          </Row>
        )}
      </Spin>
    </div>
  );
}

export default FundamentalPage;
