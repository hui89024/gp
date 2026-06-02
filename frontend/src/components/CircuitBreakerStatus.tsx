import { useState, useEffect } from 'react';
import { Card, Tag, Button, List, message } from 'antd';
import { WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { riskControlApi } from '../services/api';

interface Props {
  userId: number;
}

export default function CircuitBreakerStatusComponent({ userId }: Props) {
  const [status, setStatus] = useState<{ is_triggered: boolean; trigger_reason: string | null } | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchEvents();
  }, [userId]);

  const fetchStatus = async () => {
    try {
      const response = await riskControlApi.getCircuitBreakerStatus(userId);
      setStatus(response.data);
    } catch (error) {
      console.error('获取状态失败:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await riskControlApi.getAlertRecords(userId, 10);
      setEvents(response.data);
    } catch (error) {
      console.error('获取事件失败:', error);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await riskControlApi.resetCircuitBreaker(userId);
      message.success('熔断器已重置');
      fetchStatus();
    } catch (error) {
      message.error('重置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="风控熔断状态"
      extra={status?.is_triggered && (
        <Button danger onClick={handleReset} loading={loading}>重置熔断器</Button>
      )}
    >
      <div style={{ marginBottom: 16 }}>
        {status?.is_triggered ? (
          <Tag icon={<WarningOutlined />} color="error" style={{ fontSize: 16, padding: '8px 16px' }}>
            熔断已触发: {status.trigger_reason}
          </Tag>
        ) : (
          <Tag icon={<CheckCircleOutlined />} color="success" style={{ fontSize: 16, padding: '8px 16px' }}>
            正常运行
          </Tag>
        )}
      </div>
      <List
        header="最近事件"
        dataSource={events}
        renderItem={(item: any) => (
          <List.Item>
            <List.Item.Meta title={item.rule_name} description={item.message} />
            <div>{new Date(item.created_at).toLocaleString()}</div>
          </List.Item>
        )}
      />
    </Card>
  );
}
