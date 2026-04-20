import { useState, useEffect } from 'react';
import { Save, RotateCcw, Info } from 'lucide-react';

const STORAGE_KEY = 'chronos_settings';

interface ChronosSettings {
  apiUrl: string;
  slackWebhookUrl: string;
  investigationWindowHours: number;
  autoRefreshInterval: number;
  maxIncidentsDisplay: number;
}

const DEFAULTS: ChronosSettings = {
  apiUrl: 'http://localhost:8100',
  slackWebhookUrl: '',
  investigationWindowHours: 24,
  autoRefreshInterval: 30,
  maxIncidentsDisplay: 50,
};

function maskSecret(val: string): string {
  if (!val) return '';
  if (val.length <= 8) return '•'.repeat(val.length);
  return val.slice(0, 4) + '•'.repeat(Math.min(val.length - 8, 20)) + val.slice(-4);
}

function loadSettings(): ChronosSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...(JSON.parse(raw) as Partial<ChronosSettings>) };
  } catch {
    return { ...DEFAULTS };
  }
}

export default function Settings() {
  const [settings, setSettings] = useState<ChronosSettings>(loadSettings);
  const [saved, setSaved] = useState(false);
  const [showSlack, setShowSlack] = useState(false);

  useEffect(() => {
    if (saved) {
      const t = setTimeout(() => setSaved(false), 2000);
      return () => clearTimeout(t);
    }
  }, [saved]);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    setSaved(true);
  }

  function handleReset() {
    setSettings({ ...DEFAULTS });
    localStorage.removeItem(STORAGE_KEY);
  }

  function update<K extends keyof ChronosSettings>(key: K, value: ChronosSettings[K]) {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          Configuration stored in browser localStorage for demo purposes.
        </p>
      </div>

      <form onSubmit={(e) => void handleSave(e)} className="space-y-6">

        {/* API Section */}
        <section className="card space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            API Configuration
          </h2>

          <div>
            <label htmlFor="apiUrl" className="block text-sm text-gray-400 mb-1.5">
              Backend API URL
            </label>
            <input
              id="apiUrl"
              type="url"
              value={settings.apiUrl}
              onChange={(e) => update('apiUrl', e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-sky-500"
              placeholder="http://localhost:8100"
            />
            <p className="text-xs text-gray-600 mt-1">
              The CHRONOS backend server. Currently: <span className="font-mono text-gray-500">{settings.apiUrl}</span>
            </p>
          </div>

          <div>
            <label htmlFor="maxIncidents" className="block text-sm text-gray-400 mb-1.5">
              Max Incidents to Display
            </label>
            <input
              id="maxIncidents"
              type="number"
              min={10}
              max={500}
              value={settings.maxIncidentsDisplay}
              onChange={(e) => update('maxIncidentsDisplay', Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div>
            <label htmlFor="refreshInterval" className="block text-sm text-gray-400 mb-1.5">
              Auto-refresh Interval (seconds)
            </label>
            <input
              id="refreshInterval"
              type="number"
              min={5}
              max={300}
              value={settings.autoRefreshInterval}
              onChange={(e) => update('autoRefreshInterval', Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
        </section>

        {/* Investigation Section */}
        <section className="card space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            Investigation
          </h2>

          <div>
            <label htmlFor="windowHours" className="block text-sm text-gray-400 mb-1.5">
              Investigation Window (hours)
            </label>
            <input
              id="windowHours"
              type="number"
              min={1}
              max={168}
              value={settings.investigationWindowHours}
              onChange={(e) => update('investigationWindowHours', Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <p className="text-xs text-gray-600 mt-1">
              How far back CHRONOS looks when correlating changes (default: 24h).
            </p>
          </div>
        </section>

        {/* Notifications Section */}
        <section className="card space-y-4">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            Notifications
          </h2>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="slackUrl" className="text-sm text-gray-400">
                Slack Webhook URL
              </label>
              <button
                type="button"
                onClick={() => setShowSlack((v) => !v)}
                className="text-xs text-sky-500 hover:text-sky-400 transition-colors"
              >
                {showSlack ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              id="slackUrl"
              type={showSlack ? 'text' : 'password'}
              value={settings.slackWebhookUrl}
              onChange={(e) => update('slackWebhookUrl', e.target.value)}
              placeholder="https://hooks.slack.com/services/..."
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
            />
            {settings.slackWebhookUrl && !showSlack && (
              <p className="text-xs text-gray-600 font-mono mt-1">
                Masked: {maskSecret(settings.slackWebhookUrl)}
              </p>
            )}
          </div>

          <div className="flex items-start gap-2 p-3 bg-gray-900 rounded-lg border border-gray-800">
            <Info className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-gray-500">
              Slack notifications are configured server-side via environment variables. The
              webhook URL here is for display/reference only — changes require a server restart.
            </p>
          </div>
        </section>

        {/* Action buttons */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            className="btn-primary flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="btn-secondary flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset Defaults
          </button>
        </div>
      </form>
    </div>
  );
}
