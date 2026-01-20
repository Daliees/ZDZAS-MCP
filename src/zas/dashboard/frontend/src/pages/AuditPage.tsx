import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { format } from 'date-fns'

interface AuditLog {
  id: string
  timestamp: string
  user_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  success: boolean
  error_message: string | null
}

export default function AuditPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit'],
    queryFn: async () => {
      const response = await apiClient.get<AuditLog[]>('/audit/?limit=100')
      return response.data
    },
  })

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading audit logs...</div>
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-2xl font-bold text-white">Audit Logs</h2>
        <p className="text-gray-400 mt-1">Immutable system audit trail for compliance</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Action
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Resource
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {logs?.map((log) => (
              <tr key={log.id} className="hover:bg-gray-700 transition">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-300">
                  {log.action}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                  {log.resource_type}
                  {log.resource_id && `: ${log.resource_id.substring(0, 8)}...`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {log.success ? (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-900 text-green-200 border border-green-700">
                      Success
                    </span>
                  ) : (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-900 text-red-200 border border-red-700">
                      Failed
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {logs?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No audit logs found.
        </div>
      )}
    </div>
  )
}
