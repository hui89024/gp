import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  StockOutlined,
  LineChartOutlined,
  FileTextOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';
import AutoTrading from './pages/AutoTrading';

const { Header, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '首页' },
  { key: '/trade', icon: <StockOutlined />, label: '交易' },
  { key: '/prediction', icon: <LineChartOutlined />, label: '预测' },
  { key: '/review', icon: <FileTextOutlined />, label: '复盘' },
  { key: '/auto-trading', icon: <RobotOutlined />, label: '自动交易' },
];

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <h1 style={{ color: 'white', margin: 0, marginRight: 40 }}>股票交易系统</h1>
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
          <Route path="/trade" element={<Trade />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
          <Route path="/auto-trading" element={<AutoTrading />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
