import { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, message, Space, Tag } from 'antd';
import { PlusOutlined, LoginOutlined, DeleteOutlined } from '@ant-design/icons';
import { brokerApi, BrokerAccount as BrokerAccountType } from '../services/brokerApi';

function BrokerAccountPage() {
  const [accounts, setAccounts] = useState<BrokerAccountType[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const res = await brokerApi.list();
      setAccounts(res.data);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAccounts(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await brokerApi.create(values);
      message.success('添加成功');
      setModalOpen(false);
      form.resetFields();
      loadAccounts();
    } catch {
      message.error('添加失败');
    }
  };

  const handleLogin = async (id: number) => {
    try {
      await brokerApi.login(id);
      message.success('登录成功');
      loadAccounts();
    } catch {
      message.error('登录失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await brokerApi.delete(id);
      message.success('已禁用');
      loadAccounts();
    } catch {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '券商类型', dataIndex: 'broker_type', key: 'broker_type' },
    { title: '资金账号', dataIndex: 'account', key: 'account' },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (active: boolean) => active ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>
    },
    {
      title: '最后登录', dataIndex: 'last_login_at', key: 'last_login_at',
      render: (t: string | null) => t ? new Date(t).toLocaleString() : '未登录'
    },
    {
      title: '操作', key: 'action',
      render: (_: any, record: BrokerAccountType) => (
        <Space>
          <Button icon={<LoginOutlined />} onClick={() => handleLogin(record.id)}>登录</Button>
          <Button icon={<DeleteOutlined />} danger onClick={() => handleDelete(record.id)}>禁用</Button>
        </Space>
      )
    },
  ];

  return (
    <Card title="券商账户管理" extra={<Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加账户</Button>}>
      <Table dataSource={accounts} columns={columns} rowKey="id" loading={loading} />
      <Modal title="添加券商账户" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="broker_type" label="券商类型" initialValue="eastmoney">
            <Select options={[{ value: 'eastmoney', label: '东方财富证券' }]} />
          </Form.Item>
          <Form.Item name="account" label="资金账号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default BrokerAccountPage;
