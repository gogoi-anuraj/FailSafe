import { useState } from 'react'
import { Link } from 'react-router-dom'
import useAuth from '../context/useAuth'
import { Shield, AlertCircle } from 'lucide-react'

export default function Login() {
  const { login }               = useAuth()
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Login failed. Check your credentials.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-ink flex items-center justify-center p-4">
      {/* Background grid */}
      <div className="absolute inset-0 opacity-[0.03]"
           style={{
             backgroundImage: 'linear-gradient(#6366F1 1px, transparent 1px), linear-gradient(90deg, #6366F1 1px, transparent 1px)',
             backgroundSize: '40px 40px'
           }} />

      <div className="w-full max-w-sm relative">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12
                          bg-accent/10 border border-accent/30 rounded-xl mb-4">
            <Shield size={22} className="text-accent" />
          </div>
          <h1 className="font-display text-3xl text-snow">FAILSAFE</h1>
          <p className="text-sm text-muted mt-1">Student Risk Detection System</p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <h2 className="text-base font-medium text-snow mb-5">Sign in to continue</h2>

          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30
                            text-red-400 text-sm rounded-lg px-3 py-2 mb-4">
              <AlertCircle size={14} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                placeholder="faculty@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2 flex items-center justify-center gap-2"
            >
              {loading
                ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Signing in...</>
                : 'Sign in'
              }
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-muted mt-4">
          Don't have an account?{' '}
          <Link to="/signup" className="text-accent hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}
