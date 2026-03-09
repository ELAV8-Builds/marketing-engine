'use client';

import { useEffect, useState } from 'react';
import CampaignCard from '@/components/CampaignCard';
import { fetchCampaigns, createCampaign, Campaign } from '@/lib/api';

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: '',
    product_name: '',
    product_url: '',
    product_description: '',
    target_audience: '',
    budget_daily: 10,
    budget_total: 300,
  });

  async function loadCampaigns() {
    try {
      const data = await fetchCampaigns('all', 100);
      setCampaigns(data.campaigns);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleCreate = async () => {
    if (!form.name || !form.product_name) return;
    setCreating(true);
    try {
      await createCampaign({
        ...form,
        channels: ['reddit', 'youtube', 'meta'],
      });
      setShowCreate(false);
      setForm({ name: '', product_name: '', product_url: '', product_description: '', target_audience: '', budget_daily: 10, budget_total: 300 });
      loadCampaigns();
    } catch (e) {
      alert('Failed to create campaign');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Campaigns</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-accent-blue text-white text-sm rounded-lg hover:bg-accent-blue/80 transition-colors"
        >
          + New Campaign
        </button>
      </div>

      {showCreate && (
        <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
          <h2 className="text-lg font-bold text-white mb-4">Create Campaign</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-muted">Campaign Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="Q1 Product Launch"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Product Name *</label>
              <input
                type="text"
                value={form.product_name}
                onChange={(e) => setForm({ ...form, product_name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="MyProduct"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Product URL</label>
              <input
                type="text"
                value={form.product_url}
                onChange={(e) => setForm({ ...form, product_url: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="https://myproduct.com"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Target Audience</label>
              <input
                type="text"
                value={form.target_audience}
                onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="SaaS founders, age 25-45"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-text-muted">Product Description</label>
              <textarea
                value={form.product_description}
                onChange={(e) => setForm({ ...form, product_description: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                rows={3}
                placeholder="Brief description of the product..."
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Daily Budget ($)</label>
              <input
                type="number"
                value={form.budget_daily}
                onChange={(e) => setForm({ ...form, budget_daily: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Total Budget ($)</label>
              <input
                type="number"
                value={form.budget_total}
                onChange={(e) => setForm({ ...form, budget_total: Number(e.target.value) })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleCreate}
              disabled={creating || !form.name || !form.product_name}
              className="px-4 py-2 bg-accent-blue text-white text-sm rounded-lg hover:bg-accent-blue/80 disabled:opacity-50 transition-colors"
            >
              {creating ? 'Creating...' : 'Create Campaign'}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 bg-bg-main text-text-muted text-sm rounded-lg hover:text-white transition-colors"
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
      ) : campaigns.length === 0 ? (
        <div className="bg-bg-card rounded-xl p-12 border border-border-subtle text-center">
          <p className="text-4xl mb-3">🎯</p>
          <p className="text-white font-medium">No campaigns yet</p>
          <p className="text-sm text-text-muted mt-1">Create your first marketing campaign to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {campaigns.map((c) => (
            <CampaignCard key={c.id} campaign={c} />
          ))}
        </div>
      )}
    </div>
  );
}
