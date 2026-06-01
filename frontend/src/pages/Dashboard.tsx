import { Card, Row, Col, Statistic } from 'antd';

function Dashboard() {
  return (
    <div>
      <h2>账户概览</h2>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title="总资产" value={0} precision={2} prefix="¥" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="可用资金" value={0} precision={2} prefix="¥" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="持仓市值" value={0} precision={2} prefix="¥" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="总盈亏" value={0} precision={2} prefix="¥" />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
