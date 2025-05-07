import { fetchAPI } from './api'

// Types for log data
export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

export type LogEntry = {
  id: number
  timestamp: string
  category: string | null
  source: string | null
  level: LogLevel
  message: string
  details: any | null
  entity_type: string | null
  entity_id: string | null
  user_id: number | null
  owner_id: number | null
  trace_id: string | null
  span_id: string | null
  parent_span_id: string | null
  created_at: string
}

export type LogCategory = {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type LogSource = {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type LogsResponse = {
  logs: LogEntry[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type LogStatistic = {
  time_period: string
  level: string
  count: number
}

export type LogsParams = {
  page?: number
  page_size?: number
  start_time?: string
  end_time?: string
  levels?: string[]
  categories?: string[]
  sources?: string[]
  entity_type?: string
  entity_id?: string
  user_id?: number
  trace_id?: string
  search?: string
}

// API endpoints for logs
export const logsAPI = {
  // Get logs with pagination and filtering
  getLogs: (params: LogsParams = {}): Promise<LogsResponse> =>
    fetchAPI<LogsResponse>(`/logs/`, {
      params: params as Record<string, string | number | boolean | string[]>,
    }),

  // Get log by ID
  getLog: (id: number): Promise<LogEntry> =>
    fetchAPI<LogEntry>(`/logs/${id}/`),

  // Get log categories
  getCategories: (): Promise<LogCategory[]> =>
    fetchAPI<LogCategory[]>(`/logs/categories/`),

  // Get log sources
  getSources: (): Promise<LogSource[]> =>
    fetchAPI<LogSource[]>(`/logs/sources/`),

  // Get log levels
  getLevels: (): Promise<{ id: number, name: string, severity: number, color: string }[]> =>
    fetchAPI<{ id: number, name: string, severity: number, color: string }[]>(`/logs/levels/`),

  // Get log statistics
  getStatistics: (days: number = 7, group_by: string = 'day'): Promise<LogStatistic[]> =>
    fetchAPI<LogStatistic[]>(`/logs/statistics/`, {
      params: { days, group_by },
    }),

  // Clean up logs (admin only)
  cleanupLogs: (dryRun: boolean = false): Promise<{
    dry_run: boolean,
    deleted_count?: number,
    would_delete_count?: number,
    counts_by_level?: Array<{ level: string, retention_days: number, count: number }>
  }> =>
    fetchAPI<any>(`/logs/cleanup/`, {
      method: 'POST',
      params: { dry_run: dryRun },
    }),

  // Create a new log entry
  createLog: (logData: {
    message: string
    level?: LogLevel
    category?: string
    source?: string
    details?: any
    entity_type?: string
    entity_id?: string
    user_id?: number
    owner_id?: number
    trace_id?: string
    span_id?: string
    parent_span_id?: string
    timestamp?: string
  }): Promise<LogEntry> =>
    fetchAPI<LogEntry>(`/logs/`, {
      method: 'POST',
      body: logData,
    }),
}
