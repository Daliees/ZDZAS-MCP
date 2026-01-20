import { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import ConversationsPage from './pages/ConversationsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import OrganizationsPage from './pages/OrganizationsPage'
import UsersPage from './pages/UsersPage'
import AuditPage from './pages/AuditPage'
import CompliancePage from './pages/CompliancePage'
import LoginPage from './pages/LoginPage'
import DashboardHome from './pages/DashboardHome'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is authenticated
    const auth = localStorage.getItem('auth')
    if (auth) {
      const { username: storedUsername } = JSON.parse(auth)
      setUsername(storedUsername)
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogin = (username: string) => {
    setUsername(username)
    setIsAuthenticated(true)
    navigate('/')
  }

  const handleLogout = () => {
    localStorage.removeItem('auth')
    setUsername('')
    setIsAuthenticated(false)
    navigate('/login')
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation */}
      <nav className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex space-x-8">
              <Link to="/" className="flex items-center px-3 py-2 text-gray-300 hover:text-white">
                <span className="font-bold text-xl">🤖 ZAS Admin</span>
              </Link>
              <Link to="/conversations" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Conversations
              </Link>
              <Link to="/analytics" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Analytics
              </Link>
              <Link to="/organizations" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Organizations
              </Link>
              <Link to="/users" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Users
              </Link>
              <Link to="/audit" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Audit
              </Link>
              <Link to="/compliance" className="flex items-center px-3 py-2 text-gray-400 hover:text-white">
                Compliance
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-400 text-sm">👤 {username}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                Logout
              </button>
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

export default App
