import { useState, useEffect } from 'react';
import { Card, Table, Button, Form, InputNumber, Input, message, Tabs, Tag, Row, Col, Statistic } from 'antd';
import { liveTradeApi, LiveTrade as LiveTradeType } from '../services/liveTradeApi';

function LiveTradePage() {
  const [trades, setTrades] = useState<LiveTradeType[]>([]);
  const [_positions, setPositions] = useState<any[]>([]);
  const [balance, setBalance] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [buyForm] = Form.useForm();
  const [sellForm] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const [tradesRes, posRes, balRes] = await Promise.all([
        liveTradeApi.history(),
        liveTradeApi.positions().catch(() => ({ data: [] })),
        liveTradeApi.balance().catch(() => ({ data: null })),
      ]);
      setTrades(tradesRes.data);
      setPositions(posRes.data || []);
      setBalance(balRes.data);
    } catch {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleBuy = async () => {
    try {
      const values = await buyForm.validateFields();
      await liveTradeApi.buy({ ...values, stock_name: '' });
      message.success('买入成功');
      buyForm.resetFields();
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '买入失败');
    }
  };

  const handleSell = async () => {
    try {
      const values = await sellForm.validateFields();
      await liveTradeApi.sell({ ...values, stock_name: '' });
      message.success('卖出成功');
      sellForm.resetFields();
      loadData();
    } catch (e: any) {
      message.error(e.response?.data?.detail || '卖出失败');
    }
  };

  const tradeColumns = [
    { title: '时间', dataIndex: 'trade_time', key: 'trade_time', render: (t: string) => new Date(t).toLocaleString() },
    { title: '股票', dataIndex: 'stock_code', key: 'stock_code' },
    { title: '名称', dataIndex: 'stock_name', key: 'stock_name' },
    { title: '类型', dataIndex: 'trade_type', key: 'trade_type', render: (t: string) => <Tag color={t === 'BUY' ? 'green' : 'red'}>{t === 'BUY' ? '买入' : '卖出'}</Tag> },
    { title: '价格', dataIndex: 'price', key: 'price' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  return (
    <div>
      {balance && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Card><Statistic title="总资产" value={balance.total_assets} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="可用资金" value={balance.available_cash} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="市值" value={balance.market_value} precision={2} /></Card></Col>
          <Col span={6}><Card><Statistic title="冻结资金" value={balance.frozen_amount} precision={2} /></Card></Col>
        </Row>
      )}
      <Tabs items={[
        {
          key: 'trade', label: '交易下单',
          children: (
            <Row gutter={16}>
              <Col span={12}>
                <Card title="买入">
                  <Form form={buyForm} layout="vertical">
                    <Form.Item name="stock_code" label="股票代码" rules={[{ required: true }]}>
                      <Input placeholder="如 000001" />
                    </Form.Item>
                    <Form.Item name="price" label="价格" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={0.01} min={0} />
                    </Form.Item>
                    <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={100} min={100} />
                    </Form.Item>
                    <Button type="primary" onClick={handleBuy} block>买入</Button>
                  </Form>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="卖出">
                  <Form form={sellForm} layout="vertical">
                    <Form.Item name="stock_code" label="股票代码" rules={[{ required: true }]}>
                      <Input placeholder="如 000001" />
                    </Form.Item>
                    <Form.Item name="price" label="价格" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={0.01} min={0} />
                    </Form.Item>
                    <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
                      <InputNumber style={{ width: '100%' }} step={100} min={100} />
                    </Form.Item>
                    <Button type="primary" danger onClick={handleSell} block>卖出</Button>
                  </Form>
                </Card>
              </Col>
            </Row>
          )
        },
        {
          key: 'history', label: '交易记录',
          children: <Table dataSource={trades} columns={tradeColumns} rowKey="id" loading={loading} />,
        },
      ]} />
    </div>
  );
}

export default LiveTradePage;
