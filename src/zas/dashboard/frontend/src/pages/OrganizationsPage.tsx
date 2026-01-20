import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

interface Organisation {
  organisation_id: string
  organisation_name: string
  organisation_url: string | null
}

export default function OrganizationsPage() {
  const { data: organisations, isLoading } = useQuery({
    queryKey: ['organisations'],
    queryFn: async () => {
      const response = await apiClient.get<Organisation[]>('/organizations/')
      return response.data
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading organizations...</div>
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-xl border border-gray-700">
      <div className="px-6 py-4 border-b border-gray-700">
        <h2 className="text-2xl font-bold text-white">Organizations</h2>
        <p className="text-gray-400 mt-1">Manage Salesforce organizations using ZAS</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Organization ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                URL
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {organisations?.map((org) => (
              <tr key={org.organisation_id} className="hover:bg-gray-700 transition">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                  {org.organisation_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {org.organisation_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-400">
                  {org.organisation_url ? (
                    <a href={org.organisation_url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-300">
                      {org.organisation_url}
                    </a>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {organisations?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No organizations found.
        </div>
      )}
    </div>
  )
}
