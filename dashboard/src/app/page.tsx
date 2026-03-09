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
          <div className="w-10 h-10 border-2 border-accent-purple border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-zinc-500 text-sm">Connecting to engine...</p>
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
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-1">Real-time overview of your marketing operations</p>
        </div>
        {connected ? (
          <div className="flex items-center gap-3">
            <span className="glass px-4 py-2 rounded-xl text-xs text-zinc-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-accent-green live-pulse" />
              Engine Connected
            </span>
          </div>
        ) : (
          <span className="glass px-4 py-2 rounded-xl text-xs text-accent-red flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-red" />
            Engine Offline
          </span>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Campaigns"
          value={activeCampaigns}
          icon="🎯"
          gradient="purple"
          subtext="+2 this week"
          trend="up"
        />
        <StatCard
          label="Content Generated"
          value={totalContent}
          icon="✨"
          gradient="teal"
          subtext="Across all platforms"
        />
        <StatCard
          label="Reddit Engagements"
          value={totalReddit}
          icon="💬"
          gradient="orange"
          subtext="Comments posted"
        />
        <StatCard
          label="Ad Spend"
          value={`$${totalAdSpend.toLocaleString()}`}
          icon="📡"
          gradient="pink"
          subtext="Total across platforms"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Service Status */}
        <div className="lg:col-span-1">
          <ServiceStatus
            services={health?.services || {}}
            connected={connected}
          />
        </div>

        {/* Active Campaigns */}
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
              Active Campaigns
            </h3>
            <span className="text-xs text-zinc-600">{campaigns.length} total</span>
          </div>
          {campaigns.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-12 h-12 rounded-2xl bg-accent-purple/10 flex items-center justify-center mb-3">
                <span className="text-xl">🎯</span>
              </div>
              <p className="text-white font-medium">No active campaigns</p>
              <p className="text-sm text-zinc-500 mt-1">Create your first campaign to get started</p>
            </div>
          ) : (
            <div className="space-y-2">
              {campaigns.slice(0, 5).map((c, i) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors group animate-slide-up"
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-purple/20 to-accent-teal/10 flex items-center justify-center text-xs font-bold text-accent-purple">
                      {(c.name || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm text-white font-medium group-hover:text-accent-purple transition-colors">{c.name}</p>
                      <p className="text-xs text-zinc-500">{c.product_name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-mono text-white">
                      ${c.budget_daily}<span className="text-zinc-600 text-xs">/day</span>
                    </p>
                    <p className="text-xs text-zinc-500">
                      {c.channels?.join(', ') || 'No channels'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Content */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">
            Recent Content
          </h3>
          <span className="text-xs text-zinc-600">{content.length} items</span>
        </div>
        <ContentTable items={content} />
      </div>
    </div>
  );
}
