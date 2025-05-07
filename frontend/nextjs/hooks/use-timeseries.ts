"use client"

import { useState, useEffect, useCallback } from 'react'
import {
  timeseriesAPI,
  TimeseriesParams,
  TimeseriesResponse,
  TimeseriesDataPoint,
  TimeseriesStatisticsResponse,
  TimeseriesSystemOverviewResponse
} from '@/lib/api'

export type TimeseriesState = {
  data: TimeseriesDataPoint[];
  loading: boolean;
  error: string | null;
  startTime: string | null;
  endTime: string | null;
  period: string | null;
}

export type TimeseriesStatisticsState = {
  statistics: {
    min: number | null;
    max: number | null;
    avg: number | null;
    sum: number | null;
    count: number;
  };
  loading: boolean;
  error: string | null;
}

export type SystemOverviewState = {
  cpuUsage: TimeseriesDataPoint[];
  memoryUsage: TimeseriesDataPoint[];
  diskUsage: TimeseriesDataPoint[];
  vmCount: TimeseriesDataPoint[];
  accountCount: TimeseriesDataPoint[];
  loading: boolean;
  error: string | null;
  period: string | null;
  startTime: string | null;
  endTime: string | null;
}

// Hook for fetching timeseries data for a specific metric
export function useTimeseriesData(metricName: string, initialParams: TimeseriesParams = {}) {
  const [state, setState] = useState<TimeseriesState>({
    data: [],
    loading: true,
    error: null,
    startTime: null,
    endTime: null,
    period: null
  })
  const [params, setParams] = useState<TimeseriesParams>(initialParams)

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const response = await timeseriesAPI.getMetricData(metricName, params)

      setState({
        data: response.data,
        loading: false,
        error: null,
        startTime: response.start_time,
        endTime: response.end_time,
        period: response.period
      })
    } catch (err) {
      console.error(`Error fetching timeseries data for ${metricName}:`, err)
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load timeseries data',
        data: [] // Reset data on error
      }))
    }
  }, [metricName, params])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const updateParams = (newParams: Partial<TimeseriesParams>) => {
    setParams(prev => ({ ...prev, ...newParams }))
  }

  const refresh = () => {
    fetchData()
  }

  return {
    ...state,
    refresh,
    updateParams
  }
}

// Hook for fetching timeseries statistics for a specific metric
export function useTimeseriesStatistics(metricName: string, initialParams: TimeseriesParams = {}) {
  const [state, setState] = useState<TimeseriesStatisticsState>({
    statistics: {
      min: null,
      max: null,
      avg: null,
      sum: null,
      count: 0
    },
    loading: true,
    error: null
  })
  const [params, setParams] = useState<TimeseriesParams>(initialParams)

  const fetchStatistics = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const response = await timeseriesAPI.getMetricStatistics(metricName, params)

      setState({
        statistics: response.statistics,
        loading: false,
        error: null
      })
    } catch (err) {
      console.error(`Error fetching timeseries statistics for ${metricName}:`, err)
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load timeseries statistics',
        statistics: {
          min: null,
          max: null,
          avg: null,
          sum: null,
          count: 0
        }
      }))
    }
  }, [metricName, params])

  useEffect(() => {
    fetchStatistics()
  }, [fetchStatistics])

  const updateParams = (newParams: Partial<TimeseriesParams>) => {
    setParams(prev => ({ ...prev, ...newParams }))
  }

  const refresh = () => {
    fetchStatistics()
  }

  return {
    ...state,
    refresh,
    updateParams
  }
}

// Hook for fetching latest metric value
export function useLatestMetricValue(metricName: string, entityType?: string, entityId?: string) {
  const [value, setValue] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLatestValue = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await timeseriesAPI.getLatestMetricValue(metricName, entityType, entityId)
      setValue(response.value)
      setLoading(false)
    } catch (err) {
      console.error(`Error fetching latest value for ${metricName}:`, err)
      setError(err instanceof Error ? err.message : 'Failed to load latest metric value')
      setLoading(false)
    }
  }, [metricName, entityType, entityId])

  useEffect(() => {
    fetchLatestValue()
  }, [fetchLatestValue])

  const refresh = () => {
    fetchLatestValue()
  }

  return { value, loading, error, refresh }
}

// Hook for fetching system overview metrics
export function useSystemOverview(period: string = 'hourly', duration: string = 'day') {
  const [state, setState] = useState<SystemOverviewState>({
    cpuUsage: [],
    memoryUsage: [],
    diskUsage: [],
    vmCount: [],
    accountCount: [],
    loading: true,
    error: null,
    period: null,
    startTime: null,
    endTime: null
  })

  const fetchOverview = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    console.log(`Fetching system overview with period=${period}, duration=${duration}`)

    try {
      console.log('Calling timeseriesAPI.getSystemOverview...')
      const response = await timeseriesAPI.getSystemOverview(period, duration)
      console.log('System overview response:', response)

      setState({
        cpuUsage: response.cpu_usage,
        memoryUsage: response.memory_usage,
        diskUsage: response.disk_usage,
        vmCount: response.vm_count,
        accountCount: response.account_count,
        loading: false,
        error: null,
        period: response.period,
        startTime: response.start_time,
        endTime: response.end_time
      })
    } catch (err) {
      console.error('Error fetching system overview:', err)
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load system overview',
        cpuUsage: [],
        memoryUsage: [],
        diskUsage: [],
        vmCount: [],
        accountCount: []
      }))
    }
  }, [period, duration])

  useEffect(() => {
    fetchOverview()
  }, [fetchOverview])

  const refresh = () => {
    fetchOverview()
  }

  return {
    ...state,
    refresh
  }
}

// Hook for fetching VM metrics
export function useVMMetrics(vmId: number, metricName: string, initialParams: TimeseriesParams = {}) {
  const [state, setState] = useState<TimeseriesState>({
    data: [],
    loading: true,
    error: null,
    startTime: null,
    endTime: null,
    period: null
  })
  const [params, setParams] = useState<TimeseriesParams>(initialParams)

  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const response = await timeseriesAPI.getVMMetrics(vmId, metricName, params)

      setState({
        data: response.data,
        loading: false,
        error: null,
        startTime: response.start_time,
        endTime: response.end_time,
        period: response.period
      })
    } catch (err) {
      console.error(`Error fetching VM metrics for ${metricName}:`, err)
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load VM metrics'
      }))
    }
  }, [vmId, metricName, params])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const updateParams = (newParams: Partial<TimeseriesParams>) => {
    setParams(prev => ({ ...prev, ...newParams }))
  }

  const refresh = () => {
    fetchData()
  }

  return {
    ...state,
    refresh,
    updateParams
  }
}
