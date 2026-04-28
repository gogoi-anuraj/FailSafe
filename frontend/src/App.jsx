import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AuthProvider  from './context/AuthProvider'
import useAuth       from './context/useAuth'
import Login         from './pages/Login'
import Signup        from './pages/Signup'
import Dashboard     from './pages/Dashboard'
import Upload        from './pages/Upload'
import StudentDetail from './pages/StudentDetail'

function PrivateRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login"              element={<Login />} />
      <Route path="/signup"             element={<Signup />} />
      <Route path="/dashboard"          element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/upload"             element={<PrivateRoute><Upload /></PrivateRoute>} />
      <Route path="/student/:studentId" element={<PrivateRoute><StudentDetail /></PrivateRoute>} />
      <Route path="*"                   element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
