import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface AnalyticsSummary {
  total_conversations: number
  total_tokens: number
  total_cost_estimate: string
  average_latency_ms: number
  unique_users: number
  unique_organisations: number
}

export default function AnalyticsPage() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsSummary>('/analytics/summary')
      return response.data
    },
  })

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading analytics...</div>
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg shadow-xl px-6 py-4 border border-gray-700">
        <h2 className="text-2xl font-bold text-white mb-1">Analytics Dashboard</h2>
        <p className="text-gray-400">Token usage and performance metrics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Total Conversations</div>
          <div className="text-3xl font-bold text-white">{summary?.total_conversations || 0}</div>
        </div>
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Total Tokens</div>
          <div className="text-3xl font-bold text-white">
            {summary?.total_tokens?.toLocaleString() || 0}
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Estimated Cost</div>
          <div className="text-3xl font-bold text-white">
            ${summary?.total_cost_estimate || '0.00'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Average Latency</div>
          <div className="text-3xl font-bold text-white">
            {summary?.average_latency_ms?.toFixed(0) || 0}ms
          </div>
        </div>
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Unique Users</div>
          <div className="text-3xl font-bold text-white">{summary?.unique_users || 0}</div>
        </div>
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-sm font-medium text-gray-400 mb-2">Organizations</div>
          <div className="text-3xl font-bold text-white">{summary?.unique_organisations || 0}</div>
        </div>
      </div>

      {/* Chart Placeholder */}
      <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Token Usage Over Time</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          Chart will display when token usage data is available
        </div>
      </div>
    </div>
  )
}
