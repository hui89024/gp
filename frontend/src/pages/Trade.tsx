import { useState, useEffect } from 'react';
import { Row, Col, message } from 'antd';
import TradeForm from '../components/TradeForm';
import PositionList from '../components/PositionList';
import StockChart from '../components/StockChart';
import { useTradeStore } from '../stores/tradeStore';

export default function Trade() {
  const {
    userId,
    positions,
    loading,
    error,
    setUserId,
    buyStock,
    sellStock,
  } = useTradeStore();

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  useEffect(() => {
    if (error) {
      message.error(error);
    }
  }, [error]);

  const [selectedStock, setSelectedStock] = useState<string>('000001');

  const handleBuy = async (stockCode: string, stockName: string, price: number, quantity: number) => {
    return await buyStock(stockCode, stockName, price, quantity);
  };

  const handleSell = async (stockCode: string, stockName: string, price: number, quantity: number) => {
    return await sellStock(stockCode, stockName, price, quantity);
  };

  return (
    <Row gutter={16}>
      <Col span={8}>
        <TradeForm
          onBuy={handleBuy}
          onSell={handleSell}
          loading={loading}
        />
      </Col>
      <Col span={16}>
        <StockChart stockCode={selectedStock} />
        <div style={{ marginTop: 16 }}>
          <PositionList
            positions={positions}
            loading={loading}
            onSelect={(position) => setSelectedStock(position.stock_code)}
          />
        </div>
      </Col>
    </Row>
  );
}
