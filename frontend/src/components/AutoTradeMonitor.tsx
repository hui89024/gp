import { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, Badge, message, Divider } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import type { AutoTradingStatus, AutoTradingStatistics, AutoTradeLog } from '../types';
import { autoTradingApi } from '../services/api';

interface Props {
  userId: number;
}

export default function AutoTradeMonitor({ userId }: Props) {
  const [status, setStatus] = useState<AutoTradingStatus | null>(null);
  const [statistics, setStatistics] = useState<AutoTradingStatistics | null>(null);
  const [logs, setLogs] = useState<AutoTradeLog[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, statsRes, logsRes] = await Promise.all([
        autoTradingApi.getStatus(userId),
        autoTradingApi.getStatistics(userId),
        autoTradingApi.getLogs(userId, 20),
      ]);
      setStatus(statusRes.data);
      setStatistics(statsRes.data);
      setLogs(logsRes.data);
    } catch (err: any) {
      message.error('获取监控数据失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchAll();
    const timer = setInterval(fetchAll, 30000); // 30秒刷新一次
    return () => clearInterval(timer);
  }, [fetchAll]);

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '股票',
      key: 'stock',
      width: 120,
      render: (_: any, record: AutoTradeLog) => (
        <span>{record.stock_code} {record.stock_name}</span>
      ),
    },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      width: 80,
      render: (text: string | null) => {
        if (!text) return '-';
        return (
          <Tag color={text === 'BUY' ? 'green' : 'red'}>
            {text === 'BUY' ? '买入' : '卖出'}
          </Tag>
        );
      },
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (val: number | null) => val != null ? `¥${val.toFixed(2)}` : '-',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (val: number | null) => val != null ? val : '-',
    },
    {
      title: '信心度',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 90,
      render: (val: number | null) => {
        if (val == null) return '-';
        const percent = (val * 100).toFixed(0);
        let color = 'green';
        if (val < 0.6) color = 'red';
        else if (val < 0.8) color = 'orange';
        return <Tag color={color}>{percent}%</Tag>;
      },
    },
    {
      title: '风控',
      key: 'risk',
      width: 100,
      render: (_: any, record: AutoTradeLog) => {
        if (record.risk_check_passed == null) return '-';
        return record.risk_check_passed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">通过</Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">拒绝</Tag>
        );
      },
    },
    {
      title: '执行结果',
      key: 'result',
      width: 120,
      render: (_: any, record: AutoTradeLog) => {
        if (record.error_message) {
          return <Tag icon={<WarningOutlined />} color="error">失败</Tag>;
        }
        if (record.execution_result === 'success') {
          return <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag>;
        }
        return record.execution_result || '-';
      },
    },
    {
      title: '信号源',
      dataIndex: 'signal_source',
      key: 'signal_source',
      width: 100,
      render: (text: string | null) => text || '-',
    },
  ];

  return (
    <div>
      <Card title="自动交易状态" loading={loading}>
        <Row gutter={16}>
          <Col span={4}>
            <Statistic
              title="运行状态"
              value={status?.running ? '运行中' : '已停止'}
              valueStyle={{ color: status?.running ? '#3f8600' : '#999' }}
              prefix={status?.running ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="活跃任务数"
              value={status?.active_tasks ?? 0}
              suffix="个"
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="活跃策略数"
              value={status?.active_strategies ?? 0}
              suffix="个"
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="今日交易次数"
              value={status?.today_trades ?? 0}
              suffix="笔"
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="今日盈亏"
              value={status?.today_pnl ?? 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: (status?.today_pnl ?? 0) >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
        </Row>
      </Card>

      <Card title="交易统计" style={{ marginTop: 16 }} loading={loading}>
        <Row gutter={16}>
          <Col span={3}>
            <Statistic title="总交易次数" value={statistics?.total_trades ?? 0} suffix="笔" />
          </Col>
          <Col span={3}>
            <Statistic title="盈利次数" value={statistics?.winning_trades ?? 0} suffix="笔" valueStyle={{ color: '#3f8600' }} />
          </Col>
          <Col span={3}>
            <Statistic title="亏损次数" value={statistics?.losing_trades ?? 0} suffix="笔" valueStyle={{ color: '#cf1322' }} />
          </Col>
          <Col span={3}>
            <Statistic title="胜率" value={(statistics?.win_rate ?? 0) * 100} precision={1} suffix="%" />
          </Col>
          <Col span={3}>
            <Statistic
              title="总盈亏"
              value={statistics?.total_pnl ?? 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: (statistics?.total_pnl ?? 0) >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={3}>
            <Statistic title="平均盈亏" value={statistics?.avg_pnl_per_trade ?? 0} precision={2} prefix="¥" />
          </Col>
          <Col span={3}>
            <Statistic title="最大单笔盈利" value={statistics?.max_win ?? 0} precision={2} prefix="¥" valueStyle={{ color: '#3f8600' }} />
          </Col>
          <Col span={3}>
            <Statistic title="最大单笔亏损" value={statistics?.max_loss ?? 0} precision={2} prefix="¥" valueStyle={{ color: '#cf1322' }} />
          </Col>
        </Row>
      </Card>

      <Card
        title="交易日志"
        style={{ marginTop: 16 }}
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchAll} loading={loading}>
            刷新
          </Button>
        }
      >
        <Table
          dataSource={logs}
          columns={logColumns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
}
