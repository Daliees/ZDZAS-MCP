import { Routes, Route, Link } from 'react-router-dom'
import ConversationsPage from './pages/ConversationsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import OrganizationsPage from './pages/OrganizationsPage'
import UsersPage from './pages/UsersPage'
import AuditPage from './pages/AuditPage'
import CompliancePage from './pages/CompliancePage'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <Link to="/" className="flex items-center px-3 py-2 text-gray-700 hover:text-gray-900">
                <span className="font-bold text-xl">ZAS Admin</span>
              </Link>
              <Link to="/conversations" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Conversations
              </Link>
              <Link to="/analytics" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Analytics
              </Link>
              <Link to="/organizations" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Organizations
              </Link>
              <Link to="/users" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Users
              </Link>
              <Link to="/audit" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Audit
              </Link>
              <Link to="/compliance" className="flex items-center px-3 py-2 text-gray-600 hover:text-gray-900">
                Compliance
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="/conversations" element={<ConversationsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/organizations" element={<OrganizationsPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/compliance" element={<CompliancePage />} />
        </Routes>
      </main>
    </div>
  )
}

function DashboardHome() {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">ZAS Admin Dashboard</h1>
      <p className="text-gray-600 mb-6">
        EU AI Act compliant monitoring and management for ZAS AI Agent.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Conversations</h3>
          <p className="text-blue-700">View and analyze AI conversations</p>
        </div>
        <div className="bg-green-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 mb-2">Analytics</h3>
          <p className="text-green-700">Token usage and cost tracking</p>
        </div>
        <div className="bg-purple-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-purple-900 mb-2">Compliance</h3>
          <p className="text-purple-700">EU AI Act transparency reports</p>
        </div>
      </div>
    </div>
  )
}

export default App
