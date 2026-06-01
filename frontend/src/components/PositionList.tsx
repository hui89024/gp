import { Table, Tag } from 'antd';
import type { Position } from '../types';

interface Props {
  positions: Position[];
  loading?: boolean;
  onSelect?: (position: Position) => void;
}

export default function PositionList({ positions, loading, onSelect }: Props) {
  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
    },
    {
      title: '持仓数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '成本价',
      dataIndex: 'avg_cost',
      key: 'avg_cost',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '现价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      render: (value: number) => (
        <Tag color={value >= 0 ? 'green' : 'red'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}
        </Tag>
      ),
    },
    {
      title: '市值',
      dataIndex: 'market_value',
      key: 'market_value',
      render: (value: number) => `¥${value.toFixed(2)}`,
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={positions}
      loading={loading}
      rowKey="id"
      onRow={(record) => ({
        onClick: () => onSelect?.(record),
      })}
      pagination={false}
    />
  );
}
