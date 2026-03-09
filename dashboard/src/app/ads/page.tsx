'use client';

import { useEffect, useState } from 'react';
import StatCard from '@/components/StatCard';
import { fetchAdCampaigns, createAdCampaign, AdCampaign } from '@/lib/api';

export default function AdsPage() {
  const [ads, setAds] = useState<AdCampaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    platform: 'meta',
    name: '',
    objective: 'traffic',
    daily_budget: 10,
    product_name: '',
    product_description: '',
    target_audience: '',
    creative_count: 3,
  });

  async function loadAds() {
    try {
      const data = await fetchAdCampaigns();
      setAds(data.ads);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAds();
  }, []);

  const handleCreate = async () => {
    if (!form.name || !form.product_name) return;
    setCreating(true);
    try {
      await createAdCampaign(form);
      setShowCreate(false);
      loadAds();
    } catch {
      alert('Failed to create ad campaign');
    } finally {
      setCreating(false);
    }
  };

  const totalImpressions = ads.reduce((s, a) => s + (a.impressions || 0), 0);
  const totalClicks = ads.reduce((s, a) => s + (a.clicks || 0), 0);
  const totalSpend = ads.reduce((s, a) => s + (a.spend_total || 0), 0);
  const totalConversions = ads.reduce((s, a) => s + (a.conversions || 0), 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Ad Campaigns</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-accent-blue text-white text-sm rounded-lg hover:bg-accent-blue/80 transition-colors"
        >
          + Create Ad Campaign
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Impressions" value={totalImpressions.toLocaleString()} icon="👁️" />
        <StatCard label="Clicks" value={totalClicks.toLocaleString()} icon="🖱️" />
        <StatCard label="Total Spend" value={`$${totalSpend.toFixed(2)}`} icon="💰" />
        <StatCard label="Conversions" value={totalConversions} icon="🎯" />
      </div>

      {showCreate && (
        <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
          <h2 className="text-lg font-bold text-white mb-4">Create Ad Campaign</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-muted">Platform</label>
              <select
                value={form.platform}
                onChange={(e) => setForm({ ...form, platform: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              >
                <option value="meta">Meta (Facebook/Instagram)</option>
                <option value="google">Google Ads</option>
                <option value="tiktok">TikTok</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted">Campaign Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="Spring Sale Campaign"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Product Name</label>
              <input
                type="text"
                value={form.product_name}
                onChange={(e) => setForm({ ...form, product_name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Daily Budget ($)</label>
              <input
                type="number"
                value={form.daily_budget}
                onChange={(e) => setForm({ ...form, daily_budget: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-text-muted">Product Description</label>
              <textarea
                value={form.product_description}
                onChange={(e) => setForm({ ...form, product_description: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                rows={2}
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Target Audience</label>
              <input
                type="text"
                value={form.target_audience}
                onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">AI Creatives to Generate</label>
              <input
                type="number"
                value={form.creative_count}
                onChange={(e) => setForm({ ...form, creative_count: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                min={1}
                max={10}
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleCreate}
              disabled={creating}
              className="px-4 py-2 bg-accent-blue text-white text-sm rounded-lg hover:bg-accent-blue/80 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create with AI Creatives'}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 bg-bg-main text-text-muted text-sm rounded-lg hover:text-white"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
        </div>
      ) : ads.length === 0 ? (
        <div className="bg-bg-card rounded-xl p-12 border border-border-subtle text-center">
          <p className="text-4xl mb-3">📢</p>
          <p className="text-white font-medium">No ad campaigns yet</p>
          <p className="text-sm text-text-muted mt-1">
            Create an ad campaign with AI-generated creatives
          </p>
        </div>
      ) : (
        <div className="bg-bg-card rounded-xl border border-border-subtle overflow-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle text-xs text-text-muted">
                <th className="py-3 px-4 text-left">Campaign</th>
                <th className="py-3 px-4 text-left">Platform</th>
                <th className="py-3 px-4 text-left">Budget</th>
                <th className="py-3 px-4 text-left">Impressions</th>
                <th className="py-3 px-4 text-left">Clicks</th>
                <th className="py-3 px-4 text-left">CTR</th>
                <th className="py-3 px-4 text-left">Spend</th>
                <th className="py-3 px-4 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {ads.map((ad) => (
                <tr key={ad.id} className="border-b border-border-subtle hover:bg-bg-hover">
                  <td className="py-3 px-4 text-sm text-white">{ad.name}</td>
                  <td className="py-3 px-4 text-sm text-text-muted capitalize">{ad.platform}</td>
                  <td className="py-3 px-4 text-sm font-mono">${ad.budget_daily}/day</td>
                  <td className="py-3 px-4 text-sm font-mono">{(ad.impressions || 0).toLocaleString()}</td>
                  <td className="py-3 px-4 text-sm font-mono">{(ad.clicks || 0).toLocaleString()}</td>
                  <td className="py-3 px-4 text-sm font-mono">{(ad.ctr || 0).toFixed(2)}%</td>
                  <td className="py-3 px-4 text-sm font-mono">${(ad.spend_total || 0).toFixed(2)}</td>
                  <td className="py-3 px-4 text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      ad.status === 'active' ? 'bg-accent-green/20 text-accent-green' :
                      ad.status === 'created_paused' ? 'bg-accent-yellow/20 text-accent-yellow' :
                      'bg-text-muted/20 text-text-muted'
                    }`}>
                      {ad.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
