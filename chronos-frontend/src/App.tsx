import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { lazy, Suspense, useState, useEffect } from 'react';
import { Activity, LayoutDashboard, Settings as SettingsIcon, Zap, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/LoadingSpinner';
import Tooltip from './components/Tooltip';
import { api } from './lib/api';

// Route-level code splitting
const Demo = lazy(() => import('./pages/Demo'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const IncidentDetail = lazy(() => import('./pages/IncidentDetail'));
const IncidentReport = lazy(() => import('./pages/IncidentReport'));
const Settings = lazy(() => import('./pages/Settings'));

// Nav for the demo / landing page
function DemoNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 h-16 flex items-center px-6 md:px-12 transition-all duration-300"
      style={{
        backgroundColor: scrolled ? 'rgba(17,17,17,0.96)' : 'transparent',
        backdropFilter: scrolled ? 'blur(12px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(255,255,255,0.08)' : 'none',
      }}
    >
      {/* Wordmark */}
      <a
        href="/"
        className="font-heading text-white mr-auto"
        style={{ fontSize: '22px', textDecoration: 'none' }}
      >
        CHRONOS
      </a>

      {/* Nav links */}
      <div className="hidden md:flex items-center gap-8 mr-8">
        <a
          href="#how-it-works"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          How It Works
        </a>
        <a
          href="#live-demo"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          Live Demo
        </a>
        <a
          href="#architecture"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          Architecture
        </a>
        <a
          href="#for-agents"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          For Agents
        </a>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          View on GitHub
        </a>
        <a
          href="https://chronos-api-0e8635fe890d.herokuapp.com/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="font-body text-sm transition-colors hover:text-white"
          style={{ color: '#707072', textDecoration: 'none' }}
        >
          API Docs
        </a>
      </div>

      <a
        href="#live-demo"
        className="chronos-btn-black text-sm px-5 py-2.5"
        style={{ fontSize: '13px' }}
      >
        Try Demo →
      </a>
    </nav>
  );
}

// Nav for the internal dashboard
function DashboardNav() {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/90 backdrop-blur border-b border-gray-800 h-14 flex items-center px-6">
      {/* Logo */}
      <NavLink to="/app" className="flex items-center gap-2 mr-8 group">
        <div className="p-1.5 bg-ps-blue rounded-lg transition-all duration-200 group-hover:bg-ps-cyan group-hover:shadow-ps-ring group-hover:scale-110">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-white tracking-tight text-lg">CHRONOS</span>
        <span className="text-gray-500 text-xs ml-1 font-mono">v2.0</span>
      </NavLink>

      {/* Nav links */}
      <div className="flex items-center gap-1 flex-1">
        <NavLink
          to="/app"
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
          to="/app/settings"
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
              location.pathname === '/app' ? 'text-emerald-400' : 'text-gray-500'
            )}
          >
            <span className="relative flex h-2 w-2">
              <span
                className={clsx(
                  'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                  location.pathname === '/app' ? 'bg-emerald-400' : 'bg-gray-500'
                )}
              />
              <span
                className={clsx(
                  'relative inline-flex rounded-full h-2 w-2',
                  location.pathname === '/app' ? 'bg-emerald-500' : 'bg-gray-600'
                )}
              />
            </span>
            {location.pathname === '/app' ? 'Live' : 'Idle'}
          </span>
        </div>
      </div>
    </nav>
  );
}

function AppRoutes() {
  const location = useLocation();
  const isDashboard = location.pathname.startsWith('/app');

  return (
    <>
      {isDashboard ? (
        <div className="min-h-screen bg-gray-900 text-gray-100">
          <DashboardNav />
          <main className="pt-14">
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner size="lg" />}>
                <Routes>
                  <Route path="/app" element={<Dashboard />} />
                  <Route path="/app/incidents/:id" element={<IncidentDetail />} />
                  <Route path="/app/settings" element={<Settings />} />
                </Routes>
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>
      ) : (
        <div>
          <DemoNav />
          <ErrorBoundary>
            <Suspense fallback={<LoadingSpinner size="lg" />}>
              <Routes>
                <Route path="/" element={<Demo />} />
                <Route path="/report/:incidentId" element={<IncidentReport />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </div>
      )}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
