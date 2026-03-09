'use client';

import { useEffect, useState } from 'react';
import { fetchHealth, HealthStatus } from '@/lib/api';

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [engineUrl, setEngineUrl] = useState(
    process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8300'
  );

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {/* Connection */}
      <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
        <h2 className="text-lg font-bold text-white mb-4">Engine Connection</h2>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-text-muted">Engine URL</label>
            <input
              type="text"
              value={engineUrl}
              onChange={(e) => setEngineUrl(e.target.value)}
              className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white font-mono focus:border-accent-blue focus:outline-none"
            />
            <p className="text-xs text-text-muted mt-1">
              Set via NEXT_PUBLIC_ENGINE_URL environment variable
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${health ? 'bg-accent-green' : 'bg-accent-red'}`} />
            <span className="text-sm text-white">{health ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </div>

      {/* Services */}
      <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
        <h2 className="text-lg font-bold text-white mb-4">Service Status</h2>
        <div className="grid grid-cols-2 gap-3">
          {health?.services ? (
            Object.entries(health.services).map(([name, active]) => (
              <div
                key={name}
                className="flex items-center gap-3 px-4 py-3 bg-bg-main rounded-lg"
              >
                <div className={`w-3 h-3 rounded-full ${active ? 'bg-accent-green' : 'bg-accent-red'}`} />
                <div>
                  <p className="text-sm text-white capitalize">{name.replace('_', ' ')}</p>
                  <p className="text-xs text-text-muted">
                    {active ? 'API key configured' : 'Not configured'}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-text-muted col-span-2 py-4 text-center">
              Connect to engine to see service status
            </p>
          )}
        </div>
      </div>

      {/* API Documentation */}
      <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
        <h2 className="text-lg font-bold text-white mb-4">API Endpoints</h2>
        <div className="space-y-2 font-mono text-sm">
          {[
            { method: 'GET', path: '/api/health', desc: 'Service health status' },
            { method: 'GET', path: '/api/campaigns', desc: 'List campaigns' },
            { method: 'POST', path: '/api/campaigns', desc: 'Create campaign' },
            { method: 'POST', path: '/api/content/generate', desc: 'Generate AI content' },
            { method: 'GET', path: '/api/content', desc: 'List content items' },
            { method: 'POST', path: '/api/video/generate', desc: 'Generate faceless video' },
            { method: 'POST', path: '/api/reddit/discover', desc: 'Discover Reddit posts' },
            { method: 'POST', path: '/api/reddit/engage', desc: 'Generate Reddit comments' },
            { method: 'POST', path: '/api/ads/create', desc: 'Create ad campaign' },
            { method: 'GET', path: '/api/ads', desc: 'List ad campaigns' },
            { method: 'POST', path: '/api/landing-pages/generate', desc: 'Generate landing page' },
            { method: 'GET', path: '/api/landing-pages', desc: 'List landing pages' },
            { method: 'GET', path: '/api/analytics/overview', desc: 'Analytics overview' },
            { method: 'GET', path: '/api/analytics/daily', desc: 'Daily performance' },
            { method: 'GET', path: '/api/calendar', desc: 'Content calendar' },
          ].map((ep) => (
            <div
              key={ep.path}
              className="flex items-center gap-3 px-3 py-2 bg-bg-main rounded-lg"
            >
              <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                ep.method === 'GET' ? 'bg-accent-green/20 text-accent-green' :
                'bg-accent-blue/20 text-accent-blue'
              }`}>
                {ep.method}
              </span>
              <span className="text-white flex-1">{ep.path}</span>
              <span className="text-text-muted text-xs">{ep.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Environment Variables */}
      <div className="bg-bg-card rounded-xl p-6 border border-border-subtle">
        <h2 className="text-lg font-bold text-white mb-4">Required Environment Variables</h2>
        <p className="text-sm text-text-muted mb-3">
          Configure these in your .env file or hosting provider:
        </p>
        <div className="space-y-1 font-mono text-xs">
          {[
            { key: 'LITELLM_URL', desc: 'LiteLLM API proxy URL' },
            { key: 'PEXELS_API_KEY', desc: 'Pexels stock footage API (free)' },
            { key: 'HEYGEN_API_KEY', desc: 'HeyGen AI avatar videos ($5-29/mo)' },
            { key: 'REDDIT_CLIENT_ID', desc: 'Reddit OAuth app (free)' },
            { key: 'META_ACCESS_TOKEN', desc: 'Meta Ads access token' },
            { key: 'META_AD_ACCOUNT_ID', desc: 'Meta ad account ID' },
            { key: 'GOOGLE_ADS_DEVELOPER_TOKEN', desc: 'Google Ads API token' },
            { key: 'TIKTOK_ACCESS_TOKEN', desc: 'TikTok Marketing API token' },
            { key: 'YOUTUBE_API_KEY', desc: 'YouTube Data API key (free)' },
          ].map((v) => (
            <div
              key={v.key}
              className="flex items-center gap-3 px-3 py-2 bg-bg-main rounded-lg"
            >
              <span className="text-accent-yellow">{v.key}</span>
              <span className="text-text-muted">— {v.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
