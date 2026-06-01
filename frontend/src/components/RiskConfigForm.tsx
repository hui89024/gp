import { useState, useEffect } from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Divider, message, Spin } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { autoTradingApi } from '../services/api';

interface Props {
  userId: number;
}

export default function RiskConfigForm({ userId }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await autoTradingApi.getRiskConfig(userId);
      const config = res.data;
      form.setFieldsValue({
        stop_loss_pct: config.stop_loss_pct,
        take_profit_pct: config.take_profit_pct,
        max_position_pct: config.max_position_pct,
        max_total_position_pct: config.max_total_position_pct,
        max_daily_trades: config.max_daily_trades,
        max_weekly_trades: config.max_weekly_trades,
        max_daily_loss: config.max_daily_loss,
        max_single_trade: config.max_single_trade,
      });
    } catch (err: any) {
      // 如果不存在，设置默认值
      if (err.response?.status === 404) {
        form.setFieldsValue({
          stop_loss_pct: 5,
          take_profit_pct: 10,
          max_position_pct: 30,
          max_total_position_pct: 80,
          max_daily_trades: 10,
          max_weekly_trades: 50,
          max_daily_loss: 5000,
          max_single_trade: 50000,
        });
      } else {
        message.error('获取风控配置失败: ' + (err.response?.data?.detail || err.message));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [userId]);

  const handleSubmit = async (values: any) => {
    setSaving(true);
    try {
      await autoTradingApi.updateRiskConfig(userId, values);
      message.success('风控配置保存成功');
      fetchConfig(); // 重新获取最新配置
    } catch (err: any) {
      message.error('保存失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="风控配置">
      <Spin spinning={loading}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Divider orientation="left">止损止盈</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="stop_loss_pct"
                label="止损比例 (%)"
                rules={[{ required: true, message: '请输入止损比例' }]}
                extra="当亏损达到持仓成本的该比例时触发止损"
              >
                <InputNumber
                  min={0}
                  max={100}
                  step={0.5}
                  precision={1}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="take_profit_pct"
                label="止盈比例 (%)"
                rules={[{ required: true, message: '请输入止盈比例' }]}
                extra="当盈利达到持仓成本的该比例时触发止盈"
              >
                <InputNumber
                  min={0}
                  max={1000}
                  step={1}
                  precision={1}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">仓位控制</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="max_position_pct"
                label="单只股票最大仓位 (%)"
                rules={[{ required: true, message: '请输入最大仓位比例' }]}
                extra="单只股票持仓市值占总资产的最大比例"
              >
                <InputNumber
                  min={0}
                  max={100}
                  step={5}
                  precision={0}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_total_position_pct"
                label="总仓位上限 (%)"
                rules={[{ required: true, message: '请输入总仓位上限' }]}
                extra="所有股票持仓市值之和占总资产的最大比例"
              >
                <InputNumber
                  min={0}
                  max={100}
                  step={5}
                  precision={0}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">交易频率限制</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="max_daily_trades"
                label="每日最大交易次数"
                rules={[{ required: true, message: '请输入每日最大交易次数' }]}
              >
                <InputNumber
                  min={0}
                  max={1000}
                  step={1}
                  precision={0}
                  style={{ width: '100%' }}
                  suffix="次"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_weekly_trades"
                label="每周最大交易次数"
                rules={[{ required: true, message: '请输入每周最大交易次数' }]}
              >
                <InputNumber
                  min={0}
                  max={5000}
                  step={1}
                  precision={0}
                  style={{ width: '100%' }}
                  suffix="次"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">资金限制</Divider>
          <Row gutter={24}>
            <Col span={12}>
              <Form.Item
                name="max_daily_loss"
                label="每日最大亏损额 (元)"
                rules={[{ required: true, message: '请输入每日最大亏损额' }]}
                extra="当日累计亏损达到该金额时停止自动交易"
              >
                <InputNumber
                  min={0}
                  max={1000000}
                  step={1000}
                  precision={2}
                  style={{ width: '100%' }}
                  prefix="¥"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_single_trade"
                label="单笔交易最大金额 (元)"
                rules={[{ required: true, message: '请输入单笔交易最大金额' }]}
              >
                <InputNumber
                  min={0}
                  max={10000000}
                  step={10000}
                  precision={2}
                  style={{ width: '100%' }}
                  prefix="¥"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={saving}
              size="large"
            >
              保存风控配置
            </Button>
          </Form.Item>
        </Form>
      </Spin>
    </Card>
  );
}
