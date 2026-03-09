'use client';

import { useEffect, useState } from 'react';
import ContentTable from '@/components/ContentTable';
import { fetchContent, generateContent, ContentItem } from '@/lib/api';

export default function ContentPage() {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [form, setForm] = useState({
    content_type: 'video_short',
    platform: 'youtube',
    topic: '',
    product_name: '',
    product_url: '',
  });
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  async function loadContent() {
    try {
      const data = await fetchContent('', '', 100);
      setContent(data.content);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContent();
  }, []);

  const handleGenerate = async () => {
    if (!form.topic && !form.product_name) return;
    setGenerating(true);
    setResult(null);
    try {
      const res = await generateContent(form);
      setResult(res);
      loadContent();
    } catch (e) {
      alert('Generation failed — is the engine running?');
    } finally {
      setGenerating(false);
    }
  };

  const contentTypes = [
    { value: 'video_short', label: 'Video Short' },
    { value: 'blog_post', label: 'Blog Post' },
    { value: 'ad_creative', label: 'Ad Creative' },
    { value: 'landing_page', label: 'Landing Page' },
    { value: 'reddit_comment', label: 'Reddit Comment' },
  ];

  const platforms = [
    { value: 'youtube', label: 'YouTube' },
    { value: 'tiktok', label: 'TikTok' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'reddit', label: 'Reddit' },
    { value: 'meta', label: 'Meta Ads' },
    { value: 'website', label: 'Website' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Content</h1>
        <button
          onClick={() => setShowGenerate(!showGenerate)}
          className="px-4 py-2 bg-accent-purple text-white text-sm rounded-lg hover:bg-accent-purple/80 transition-colors"
        >
          + Generate Content
        </button>
      </div>

      {showGenerate && (
        <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
          <h2 className="text-lg font-bold text-white mb-4">AI Content Generator</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-muted">Content Type</label>
              <select
                value={form.content_type}
                onChange={(e) => setForm({ ...form, content_type: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              >
                {contentTypes.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted">Platform</label>
              <select
                value={form.platform}
                onChange={(e) => setForm({ ...form, platform: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              >
                {platforms.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-text-muted">Topic / Prompt</label>
              <textarea
                value={form.topic}
                onChange={(e) => setForm({ ...form, topic: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                rows={2}
                placeholder="e.g., 5 AI tools that will save you 10 hours a week"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Product Name (optional)</label>
              <input
                type="text"
                value={form.product_name}
                onChange={(e) => setForm({ ...form, product_name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Product URL (optional)</label>
              <input
                type="text"
                value={form.product_url}
                onChange={(e) => setForm({ ...form, product_url: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleGenerate}
              disabled={generating || (!form.topic && !form.product_name)}
              className="px-4 py-2 bg-accent-purple text-white text-sm rounded-lg hover:bg-accent-purple/80 disabled:opacity-50 transition-colors"
            >
              {generating ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Generating...
                </span>
              ) : (
                'Generate'
              )}
            </button>
            <button
              onClick={() => { setShowGenerate(false); setResult(null); }}
              className="px-4 py-2 bg-bg-main text-text-muted text-sm rounded-lg hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>

          {result && (
            <div className="mt-4 p-4 bg-bg-main rounded-lg border border-border-subtle">
              <p className="text-xs text-accent-green mb-2 font-medium">Generated Successfully</p>
              <pre className="text-xs text-text-muted overflow-auto max-h-64 whitespace-pre-wrap">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ContentTable items={content} />
      )}
    </div>
  );
}
