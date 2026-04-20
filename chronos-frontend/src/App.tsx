import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { Activity, LayoutDashboard, Settings as SettingsIcon, Zap } from 'lucide-react';
import clsx from 'clsx';
import Dashboard from './pages/Dashboard';
import IncidentDetail from './pages/IncidentDetail';
import Settings from './pages/Settings';

function NavBar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900 border-b border-gray-800 h-14 flex items-center px-6">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-8">
        <div className="p-1.5 bg-sky-600 rounded-lg">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-white tracking-tight text-lg">CHRONOS</span>
        <span className="text-gray-500 text-xs ml-1 font-mono">v2.0</span>
      </div>

      {/* Nav links */}
      <div className="flex items-center gap-1 flex-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
              isActive
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            )
          }
        >
          <LayoutDashboard className="w-4 h-4" />
          Dashboard
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors',
              isActive
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            )
          }
        >
          <SettingsIcon className="w-4 h-4" />
          Settings
        </NavLink>
      </div>

      {/* Live indicator */}
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <Activity className="w-3.5 h-3.5" />
        <span
          className={clsx(
            'flex items-center gap-1.5',
            location.pathname === '/' ? 'text-emerald-400' : 'text-gray-500'
          )}
        >
          <span className="relative flex h-2 w-2">
            <span
              className={clsx(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                location.pathname === '/' ? 'bg-emerald-400' : 'bg-gray-500'
              )}
            />
            <span
              className={clsx(
                'relative inline-flex rounded-full h-2 w-2',
                location.pathname === '/' ? 'bg-emerald-500' : 'bg-gray-600'
              )}
            />
          </span>
          {location.pathname === '/' ? 'Live' : 'Idle'}
        </span>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <NavBar />
        <main className="pt-14">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/incidents/:id" element={<IncidentDetail />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
