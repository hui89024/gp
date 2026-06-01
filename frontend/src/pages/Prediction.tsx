import { useState } from 'react';
import { Row, Col, Input, message } from 'antd';
import PredictionPanel from '../components/PredictionPanel';
import StockChart from '../components/StockChart';

const { Search } = Input;

export default function Prediction() {
  const [stockCode, setStockCode] = useState('000001');
  const [stockName, setStockName] = useState('平安银行');

  const handleSearch = (value: string) => {
    if (value.length === 6) {
      setStockCode(value);
      setStockName(value);
    } else {
      message.error('请输入6位股票代码');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Search placeholder="输入股票代码" enterButton="查询" onSearch={handleSearch} style={{ width: 400 }} />
      </div>
      <Row gutter={16}>
        <Col span={16}><StockChart stockCode={stockCode} stockName={stockName} /></Col>
        <Col span={8}><PredictionPanel stockCode={stockCode} stockName={stockName} /></Col>
      </Row>
    </div>
  );
}
