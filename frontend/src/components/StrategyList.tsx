import { useState, useEffect } from 'react';
import { Card, Table, Switch, Button, Space, Tag, Popconfirm, message } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import type { StrategyConfig } from '../types';
import { autoTradingApi } from '../services/api';

interface Props {
  userId: number;
  onEdit: (strategy: StrategyConfig) => void;
  onCreate: () => void;
  refreshTrigger?: number;
}

export default function StrategyList({ userId, onEdit, onCreate, refreshTrigger }: Props) {
  const [strategies, setStrategies] = useState<StrategyConfig[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchStrategies = async () => {
    setLoading(true);
    try {
      const res = await autoTradingApi.getStrategies(userId);
      setStrategies(res.data);
    } catch (err: any) {
      message.error('获取策略列表失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, [userId, refreshTrigger]);

  const handleToggleEnabled = async (strategy: StrategyConfig) => {
    try {
      await autoTradingApi.updateStrategy(strategy.id, userId, { enabled: !strategy.enabled });
      message.success(strategy.enabled ? '策略已禁用' : '策略已启用');
      fetchStrategies();
    } catch (err: any) {
      message.error('操作失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDelete = async (strategyId: number) => {
    try {
      await autoTradingApi.deleteStrategy(strategyId, userId);
      message.success('策略已删除');
      fetchStrategies();
    } catch (err: any) {
      message.error('删除失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStrategyTypeLabel = (type: string) => {
    const map: Record<string, { label: string; color: string }> = {
      PREDICTION: { label: '预测信号', color: 'blue' },
      MA: { label: '均线策略', color: 'green' },
      RSI: { label: 'RSI策略', color: 'orange' },
      RULE: { label: '规则策略', color: 'purple' },
    };
    const info = map[type] || { label: type, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
    },
    {
      title: '策略类型',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      render: (type: string) => getStrategyTypeLabel(type),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: StrategyConfig) => (
        <Switch
          checked={enabled}
          onChange={() => handleToggleEnabled(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: StrategyConfig) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => onEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此策略?"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="策略列表"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={onCreate}>
          新建策略
        </Button>
      }
    >
      <Table
        dataSource={strategies}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
      />
    </Card>
  );
}
