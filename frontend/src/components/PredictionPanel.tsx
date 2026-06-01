import { useState, useEffect } from 'react';
import { Card, Button, Tag, Space, message, Spin } from 'antd';
import { ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';
import { predictionApi } from '../services/api';
import type { PredictionSignal, ModelPerformance } from '../types';

interface Props {
  stockCode: string;
  stockName: string;
}

export default function PredictionPanel({ stockCode, stockName }: Props) {
  const [signal, setSignal] = useState<PredictionSignal | null>(null);
  const [performance, setPerformance] = useState<ModelPerformance | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    if (stockCode) {
      fetchSignal();
      fetchPerformance();
    }
  }, [stockCode]);

  const fetchSignal = async () => {
    setLoading(true);
    try {
      const response = await predictionApi.getSignal(stockCode);
      setSignal(response.data);
    } catch (error) {
      console.error('获取预测信号失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformance = async () => {
    try {
      const response = await predictionApi.getPerformance();
      setPerformance(response.data);
    } catch (error) {
      console.error('获取模型性能失败:', error);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      await predictionApi.train(stockCode, 180);
      message.success('模型训练完成');
      await fetchSignal();
      await fetchPerformance();
    } catch (error) {
      message.error('模型训练失败');
    } finally {
      setTraining(false);
    }
  };

  const getDirectionColor = (direction: string) => direction === 'UP' ? 'green' : 'red';
  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'STRONG': return 'gold';
      case 'MEDIUM': return 'blue';
      case 'WEAK': return 'default';
      default: return 'default';
    }
  };

  return (
    <Card
      title={`AI预测 - ${stockName} (${stockCode})`}
      extra={
        <Space>
          <Button icon={<ThunderboltOutlined />} onClick={handleTrain} loading={training}>
            训练模型
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchSignal} loading={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        {signal ? (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>当前价格:</span>
                <span style={{ fontSize: 18, fontWeight: 'bold' }}>¥{signal.current_price.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>预测方向:</span>
                <Tag color={getDirectionColor(signal.predicted_direction)} style={{ fontSize: 16 }}>
                  {signal.predicted_direction === 'UP' ? '看涨 ↑' : '看跌 ↓'}
                </Tag>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>预测价格:</span>
                <span>¥{signal.predicted_price.toFixed(2)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>置信度:</span>
                <span>{(signal.confidence * 100).toFixed(1)}%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>信号强度:</span>
                <Tag color={getStrengthColor(signal.signal_strength)}>{signal.signal_strength}</Tag>
              </div>
            </Space>

            {performance && performance.total_predictions > 0 && (
              <div style={{ marginTop: 16, padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', marginBottom: 8 }}>模型统计</div>
                <div>总预测: {performance.total_predictions} 次</div>
                <div>准确率: {(performance.accuracy * 100).toFixed(1)}%</div>
                <div>平均置信度: {(performance.avg_confidence * 100).toFixed(1)}%</div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <p>暂无预测数据</p>
            <Button type="primary" onClick={handleTrain} loading={training}>点击训练模型</Button>
          </div>
        )}
      </Spin>
    </Card>
  );
}
