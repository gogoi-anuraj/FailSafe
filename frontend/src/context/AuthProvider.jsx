import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login as apiLogin } from '../api/client'
import AuthContext from './AuthContext'

function getStoredUser() {
  try {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  } catch {
    localStorage.clear()
    return null
  }
}

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser)
  const navigate        = useNavigate()

  const login = async (email, password) => {
    const res  = await apiLogin({ email, password })
    const data = res.data
    const u    = { name: data.user_name, email: data.user_email }
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user',  JSON.stringify(u))
    setUser(u)
    navigate('/dashboard')
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
