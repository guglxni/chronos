import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Activity, LayoutDashboard, Settings as SettingsIcon, Zap, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/LoadingSpinner';
import Tooltip from './components/Tooltip';
import { api } from './lib/api';

// Route-level code splitting: each page becomes its own chunk so the first
// paint doesn't pay the cost of loading React Flow (Lineage) and GSAP (Detail)
// when the user is still on the Dashboard.
const Dashboard = lazy(() => import('./pages/Dashboard'));
const IncidentDetail = lazy(() => import('./pages/IncidentDetail'));
const Settings = lazy(() => import('./pages/Settings'));

function NavBar() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/90 backdrop-blur border-b border-gray-800 h-14 flex items-center px-6">
      {/* Logo */}
      <NavLink to="/" className="flex items-center gap-2 mr-8 group">
        <div className="p-1.5 bg-ps-blue rounded-lg transition-all duration-200 group-hover:bg-ps-cyan group-hover:shadow-ps-ring group-hover:scale-110">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-white tracking-tight text-lg">CHRONOS</span>
        <span className="text-gray-500 text-xs ml-1 font-mono">v2.0</span>
      </NavLink>

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

      {/* Right-side indicators */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        {api.isDemoMode() && (
          <Tooltip
            content="This deployment is running against fixture data so the UI works without a live backend. Trigger and acknowledge actions mutate in-memory state only."
            placement="bottom"
          >
            <span className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-ps-blue/20 border border-ps-blue/40 text-ps-darklink">
              <Sparkles className="w-3 h-3" />
              Demo
            </span>
          </Tooltip>
        )}
        <div className="flex items-center gap-2">
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
          <ErrorBoundary>
            <Suspense fallback={<LoadingSpinner size="lg" />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/incidents/:id" element={<IncidentDetail />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  );
}
