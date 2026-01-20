import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { format } from 'date-fns'

interface Conversation {
  id: string
  organisation_id: string
  user_id: string
  timestamp: string
  input_prompt: string
  output_response: string
  total_tokens: number | null
  latency_ms: number | null
}

export default function ConversationsPage() {
  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await apiClient.get<Conversation[]>('/conversations/?limit=50')
      return response.data
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading conversations...</div>
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">Conversations</h2>
        <p className="text-gray-600 mt-1">EU AI Act Article 12 compliant conversation logs</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Input
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tokens
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Latency
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {conversations?.map((conv) => (
              <tr key={conv.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {format(new Date(conv.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                  {conv.user_id.substring(0, 12)}...
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  <div className="max-w-md truncate">{conv.input_prompt}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {conv.total_tokens || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {conv.latency_ms ? `${conv.latency_ms}ms` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {conversations?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No conversations found. Start chatting to see logs here.
        </div>
      )}
    </div>
  )
}
