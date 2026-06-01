import { useState, useEffect } from 'react';
import { Row, Col } from 'antd';
import AccountOverviewComponent from '../components/AccountOverview';
import PositionList from '../components/PositionList';
import StockChart from '../components/StockChart';
import { useTradeStore } from '../stores/tradeStore';

export default function Dashboard() {
  const {
    userId,
    overview,
    positions,
    loading,
    setUserId,
  } = useTradeStore();

  useEffect(() => {
    // 临时使用固定用户ID，实际应从登录获取
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  const [selectedStock, setSelectedStock] = useState<string>('000001');

  return (
    <div>
      <AccountOverviewComponent overview={overview} loading={loading} />

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={16}>
          <StockChart stockCode={selectedStock} />
        </Col>
        <Col span={8}>
          <PositionList
            positions={positions}
            loading={loading}
            onSelect={(position) => setSelectedStock(position.stock_code)}
          />
        </Col>
      </Row>
    </div>
  );
}
