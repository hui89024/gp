import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card } from 'antd';
import { stockApi } from '../services/api';
import type { KLineData } from '../types';

interface Props {
  stockCode: string;
  stockName?: string;
}

export default function StockChart({ stockCode, stockName }: Props) {
  const [klineData, setKlineData] = useState<KLineData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (stockCode) {
      fetchKlineData();
    }
  }, [stockCode]);

  const fetchKlineData = async () => {
    setLoading(true);
    try {
      const response = await stockApi.getKlineData(stockCode, 60);
      setKlineData(response.data);
    } catch (error) {
      console.error('获取K线数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getOption = () => {
    if (!klineData) return {};

    return {
      title: {
        text: stockName ? `${stockName} (${stockCode})` : stockCode,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['K线', '成交量'],
        bottom: 0,
      },
      grid: [
        { left: '10%', right: '8%', height: '50%' },
        { left: '10%', right: '8%', top: '70%', height: '20%' },
      ],
      xAxis: [
        {
          type: 'category',
          data: klineData.dates,
          gridIndex: 0,
        },
        {
          type: 'category',
          data: klineData.dates,
          gridIndex: 1,
        },
      ],
      yAxis: [
        {
          type: 'value',
          gridIndex: 0,
          scale: true,
        },
        {
          type: 'value',
          gridIndex: 1,
          scale: true,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: klineData.dates.map((_, i) => [
            klineData.opens[i],
            klineData.closes[i],
            klineData.lows[i],
            klineData.highs[i],
          ]),
          xAxisIndex: 0,
          yAxisIndex: 0,
        },
        {
          name: '成交量',
          type: 'bar',
          data: klineData.volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };
  };

  return (
    <Card title="K线图" loading={loading}>
      {klineData && (
        <ReactECharts option={getOption()} style={{ height: 400 }} />
      )}
    </Card>
  );
}
