import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, List, Spin, Button } from 'antd';
import { WarningOutlined, ReloadOutlined } from '@ant-design/icons';
import { reviewApi } from '../services/api';
import type { ComprehensiveReview } from '../types';

interface Props {
  userId: number;
}

export default function ReviewPanel({ userId }: Props) {
  const [review, setReview] = useState<ComprehensiveReview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchReview();
  }, [userId]);

  const fetchReview = async () => {
    setLoading(true);
    try {
      const response = await reviewApi.getComprehensiveReview(userId);
      setReview(response.data);
    } catch (error) {
      console.error('获取复盘数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!review) {
    return (
      <Card title="复盘分析" loading={loading}>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <p>暂无复盘数据</p>
          <Button type="primary" onClick={fetchReview}>刷新</Button>
        </div>
      </Card>
    );
  }

  const { daily_summary, weekly_summary, strategy_analysis, behavior_analysis, recommendations } = review;

  const strategyColumns = [
    { title: '策略', dataIndex: 'strategy_tag', key: 'strategy_tag' },
    { title: '交易次数', dataIndex: 'total_trades', key: 'total_trades' },
    { title: '胜率', dataIndex: 'win_rate', key: 'win_rate', render: (v: number) => `${(v * 100).toFixed(1)}%` },
    { title: '总盈亏', dataIndex: 'total_pnl', key: 'total_pnl', render: (v: number) => (
      <Tag color={v >= 0 ? 'green' : 'red'}>{v >= 0 ? '+' : ''}{v.toFixed(2)}</Tag>
    )},
  ];

  return (
    <Card title="复盘分析" extra={<Button icon={<ReloadOutlined />} onClick={fetchReview}>刷新</Button>}>
      <Spin spinning={loading}>
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic title="今日交易" value={daily_summary.total_trades} suffix="笔" />
          </Col>
          <Col span={6}>
            <Statistic title="今日盈亏" value={daily_summary.total_pnl} precision={2} prefix="¥"
              valueStyle={{ color: daily_summary.total_pnl >= 0 ? '#3f8600' : '#cf1322' }} />
          </Col>
          <Col span={6}>
            <Statistic title="胜率" value={daily_summary.win_rate * 100} precision={1} suffix="%" />
          </Col>
          <Col span={6}>
            <Statistic title="盈利交易" value={daily_summary.winning_trades} suffix={`/ ${daily_summary.total_trades}`} />
          </Col>
        </Row>

        {weekly_summary && (
          <Card type="inner" title="本周概览" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={8}><Statistic title="本周交易" value={weekly_summary.total_trades} suffix="笔" /></Col>
              <Col span={8}><Statistic title="本周盈亏" value={weekly_summary.total_pnl} precision={2} prefix="¥"
                valueStyle={{ color: weekly_summary.total_pnl >= 0 ? '#3f8600' : '#cf1322' }} /></Col>
              <Col span={8}><Statistic title="本周胜率" value={weekly_summary.win_rate * 100} precision={1} suffix="%" /></Col>
            </Row>
          </Card>
        )}

        <Card type="inner" title="行为分析" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}><Statistic title="交易频率" value={behavior_analysis.trade_frequency} precision={1} suffix="笔/天" /></Col>
            <Col span={8}><Statistic title="情绪化交易" value={behavior_analysis.emotional_trades} suffix="次" /></Col>
            <Col span={8}><Statistic title="过度交易天数" value={behavior_analysis.overtrading_days} suffix="天"
              valueStyle={{ color: behavior_analysis.overtrading_days > 3 ? '#cf1322' : undefined }} /></Col>
          </Row>
        </Card>

        {strategy_analysis.length > 0 && (
          <Card type="inner" title="策略分析" style={{ marginBottom: 24 }}>
            <Table columns={strategyColumns} dataSource={strategy_analysis} rowKey="strategy_tag" pagination={false} />
          </Card>
        )}

        <Card type="inner" title="改进建议">
          <List dataSource={recommendations} renderItem={(item) => (
            <List.Item><WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />{item}</List.Item>
          )} />
        </Card>
      </Spin>
    </Card>
  );
}
