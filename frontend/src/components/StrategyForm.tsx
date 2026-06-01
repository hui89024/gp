import { useState, useEffect } from 'react';
import { Card, Form, Input, Select, Switch, Button, InputNumber, Space, message } from 'antd';
import type { StrategyConfig } from '../types';
import { autoTradingApi } from '../services/api';

interface Props {
  userId: number;
  editingStrategy: StrategyConfig | null;
  onSuccess: () => void;
  onCancel: () => void;
}

const { TextArea } = Input;

export default function StrategyForm({ userId, editingStrategy, onSuccess, onCancel }: Props) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [strategyType, setStrategyType] = useState<string>('PREDICTION');

  useEffect(() => {
    if (editingStrategy) {
      form.setFieldsValue({
        strategy_name: editingStrategy.strategy_name,
        strategy_type: editingStrategy.strategy_type,
        enabled: editingStrategy.enabled,
        config: JSON.stringify(editingStrategy.config, null, 2),
      });
      setStrategyType(editingStrategy.strategy_type);
    } else {
      form.resetFields();
      form.setFieldsValue({
        strategy_type: 'PREDICTION',
        enabled: true,
        config: '{}',
      });
      setStrategyType('PREDICTION');
    }
  }, [editingStrategy, form]);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      let configObj: Record<string, any>;
      try {
        configObj = JSON.parse(values.config);
      } catch {
        message.error('配置JSON格式不正确');
        setLoading(false);
        return;
      }

      const data = {
        strategy_name: values.strategy_name,
        strategy_type: values.strategy_type,
        config: configObj,
        enabled: values.enabled,
      };

      if (editingStrategy) {
        await autoTradingApi.updateStrategy(editingStrategy.id, userId, data);
        message.success('策略更新成功');
      } else {
        await autoTradingApi.createStrategy(userId, data);
        message.success('策略创建成功');
      }
      onSuccess();
    } catch (err: any) {
      message.error('操作失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getConfigHint = (type: string) => {
    const hints: Record<string, string> = {
      PREDICTION: '{"confidence_threshold": 0.7, "auto_execute": true}',
      MA: '{"short_window": 5, "long_window": 20, "volume_filter": true}',
      RSI: '{"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}',
      RULE: '{"rules": [{"condition": "price_change > 0.05", "action": "sell"}]}',
    };
    return hints[type] || '{}';
  };

  return (
    <Card title={editingStrategy ? '编辑策略' : '新建策略'}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="strategy_name"
          label="策略名称"
          rules={[{ required: true, message: '请输入策略名称' }]}
        >
          <Input placeholder="请输入策略名称" />
        </Form.Item>

        <Form.Item
          name="strategy_type"
          label="策略类型"
          rules={[{ required: true, message: '请选择策略类型' }]}
        >
          <Select
            placeholder="请选择策略类型"
            onChange={(value) => setStrategyType(value)}
          >
            <Select.Option value="PREDICTION">预测信号策略</Select.Option>
            <Select.Option value="MA">均线策略</Select.Option>
            <Select.Option value="RSI">RSI策略</Select.Option>
            <Select.Option value="RULE">规则策略</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="enabled"
          label="启用状态"
          valuePropName="checked"
        >
          <Switch checkedChildren="启用" unCheckedChildren="禁用" />
        </Form.Item>

        <Form.Item
          name="config"
          label="策略配置 (JSON)"
          rules={[
            { required: true, message: '请输入策略配置' },
            {
              validator: (_, value) => {
                try {
                  JSON.parse(value);
                  return Promise.resolve();
                } catch {
                  return Promise.reject('请输入有效的JSON格式');
                }
              },
            },
          ]}
          extra={`参考格式: ${getConfigHint(strategyType)}`}
        >
          <TextArea rows={8} placeholder="请输入JSON格式的策略配置" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {editingStrategy ? '更新策略' : '创建策略'}
            </Button>
            <Button onClick={onCancel}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
}
