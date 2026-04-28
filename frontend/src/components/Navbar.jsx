import { Link, useLocation } from 'react-router-dom'
import useAuth from '../context/useAuth'
import { LayoutDashboard, Upload, LogOut, Shield } from 'lucide-react'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload',    label: 'Upload',    icon: Upload },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const { pathname }     = useLocation()

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-slate border-r border-border
                      flex flex-col z-50">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-accent rounded-lg flex items-center justify-center">
            <Shield size={14} className="text-white" />
          </div>
          <span className="font-display text-lg text-snow">FAILSAFE</span>
        </div>
        <p className="text-xs text-muted mt-1 font-mono">Risk Detection System</p>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, label, icon }) => {
          const Icon   = icon
          const active = pathname === to
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                          transition-all duration-150 ${
                active
                  ? 'bg-accent/15 text-accent font-medium'
                  : 'text-ghost hover:text-snow hover:bg-white/5'
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* User + logout */}
      <div className="px-3 py-4 border-t border-border">
        <div className="px-3 py-2 mb-2">
          <p className="text-sm font-medium text-snow truncate">{user?.name}</p>
          <p className="text-xs text-muted truncate">{user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                     text-ghost hover:text-red-400 hover:bg-red-500/10
                     transition-all duration-150 w-full"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
