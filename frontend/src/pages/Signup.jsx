import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/client'
import { Shield, AlertCircle, CheckCircle } from 'lucide-react'

export default function Signup() {
  const navigate              = useNavigate()
  const [form,    setForm]    = useState({ name: '', email: '', password: '', confirm: '' })
  const [error,   setError]   = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Client-side validation
    if (!form.name.trim()) {
      setError('Full name is required.'); return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.'); return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.'); return
    }

    setLoading(true)
    try {
      await register({
        name    : form.name.trim(),
        email   : form.email.trim(),
        password: form.password,
      })
      setSuccess(true)
      // Redirect to login after 2 seconds
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Registration failed. Please try again.'
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
             backgroundImage: 'linear-gradient(var(--color-accent) 1px, transparent 1px), linear-gradient(90deg, var(--color-accent) 1px, transparent 1px)',
             backgroundSize: '40px 40px'
           }} />

      <div className="w-full max-w-sm relative">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12
                          rounded-xl mb-4"
               style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)' }}>
            <Shield size={22} className="text-accent" />
          </div>
          <h1 className="font-display text-3xl text-snow">FAILSAFE</h1>
          <p className="text-sm text-muted mt-1">Create your faculty account</p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <h2 className="text-base font-medium text-snow mb-5">Sign up</h2>

          {/* Success state */}
          {success ? (
            <div className="flex flex-col items-center py-4 text-center gap-3">
              <CheckCircle size={32} className="text-emerald-400" />
              <p className="text-sm font-medium text-snow">Account created!</p>
              <p className="text-xs text-muted">Redirecting to login...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="flex items-center gap-2 text-red-400 text-sm
                                rounded-lg px-3 py-2 mb-4"
                     style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)' }}>
                  <AlertCircle size={14} className="shrink-0" />
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="label">Full Name</label>
                  <input
                    name="name"
                    type="text"
                    className="input"
                    placeholder="Your Name"
                    value={form.name}
                    onChange={handleChange}
                    required
                    autoFocus
                  />
                </div>

                <div>
                  <label className="label">Email</label>
                  <input
                    name="email"
                    type="email"
                    className="input"
                    placeholder="faculty@university.edu"
                    value={form.email}
                    onChange={handleChange}
                    required
                  />
                </div>

                <div>
                  <label className="label">Password</label>
                  <input
                    name="password"
                    type="password"
                    className="input"
                    placeholder="Min. 8 characters"
                    value={form.password}
                    onChange={handleChange}
                    required
                  />
                  {/* Password strength indicator */}
                  {form.password.length > 0 && (
                    <div className="mt-2 flex gap-1">
                      {[1, 2, 3, 4].map(i => (
                        <div
                          key={i}
                          className="h-1 flex-1 rounded-full transition-all duration-300"
                          style={{
                            background: form.password.length >= i * 3
                              ? i <= 1 ? '#EF4444'
                              : i <= 2 ? '#F59E0B'
                              : i <= 3 ? '#6366F1'
                              : '#10B981'
                              : 'var(--color-border)'
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <label className="label">Confirm Password</label>
                  <input
                    name="confirm"
                    type="password"
                    className="input"
                    placeholder="Re-enter password"
                    value={form.confirm}
                    onChange={handleChange}
                    required
                  />
                  {/* Match indicator */}
                  {form.confirm.length > 0 && (
                    <p className={`text-xs mt-1 ${
                      form.password === form.confirm ? 'text-emerald-400' : 'text-red-400'
                    }`}>
                      {form.password === form.confirm ? '✓ Passwords match' : '✗ Passwords do not match'}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full mt-2 flex items-center justify-center gap-2"
                >
                  {loading
                    ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Creating account...</>
                    : 'Create Account'
                  }
                </button>
              </form>
            </>
          )}
        </div>

        {/* Link to login */}
        <p className="text-center text-xs text-muted mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
