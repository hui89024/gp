import { Card, Form, Input, InputNumber, Button, Select } from 'antd';

function Trade() {
  return (
    <div>
      <h2>交易下单</h2>
      <Card>
        <Form layout="vertical">
          <Form.Item label="股票代码" name="stock_code" rules={[{ required: true }]}>
            <Input placeholder="请输入股票代码" />
          </Form.Item>
          <Form.Item label="股票名称" name="stock_name" rules={[{ required: true }]}>
            <Input placeholder="请输入股票名称" />
          </Form.Item>
          <Form.Item label="交易类型" name="trade_type" rules={[{ required: true }]}>
            <Select placeholder="请选择交易类型">
              <Select.Option value="BUY">买入</Select.Option>
              <Select.Option value="SELL">卖出</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="价格" name="price" rules={[{ required: true }]}>
            <InputNumber min={0} precision={2} placeholder="请输入价格" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="数量" name="quantity" rules={[{ required: true }]}>
            <InputNumber min={100} step={100} placeholder="请输入数量" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="策略标签" name="strategy_tag">
            <Input placeholder="可选策略标签" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交订单</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

export default Trade;
