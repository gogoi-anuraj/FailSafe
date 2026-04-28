import { useContext } from 'react'
import AuthContext from './AuthContext'

// Hook only — satisfies Fast Refresh file rules.
export default function useAuth() {
  return useContext(AuthContext)
}
