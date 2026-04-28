import { createContext } from 'react'

// Isolated in its own file — no components, no hooks.
// This satisfies Fast Refresh which requires files to export
// only one type of thing.
const AuthContext = createContext(null)

export default AuthContext
