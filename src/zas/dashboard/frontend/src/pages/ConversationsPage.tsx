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
    return <div className="text-center py-8 text-gray-400">Loading conversations...</div>
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-2xl font-bold text-white">Conversations</h2>
        <p className="text-gray-400 mt-1">EU AI Act Article 12 compliant conversation logs</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Timestamp
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                User ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Input
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Tokens
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Latency
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {conversations?.map((conv) => (
              <tr key={conv.id} className="hover:bg-gray-700 transition">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {format(new Date(conv.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400 font-mono">
                  {conv.user_id.substring(0, 12)}...
                </td>
                <td className="px-6 py-4 text-sm text-gray-300">
                  <div className="max-w-md truncate">{conv.input_prompt}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                  {conv.total_tokens || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
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
