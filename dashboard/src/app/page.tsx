'use client';

import { useEffect, useState } from 'react';
import StatCard from '@/components/StatCard';
import ServiceStatus from '@/components/ServiceStatus';
import ContentTable from '@/components/ContentTable';
import {
  fetchHealth, fetchCampaigns, fetchContent, fetchAnalytics,
  HealthStatus, Campaign, ContentItem, AnalyticsOverview,
} from '@/lib/api';

export default function DashboardPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      const [h, c, ct, a] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchCampaigns('active', 10).catch(() => ({ campaigns: [], count: 0 })),
        fetchContent('', '', 10).catch(() => ({ content: [], count: 0 })),
        fetchAnalytics().catch(() => null),
      ]);
      setHealth(h);
      setCampaigns(c.campaigns);
      setContent(ct.content);
      setAnalytics(a);
      setConnected(!!h);
    } catch {
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-muted">Connecting to engine...</p>
        </div>
      </div>
    );
  }

  const activeCampaigns = campaigns.filter(c => c.status === 'active').length;
  const totalContent = analytics?.content
    ? Object.values(analytics.content).reduce((a, b) => a + b, 0)
    : 0;
  const totalReddit = analytics?.reddit
    ? Object.values(analytics.reddit).reduce((a, b) => a + b, 0)
    : 0;
  const totalAdSpend = analytics?.ads
    ? analytics.ads.reduce((sum, a) => sum + (a.spend || 0), 0)
    : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        {connected ? (
          <span className="px-3 py-1 bg-accent-green/20 text-accent-green text-xs rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
            Engine Connected
          </span>
        ) : (
          <span className="px-3 py-1 bg-accent-red/20 text-accent-red text-xs rounded-full">
            Engine Offline
          </span>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Active Campaigns"
          value={activeCampaigns}
          icon="🎯"
        />
        <StatCard
          label="Content Generated"
          value={totalContent}
          icon="📝"
        />
        <StatCard
          label="Reddit Engagements"
          value={totalReddit}
          icon="💬"
        />
        <StatCard
          label="Ad Spend"
          value={`$${totalAdSpend.toLocaleString()}`}
          icon="📢"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Service Status */}
        <ServiceStatus
          services={health?.services || {}}
          connected={connected}
        />

        {/* Active Campaigns */}
        <div className="lg:col-span-2 bg-bg-card rounded-xl p-4 border border-border-subtle">
          <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-3">
            Active Campaigns
          </h3>
          {campaigns.length === 0 ? (
            <p className="text-text-muted text-sm py-4 text-center">
              No active campaigns. Create one to get started.
            </p>
          ) : (
            <div className="space-y-2">
              {campaigns.slice(0, 5).map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between px-3 py-2 rounded-lg bg-bg-main"
                >
                  <div>
                    <p className="text-sm text-white">{c.name}</p>
                    <p className="text-xs text-text-muted">{c.product_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-mono text-white">
                      ${c.budget_daily}/day
                    </p>
                    <p className="text-xs text-text-muted">
                      {c.channels?.join(', ') || 'none'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Content */}
      <div className="mb-6">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-3">
          Recent Content
        </h3>
        <ContentTable items={content} />
      </div>
    </div>
  );
}
