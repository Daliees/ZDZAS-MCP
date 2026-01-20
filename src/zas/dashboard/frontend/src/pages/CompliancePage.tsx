import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

interface DataRetentionPolicy {
  organisation_id: string
  conversation_logs_days: number
  token_usage_days: number
  audit_logs_days: number
  anonymize_after_days: number
}

export default function CompliancePage() {
  const [orgId, setOrgId] = useState('')

  const { data: policy, isLoading } = useQuery({
    queryKey: ['retention-policy', orgId],
    queryFn: async () => {
      if (!orgId) return null
      const response = await apiClient.get<DataRetentionPolicy>(`/compliance/retention-policy/${orgId}`)
      return response.data
    },
    enabled: !!orgId,
  })

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow px-6 py-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">EU AI Act Compliance</h2>
        <p className="text-gray-600">Data retention, transparency, and GDPR compliance</p>
      </div>

      {/* Data Retention Policies */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Retention Policy</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Organization ID
          </label>
          <input
            type="text"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
            placeholder="Enter organization ID"
            className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {isLoading && <div className="text-gray-600">Loading policy...</div>}
        
        {policy && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-blue-900 mb-1">Conversation Logs</div>
              <div className="text-2xl font-bold text-blue-700">{policy.conversation_logs_days} days</div>
              <div className="text-xs text-blue-600 mt-1">EU AI Act Article 12 minimum: 90 days</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-green-900 mb-1">Token Usage</div>
              <div className="text-2xl font-bold text-green-700">{policy.token_usage_days} days</div>
              <div className="text-xs text-green-600 mt-1">For billing and analytics</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-purple-900 mb-1">Audit Logs</div>
              <div className="text-2xl font-bold text-purple-700">{policy.audit_logs_days} days</div>
              <div className="text-xs text-purple-600 mt-1">Immutable compliance records</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-orange-900 mb-1">Anonymize After</div>
              <div className="text-2xl font-bold text-orange-700">{policy.anonymize_after_days} days</div>
              <div className="text-xs text-orange-600 mt-1">GDPR privacy protection</div>
            </div>
          </div>
        )}
      </div>

      {/* GDPR Right to Erasure */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">GDPR Article 17: Right to Erasure</h3>
        <p className="text-gray-600 mb-4">
          Users can request deletion of their personal data. This will remove conversation logs and anonymize audit trails.
        </p>
        <button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition">
          Process Erasure Request
        </button>
      </div>

      {/* Transparency Reports */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">EU AI Act Article 13: Transparency Reports</h3>
        <p className="text-gray-600 mb-4">
          Generate transparency reports showing AI system usage, performance, and flagged content.
        </p>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">
          Generate Report
        </button>
      </div>
    </div>
  )
}
