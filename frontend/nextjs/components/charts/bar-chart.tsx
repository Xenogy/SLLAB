"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { TimeseriesDataPoint } from "@/lib/api"
import { format } from "date-fns"

// Default data for when no data is provided
const defaultData = [
  { name: "VM-01", value: 75 },
  { name: "VM-02", value: 45 },
  { name: "VM-03", value: 90 },
  { name: "VM-04", value: 60 },
  { name: "VM-05", value: 30 },
  { name: "VM-06", value: 85 },
]

interface BarChartComponentProps {
  data?: TimeseriesDataPoint[] | Array<{ name: string; value: number }>;
  loading?: boolean;
  xAxisDataKey?: string;
  yAxisDataKey?: string;
  color?: string;
  formatXAxis?: (value: any) => string;
  formatTooltip?: (value: any) => string;
}

export default function BarChartComponent({
  data,
  loading = false,
  xAxisDataKey = "name",
  yAxisDataKey = "value",
  color = "#8884d8",
  formatXAxis,
  formatTooltip,
}: BarChartComponentProps) {
  // Format data for the chart
  const chartData = data?.length
    ? data.map(point => {
        // If it's timeseries data with timestamp
        if ('timestamp' in point && typeof point.timestamp === 'string') {
          return {
            ...point,
            name: format(new Date(point.timestamp), "MMM dd HH:mm")
          };
        }
        return point;
      })
    : defaultData;

  // Custom formatter for X axis
  const xAxisFormatter = (value: any) => {
    if (formatXAxis) return formatXAxis(value);
    return value;
  };

  // Custom formatter for tooltip
  const tooltipFormatter = (value: any) => {
    if (formatTooltip) return formatTooltip(value);
    return value;
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={chartData}
        margin={{
          top: 5,
          right: 10,
          left: 10,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} vertical={false} />
        <XAxis
          dataKey={xAxisDataKey}
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={xAxisFormatter}
        />
        <YAxis fontSize={12} tickLine={false} axisLine={false} />
        <Tooltip formatter={tooltipFormatter} />
        <Bar
          dataKey={yAxisDataKey}
          fill={color}
          radius={[4, 4, 0, 0]}
          isAnimationActive={!loading}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
