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
    return <div className="text-center py-8">Loading audit logs...</div>
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">Audit Logs</h2>
        <p className="text-gray-600 mt-1">Immutable system audit trail for compliance</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Resource
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs?.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {log.action}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {log.resource_type}
                  {log.resource_id && `: ${log.resource_id.substring(0, 8)}...`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {log.success ? (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Success
                    </span>
                  ) : (
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
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
