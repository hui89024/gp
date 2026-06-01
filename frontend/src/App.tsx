import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Dashboard from './pages/Dashboard';
import Trade from './pages/Trade';
import Prediction from './pages/Prediction';
import Review from './pages/Review';

const { Header, Content } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <h1 style={{ color: 'white', margin: 0 }}>股票交易系统</h1>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trade" element={<Trade />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/review" element={<Review />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default App;
