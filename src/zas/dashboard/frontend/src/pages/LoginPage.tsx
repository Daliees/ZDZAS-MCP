import { useState } from 'react'
import apiClient from '../api/client'

interface LoginPageProps {
  onLogin: (username: string) => void
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Create Basic Auth header
      const credentials = btoa(`${username}:${password}`)
      const response = await apiClient.post('/auth/login', {}, {
        headers: {
          'Authorization': `Basic ${credentials}`
        }
      })

      // Store auth in localStorage
      localStorage.setItem('auth', JSON.stringify({
        username: response.data.username,
        token: response.data.access_token
      }))

      // Set default auth header for future requests
      apiClient.defaults.auth = { username, password }

      onLogin(response.data.username)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-white mb-2">🤖 ZAS Admin</h2>
          <p className="text-gray-400">Admin Dashboard Login</p>
        </div>

        <div className="bg-gray-800 shadow-xl rounded-lg p-8 border border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter password"
              />
            </div>

            {error && (
              <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-400">
            <p className="mb-1">Default credentials:</p>
            <p className="font-mono text-xs">admin / admin</p>
            <p className="font-mono text-xs">ryan / ryan123</p>
          </div>
        </div>

        <div className="text-center text-xs text-gray-500">
          EU AI Act compliant monitoring system
        </div>
      </div>
    </div>
  )
}
