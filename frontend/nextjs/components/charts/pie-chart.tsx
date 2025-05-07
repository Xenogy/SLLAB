"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"

// Default data for when no data is provided
const defaultData = [
  { name: "Running", value: 8 },
  { name: "Stopped", value: 3 },
  { name: "Error", value: 1 },
]

// Default colors
const DEFAULT_COLORS = ["#4ade80", "#94a3b8", "#f87171"]

interface PieChartComponentProps {
  data?: Array<{ name: string; value: number }>;
  loading?: boolean;
  colors?: string[];
  nameKey?: string;
  valueKey?: string;
  formatTooltip?: (value: any, name: string) => string | string[];
}

export default function PieChartComponent({
  data,
  loading = false,
  colors = DEFAULT_COLORS,
  nameKey = "name",
  valueKey = "value",
  formatTooltip,
}: PieChartComponentProps) {
  const chartData = data?.length ? data : defaultData;

  // Custom formatter for tooltip
  const tooltipFormatter = (value: any, name: string) => {
    if (formatTooltip) return formatTooltip(value, name);
    return [value, name];
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={80}
          fill="#8884d8"
          dataKey={valueKey}
          nameKey={nameKey}
          isAnimationActive={!loading}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip formatter={tooltipFormatter} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
