"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { TimeseriesDataPoint } from "@/lib/api"
import { format } from "date-fns"

// Default data for when no data is provided
const defaultData = [
  { name: "Jan", value: 400 },
  { name: "Feb", value: 300 },
  { name: "Mar", value: 600 },
  { name: "Apr", value: 800 },
  { name: "May", value: 500 },
  { name: "Jun", value: 900 },
  { name: "Jul", value: 1000 },
]

interface LineChartComponentProps {
  data?: TimeseriesDataPoint[];
  loading?: boolean;
  xAxisDataKey?: string;
  yAxisDataKey?: string;
  color?: string;
  formatXAxis?: (value: any) => string;
  formatTooltip?: (value: any) => string;
  showDots?: boolean;
}

export default function LineChartComponent({
  data,
  loading = false,
  xAxisDataKey = "timestamp",
  yAxisDataKey = "value",
  color = "#8884d8",
  formatXAxis,
  formatTooltip,
  showDots = true,
}: LineChartComponentProps) {
  // Format data for the chart
  const chartData = data?.length
    ? data.map(point => ({
        ...point,
        // Format timestamp for display if it's a timestamp
        name: xAxisDataKey === "timestamp" && typeof point.timestamp === "string"
          ? format(new Date(point.timestamp), "MMM dd HH:mm")
          : point[xAxisDataKey as keyof typeof point]
      }))
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
      <LineChart
        data={chartData}
        margin={{
          top: 5,
          right: 10,
          left: 10,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
        <XAxis
          dataKey="name"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          tickFormatter={xAxisFormatter}
        />
        <YAxis fontSize={12} tickLine={false} axisLine={false} />
        <Tooltip formatter={tooltipFormatter} />
        <Line
          type="monotone"
          dataKey={yAxisDataKey}
          stroke={color}
          strokeWidth={2}
          dot={showDots ? { r: 3 } : false}
          isAnimationActive={!loading}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
