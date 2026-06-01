import { useState, useEffect } from 'react';
import { Tabs, Row, Col, Card, Form, Select, InputNumber, Button, Tag, Space, message, Modal, Input } from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { StrategyConfig, AutoTradeTask } from '../types';
import { autoTradingApi } from '../services/api';
import StrategyList from '../components/StrategyList';
import StrategyForm from '../components/StrategyForm';
import AutoTradeMonitor from '../components/AutoTradeMonitor';
import RiskConfigForm from '../components/RiskConfigForm';
import { useTradeStore } from '../stores/tradeStore';

const { TabPane } = Tabs;

export default function AutoTrading() {
  const { userId, setUserId } = useTradeStore();

  useEffect(() => {
    if (!userId) {
      setUserId(1);
    }
  }, [userId, setUserId]);

  const [editingStrategy, setEditingStrategy] = useState<StrategyConfig | null>(null);
  const [showStrategyForm, setShowStrategyForm] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // 任务管理相关状态
  const [tasks, setTasks] = useState<AutoTradeTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskForm] = Form.useForm();

  const fetchTasks = async () => {
    if (!userId) return;
    setTasksLoading(true);
    try {
      const res = await autoTradingApi.getTasks(userId);
      setTasks(res.data);
    } catch (err: any) {
      message.error('获取任务列表失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTasksLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [userId]);

  const handleEditStrategy = (strategy: StrategyConfig) => {
    setEditingStrategy(strategy);
    setShowStrategyForm(true);
  };

  const handleCreateStrategy = () => {
    setEditingStrategy(null);
    setShowStrategyForm(true);
  };

  const handleStrategyFormSuccess = () => {
    setShowStrategyForm(false);
    setEditingStrategy(null);
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleStrategyFormCancel = () => {
    setShowStrategyForm(false);
    setEditingStrategy(null);
  };

  // 任务管理
  const handleCreateTask = async (values: any) => {
    if (!userId) return;
    try {
      const watchlist = values.watchlist
        ? values.watchlist.split(',').map((s: string) => s.trim()).filter(Boolean)
        : [];
      await autoTradingApi.createTask(userId, {
        execution_mode: values.execution_mode,
        interval_minutes: values.interval_minutes,
        watchlist,
      });
      message.success('任务创建成功');
      setShowTaskModal(false);
      taskForm.resetFields();
      fetchTasks();
    } catch (err: any) {
      message.error('创建任务失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStartTask = async (taskId: number) => {
    if (!userId) return;
    try {
      await autoTradingApi.startTask(taskId, userId);
      message.success('任务已启动');
      fetchTasks();
    } catch (err: any) {
      message.error('启动失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStopTask = async (taskId: number) => {
    if (!userId) return;
    try {
      await autoTradingApi.stopTask(taskId, userId);
      message.success('任务已停止');
      fetchTasks();
    } catch (err: any) {
      message.error('停止失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getExecutionModeLabel = (mode: string) => {
    const map: Record<string, { label: string; color: string }> = {
      POLLING: { label: '轮询模式', color: 'blue' },
      REALTIME: { label: '实时模式', color: 'green' },
      BATCH: { label: '批量模式', color: 'orange' },
    };
    const info = map[mode] || { label: mode, color: 'default' };
    return <Tag color={info.color}>{info.label}</Tag>;
  };

  const renderTaskPanel = () => (
    <Card
      title="自动交易任务"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowTaskModal(true)}>
          新建任务
        </Button>
      }
      loading={tasksLoading}
    >
      {tasks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          暂无自动交易任务，请点击"新建任务"创建
        </div>
      ) : (
        <div>
          {tasks.map((task) => (
            <Card
              key={task.id}
              size="small"
              style={{ marginBottom: 12 }}
              extra={
                <Space>
                  {task.enabled ? (
                    <Button
                      type="primary"
                      danger
                      icon={<PauseCircleOutlined />}
                      size="small"
                      onClick={() => handleStopTask(task.id)}
                    >
                      停止
                    </Button>
                  ) : (
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      size="small"
                      onClick={() => handleStartTask(task.id)}
                    >
                      启动
                    </Button>
                  )}
                </Space>
              }
            >
              <Row gutter={16}>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>任务ID</div>
                  <div>{task.id}</div>
                </Col>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>执行模式</div>
                  <div>{getExecutionModeLabel(task.execution_mode)}</div>
                </Col>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>轮询间隔</div>
                  <div>{task.interval_minutes ? `${task.interval_minutes} 分钟` : '-'}</div>
                </Col>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>状态</div>
                  <div>
                    <Tag color={task.enabled ? 'green' : 'default'}>
                      {task.enabled ? '运行中' : '已停止'}
                    </Tag>
                  </div>
                </Col>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>上次运行</div>
                  <div>{task.last_run_at ? new Date(task.last_run_at).toLocaleString('zh-CN') : '未运行'}</div>
                </Col>
                <Col span={4}>
                  <div style={{ color: '#999', fontSize: 12 }}>监控股票</div>
                  <div>
                    {task.watchlist.length > 0 ? (
                      task.watchlist.slice(0, 3).map((code) => (
                        <Tag key={code} style={{ marginBottom: 2 }}>{code}</Tag>
                      ))
                    ) : (
                      <span style={{ color: '#999' }}>无</span>
                    )}
                    {task.watchlist.length > 3 && <Tag>+{task.watchlist.length - 3}</Tag>}
                  </div>
                </Col>
              </Row>
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="新建自动交易任务"
        open={showTaskModal}
        onCancel={() => {
          setShowTaskModal(false);
          taskForm.resetFields();
        }}
        footer={null}
      >
        <Form form={taskForm} layout="vertical" onFinish={handleCreateTask}>
          <Form.Item
            name="execution_mode"
            label="执行模式"
            rules={[{ required: true, message: '请选择执行模式' }]}
          >
            <Select placeholder="请选择执行模式">
              <Select.Option value="POLLING">轮询模式 - 定时检查信号</Select.Option>
              <Select.Option value="REALTIME">实时模式 - 实时监控</Select.Option>
              <Select.Option value="BATCH">批量模式 - 批量处理</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.execution_mode !== cur.execution_mode}
          >
            {({ getFieldValue }) =>
              getFieldValue('execution_mode') === 'POLLING' ? (
                <Form.Item
                  name="interval_minutes"
                  label="轮询间隔 (分钟)"
                  rules={[{ required: true, message: '请输入轮询间隔' }]}
                >
                  <InputNumber min={1} max={1440} style={{ width: '100%' }} suffix="分钟" />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Form.Item
            name="watchlist"
            label="监控股票列表"
            extra="输入股票代码，多个用逗号分隔，如: 000001,600000,000858"
          >
            <Input.TextArea rows={3} placeholder="000001,600000,000858" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }}>
              创建任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );

  if (!userId) {
    return <Card>请先登录</Card>;
  }

  return (
    <div>
      <Tabs defaultActiveKey="monitor" size="large">
        <TabPane tab="交易监控" key="monitor">
          <AutoTradeMonitor userId={userId} />
        </TabPane>

        <TabPane tab="策略管理" key="strategies">
          {showStrategyForm ? (
            <StrategyForm
              userId={userId}
              editingStrategy={editingStrategy}
              onSuccess={handleStrategyFormSuccess}
              onCancel={handleStrategyFormCancel}
            />
          ) : (
            <StrategyList
              userId={userId}
              onEdit={handleEditStrategy}
              onCreate={handleCreateStrategy}
              refreshTrigger={refreshTrigger}
            />
          )}
        </TabPane>

        <TabPane tab="任务管理" key="tasks">
          {renderTaskPanel()}
        </TabPane>

        <TabPane tab="风控配置" key="risk">
          <RiskConfigForm userId={userId} />
        </TabPane>
      </Tabs>
    </div>
  );
}
