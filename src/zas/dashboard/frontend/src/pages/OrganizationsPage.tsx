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
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">Organizations</h2>
        <p className="text-gray-600 mt-1">Manage Salesforce organizations using ZAS</p>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Organization ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                URL
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {organisations?.map((org) => (
              <tr key={org.organisation_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                  {org.organisation_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {org.organisation_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                  {org.organisation_url ? (
                    <a href={org.organisation_url} target="_blank" rel="noopener noreferrer">
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
