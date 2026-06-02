import { useState } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Switch, Tag, Space, Modal } from 'antd';
import {
  DashboardOutlined,
  StockOutlined,
  LineChartOutlined,
  FileTextOutlined,
  RobotOutlined,
  BankOutlined,
  FundOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';
import AutoTrading from './pages/AutoTrading';
import BrokerAccountPage from './pages/BrokerAccount';
import LiveTradePage from './pages/LiveTrade';
import FundamentalPage from './pages/Fundamental';

const { Header, Content } = Layout;

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLive, setIsLive] = useState(false);

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '首页' },
    { key: '/trade', icon: <StockOutlined />, label: isLive ? '实盘交易' : '模拟交易' },
    { key: '/prediction', icon: <LineChartOutlined />, label: '预测' },
    { key: '/review', icon: <FileTextOutlined />, label: '复盘' },
    { key: '/auto-trading', icon: <RobotOutlined />, label: '自动交易' },
    { key: '/fundamental', icon: <FundOutlined />, label: '基本面' },
    { key: '/broker', icon: <BankOutlined />, label: '券商账户' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <h1 style={{ color: 'white', margin: 0, marginRight: 20 }}>股票交易系统</h1>
        <Space style={{ marginRight: 20 }}>
          <Tag color={isLive ? 'red' : 'blue'}>{isLive ? '实盘模式' : '模拟模式'}</Tag>
          <Switch
            checked={isLive}
            onChange={(checked) => {
              if (checked) {
                Modal.confirm({
                  title: '切换到实盘模式',
                  content: '实盘交易涉及真实资金，请确认已配置券商账户并了解风险。',
                  onOk: () => setIsLive(true),
                });
              } else {
                setIsLive(false);
              }
            }}
            checkedChildren="实盘"
            unCheckedChildren="模拟"
          />
        </Space>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1 }}
        />
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trade" element={isLive ? <LiveTradePage /> : <Trade />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
          <Route path="/auto-trading" element={<AutoTrading />} />
          <Route path="/fundamental" element={<FundamentalPage />} />
          <Route path="/broker" element={<BrokerAccountPage />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
