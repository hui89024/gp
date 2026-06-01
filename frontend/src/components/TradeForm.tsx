import { useState } from 'react';
import { Card, Form, Input, InputNumber, Button, Space, message } from 'antd';
import { stockApi } from '../services/api';
import type { StockQuote } from '../types';

interface Props {
  onBuy: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  onSell: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  loading?: boolean;
}

export default function TradeForm({ onBuy, onSell, loading }: Props) {
  const [stockCode, setStockCode] = useState('');
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [price, setPrice] = useState<number>(0);
  const [quantity, setQuantity] = useState<number>(100);
  const [fetching, setFetching] = useState(false);

  const handleSearch = async () => {
    if (stockCode.length !== 6) {
      message.error('请输入6位股票代码');
      return;
    }

    setFetching(true);
    try {
      const response = await stockApi.getQuote(stockCode);
      setQuote(response.data);
      setPrice(response.data.current_price);
    } catch (error) {
      message.error('获取股票信息失败');
    } finally {
      setFetching(false);
    }
  };

  const handleBuy = async () => {
    if (!quote) return;
    const success = await onBuy(stockCode, quote.stock_name, price, quantity);
    if (success) {
      message.success('买入成功');
    }
  };

  const handleSell = async () => {
    if (!quote) return;
    const success = await onSell(stockCode, quote.stock_name, price, quantity);
    if (success) {
      message.success('卖出成功');
    }
  };

  const totalAmount = price * quantity;

  return (
    <Card title="交易下单">
      <Form layout="vertical">
        <Form.Item label="股票代码">
          <Space>
            <Input
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              placeholder="请输入6位股票代码"
              maxLength={6}
              style={{ width: 200 }}
            />
            <Button onClick={handleSearch} loading={fetching}>
              查询
            </Button>
          </Space>
        </Form.Item>

        {quote && (
          <>
            <Form.Item label="股票信息">
              <Space>
                <span>{quote.stock_name}</span>
                <span style={{ color: quote.change_percent >= 0 ? '#3f8600' : '#cf1322' }}>
                  ¥{quote.current_price.toFixed(2)} ({quote.change_percent >= 0 ? '+' : ''}{quote.change_percent.toFixed(2)}%)
                </span>
              </Space>
            </Form.Item>

            <Form.Item label="委托价格">
              <InputNumber
                value={price}
                onChange={(value) => setPrice(value || 0)}
                min={0}
                step={0.01}
                precision={2}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item label="委托数量">
              <InputNumber
                value={quantity}
                onChange={(value) => setQuantity(value || 0)}
                min={100}
                step={100}
                style={{ width: 200 }}
              />
            </Form.Item>

            <Form.Item label="预估金额">
              <span>¥{totalAmount.toFixed(2)}</span>
            </Form.Item>

            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  onClick={handleBuy}
                  loading={loading}
                  style={{ backgroundColor: '#3f8600' }}
                >
                  买入
                </Button>
                <Button
                  danger
                  onClick={handleSell}
                  loading={loading}
                >
                  卖出
                </Button>
              </Space>
            </Form.Item>
          </>
        )}
      </Form>
    </Card>
  );
}
