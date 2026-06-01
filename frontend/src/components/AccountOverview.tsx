import { Card, Statistic, Row, Col } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { AccountOverview as AccountOverviewType } from '../types';

interface Props {
  overview: AccountOverviewType | null;
  loading?: boolean;
}

export default function AccountOverviewComponent({ overview, loading }: Props) {
  if (!overview) {
    return <Card loading={loading}>加载中...</Card>;
  }

  return (
    <Card title="账户概览">
      <Row gutter={16}>
        <Col span={6}>
          <Statistic
            title="总资产"
            value={overview.total_assets}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="可用资金"
            value={overview.available_capital}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="持仓市值"
            value={overview.market_value}
            precision={2}
            prefix="¥"
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="总盈亏"
            value={overview.total_pnl}
            precision={2}
            prefix="¥"
            valueStyle={{ color: overview.total_pnl >= 0 ? '#3f8600' : '#cf1322' }}
            suffix={overview.total_pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
        </Col>
      </Row>
    </Card>
  );
}
