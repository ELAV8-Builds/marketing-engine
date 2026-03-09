'use client';

import { useEffect, useState } from 'react';
import StatCard from '@/components/StatCard';
import { fetchAnalytics, fetchDailyPerformance, AnalyticsOverview, DailyPerformance } from '@/lib/api';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [daily, setDaily] = useState<DailyPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  async function loadData() {
    try {
      const [a, d] = await Promise.all([
        fetchAnalytics().catch(() => null),
        fetchDailyPerformance('', days).catch(() => ({ performance: [] })),
      ]);
      setAnalytics(a);
      setDaily(d.performance);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const contentTotal = analytics?.content
    ? Object.values(analytics.content).reduce((a, b) => a + b, 0) : 0;
  const redditTotal = analytics?.reddit
    ? Object.values(analytics.reddit).reduce((a, b) => a + b, 0) : 0;
  const adImpressions = analytics?.ads
    ? analytics.ads.reduce((s, a) => s + (a.impressions || 0), 0) : 0;
  const adSpend = analytics?.ads
    ? analytics.ads.reduce((s, a) => s + (a.spend || 0), 0) : 0;
  const adClicks = analytics?.ads
    ? analytics.ads.reduce((s, a) => s + (a.clicks || 0), 0) : 0;
  const lpVisits = analytics?.landing_pages?.visits || 0;
  const lpConversions = analytics?.landing_pages?.conversions || 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-1.5 bg-bg-card border border-border-subtle rounded-lg text-sm text-white"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Content Generated" value={contentTotal} icon="📝" />
        <StatCard label="Reddit Engagements" value={redditTotal} icon="💬" />
        <StatCard label="Ad Impressions" value={adImpressions.toLocaleString()} icon="👁️" />
        <StatCard label="Ad Spend" value={`$${adSpend.toFixed(2)}`} icon="💰" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Ad Clicks" value={adClicks.toLocaleString()} icon="🖱️" />
        <StatCard
          label="Ad CTR"
          value={adImpressions > 0 ? `${(adClicks / adImpressions * 100).toFixed(2)}%` : '0%'}
          icon="📊"
        />
        <StatCard label="Page Visits" value={lpVisits.toLocaleString()} icon="🌐" />
        <StatCard label="LP Conversions" value={lpConversions} icon="🎯" />
      </div>

      {/* Channel Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Content by Status */}
        <div className="bg-bg-card rounded-xl p-4 border border-border-subtle">
          <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-3">Content by Status</h3>
          {analytics?.content && Object.keys(analytics.content).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(analytics.content).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between px-3 py-2 bg-bg-main rounded-lg">
                  <span className="text-sm text-white capitalize">{status}</span>
                  <span className="text-sm font-mono text-text-muted">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted py-4 text-center">No content data</p>
          )}
        </div>

        {/* Ad Performance by Platform */}
        <div className="bg-bg-card rounded-xl p-4 border border-border-subtle">
          <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-3">Ad Performance by Platform</h3>
          {analytics?.ads && analytics.ads.length > 0 ? (
            <div className="space-y-2">
              {analytics.ads.map((ad) => (
                <div key={ad.platform} className="px-3 py-2 bg-bg-main rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-white capitalize">{ad.platform}</span>
                    <span className="text-xs text-text-muted">${(ad.spend || 0).toFixed(2)} spent</span>
                  </div>
                  <div className="flex gap-4 text-xs text-text-muted">
                    <span>{(ad.impressions || 0).toLocaleString()} impressions</span>
                    <span>{(ad.clicks || 0).toLocaleString()} clicks</span>
                    <span>{ad.conversions || 0} conversions</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-muted py-4 text-center">No ad data</p>
          )}
        </div>
      </div>

      {/* Daily Performance Table */}
      <div className="bg-bg-card rounded-xl p-4 border border-border-subtle">
        <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-3">Daily Performance</h3>
        {daily.length > 0 ? (
          <div className="overflow-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-subtle text-xs text-text-muted">
                  <th className="py-2 px-3 text-left">Date</th>
                  <th className="py-2 px-3 text-left">Platform</th>
                  <th className="py-2 px-3 text-left">Impressions</th>
                  <th className="py-2 px-3 text-left">Clicks</th>
                  <th className="py-2 px-3 text-left">Spend</th>
                  <th className="py-2 px-3 text-left">Content</th>
                  <th className="py-2 px-3 text-left">Reddit</th>
                </tr>
              </thead>
              <tbody>
                {daily.slice(0, 20).map((d) => (
                  <tr key={d.id} className="border-b border-border-subtle hover:bg-bg-hover text-sm">
                    <td className="py-2 px-3 font-mono text-xs">{d.date}</td>
                    <td className="py-2 px-3 capitalize">{d.platform}</td>
                    <td className="py-2 px-3 font-mono">{(d.impressions || 0).toLocaleString()}</td>
                    <td className="py-2 px-3 font-mono">{(d.clicks || 0).toLocaleString()}</td>
                    <td className="py-2 px-3 font-mono">${(d.spend || 0).toFixed(2)}</td>
                    <td className="py-2 px-3 font-mono">{d.content_generated || 0}</td>
                    <td className="py-2 px-3 font-mono">{d.reddit_comments || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-text-muted py-4 text-center">No daily performance data yet</p>
        )}
      </div>
    </div>
  );
}
