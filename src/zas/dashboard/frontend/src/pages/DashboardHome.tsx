import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface AnalyticsSummary {
  total_conversations: number
  total_tokens: number
  total_cost_estimate: string
  average_latency_ms: number
  unique_users: number
  unique_organisations: number
}

interface DatabaseStatus {
  status: string
  database: string
  table_count: number
  tables: string[]
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

export default function DashboardHome() {
  const { data: summary } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsSummary>('/analytics/summary')
      return response.data
    },
  })

  const { data: dbStatus } = useQuery({
    queryKey: ['database-status'],
    queryFn: async () => {
      const response = await apiClient.get<DatabaseStatus>('/test/database')
      return response.data
    },
  })

  // Mock data for charts (in real app, fetch from API)
  const dailyActivityData = [
    { date: 'Jan 14', conversations: 12, tokens: 4500 },
    { date: 'Jan 15', conversations: 19, tokens: 6200 },
    { date: 'Jan 16', conversations: 23, tokens: 7800 },
    { date: 'Jan 17', conversations: 15, tokens: 5100 },
    { date: 'Jan 18', conversations: 28, tokens: 9200 },
    { date: 'Jan 19', conversations: 31, tokens: 10500 },
    { date: 'Jan 20', conversations: summary?.total_conversations || 0, tokens: summary?.total_tokens || 0 },
  ]

  const systemHealthData = [
    { name: 'Successful', value: 95 },
    { name: 'Errors', value: 3 },
    { name: 'Pending', value: 2 },
  ]

  const tableStats = dbStatus?.tables.map((table, idx) => ({
    name: table,
    count: Math.floor(Math.random() * 100) + 10, // In real app, get actual counts
  })) || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
        <h1 className="text-3xl font-bold text-white mb-2">🤖 ZAS Admin Dashboard</h1>
        <p className="text-gray-400">
          EU AI Act compliant monitoring and management for ZAS AI Agent
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg shadow-xl p-6 border border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-blue-200 text-sm font-medium mb-1">Total Conversations</div>
              <div className="text-4xl font-bold text-white">{summary?.total_conversations || 0}</div>
            </div>
            <div className="text-5xl">💬</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-lg shadow-xl p-6 border border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-green-200 text-sm font-medium mb-1">Total Tokens</div>
              <div className="text-4xl font-bold text-white">
                {summary?.total_tokens?.toLocaleString() || 0}
              </div>
            </div>
            <div className="text-5xl">🔢</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-lg shadow-xl p-6 border border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-purple-200 text-sm font-medium mb-1">Estimated Cost</div>
              <div className="text-4xl font-bold text-white">${summary?.total_cost_estimate || '0.00'}</div>
            </div>
            <div className="text-5xl">💰</div>
          </div>
        </div>
      </div>

      {/* More Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-gray-400 text-sm font-medium mb-2">Average Latency</div>
          <div className="text-3xl font-bold text-white">
            {summary?.average_latency_ms?.toFixed(0) || 0}ms
          </div>
          <div className="text-green-400 text-sm mt-2">⚡ Performance</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-gray-400 text-sm font-medium mb-2">Active Users</div>
          <div className="text-3xl font-bold text-white">{summary?.unique_users || 0}</div>
          <div className="text-blue-400 text-sm mt-2">👥 Unique users</div>
        </div>

        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <div className="text-gray-400 text-sm font-medium mb-2">Organizations</div>
          <div className="text-3xl font-bold text-white">{summary?.unique_organisations || 0}</div>
          <div className="text-purple-400 text-sm mt-2">🏢 Connected orgs</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Chart */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">📊 Daily Activity (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyActivityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Legend />
              <Line type="monotone" dataKey="conversations" stroke="#3B82F6" strokeWidth={2} name="Conversations" />
              <Line type="monotone" dataKey="tokens" stroke="#10B981" strokeWidth={2} name="Tokens (÷100)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* System Health */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">🏥 System Health</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={systemHealthData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {systemHealthData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Database Status & Table Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Database Connection Status */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">💾 Database Connection</h3>
          {dbStatus ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Status</span>
                <span className="px-3 py-1 bg-green-600 text-white rounded-full text-sm font-medium">
                  ✓ {dbStatus.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Database Type</span>
                <span className="text-white font-mono">{dbStatus.database}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Total Tables</span>
                <span className="text-white font-bold text-2xl">{dbStatus.table_count}</span>
              </div>
              <div className="mt-4">
                <div className="text-gray-400 text-sm mb-2">Tables:</div>
                <div className="grid grid-cols-2 gap-2">
                  {dbStatus.tables.map((table) => (
                    <div key={table} className="bg-gray-700 px-3 py-2 rounded text-sm text-gray-300 font-mono">
                      {table}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-gray-400">Loading database status...</div>
          )}
        </div>

        {/* Table Statistics */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">📈 Database Tables</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tableStats.slice(0, 8)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Bar dataKey="count" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg shadow-xl p-6 border border-blue-500 hover:border-blue-400 transition cursor-pointer">
          <h3 className="text-lg font-semibold text-blue-400 mb-2">💬 Conversations</h3>
          <p className="text-gray-400">View and analyze AI conversations with full transparency</p>
        </div>
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg shadow-xl p-6 border border-green-500 hover:border-green-400 transition cursor-pointer">
          <h3 className="text-lg font-semibold text-green-400 mb-2">📊 Analytics</h3>
          <p className="text-gray-400">Monitor token usage, costs, and performance metrics</p>
        </div>
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg shadow-xl p-6 border border-purple-500 hover:border-purple-400 transition cursor-pointer">
          <h3 className="text-lg font-semibold text-purple-400 mb-2">✓ Compliance</h3>
          <p className="text-gray-400">EU AI Act transparency and GDPR compliance reports</p>
        </div>
      </div>
    </div>
  )
}
