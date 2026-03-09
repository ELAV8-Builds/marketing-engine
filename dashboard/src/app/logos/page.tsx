'use client';

import { useState } from 'react';

interface LogoResult {
  url: string;
  style: string;
  prompt: string;
}

const STYLES = [
  { id: 'minimal', label: 'Minimal', desc: 'Clean, simple, modern' },
  { id: 'bold', label: 'Bold', desc: 'Strong, impactful, memorable' },
  { id: 'playful', label: 'Playful', desc: 'Fun, creative, colorful' },
  { id: 'luxury', label: 'Luxury', desc: 'Elegant, premium, refined' },
  { id: 'tech', label: 'Tech', desc: 'Modern, digital, futuristic' },
  { id: 'organic', label: 'Organic', desc: 'Natural, flowing, soft' },
];

const PROVIDERS = [
  { id: 'recraft', label: 'Recraft V4', desc: 'Best for logos — native SVG vectors', badge: 'Recommended' },
  { id: 'ideogram', label: 'Ideogram V3', desc: 'Best text rendering in logos' },
  { id: 'dalle', label: 'DALL-E 3', desc: 'Good general purpose' },
];

export default function LogosPage() {
  const [brandName, setBrandName] = useState('');
  const [tagline, setTagline] = useState('');
  const [industry, setIndustry] = useState('');
  const [style, setStyle] = useState('minimal');
  const [provider, setProvider] = useState('recraft');
  const [colorPrimary, setColorPrimary] = useState('#7c5cfc');
  const [colorSecondary, setColorSecondary] = useState('#5eead4');
  const [count, setCount] = useState(4);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<LogoResult[]>([]);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!brandName) return;
    setLoading(true);
    setError('');
    try {
      const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8300';
      const res = await fetch(`${ENGINE_URL}/api/logos/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand_name: brandName,
          tagline,
          industry,
          style,
          provider,
          color_primary: colorPrimary,
          color_secondary: colorSecondary,
          count,
        }),
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setResults(data.logos || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Logo Generator</h1>
        <p className="text-sm text-zinc-500 mt-1">AI-powered brand identity creation with Recraft, Ideogram, or DALL-E</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Form — left panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass rounded-2xl p-6 space-y-5">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Brand Name *</label>
              <input
                type="text"
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
                placeholder="ELAV8"
                className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm glow-ring"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Tagline</label>
              <input
                type="text"
                value={tagline}
                onChange={(e) => setTagline(e.target.value)}
                placeholder="Elevate Everything"
                className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Industry</label>
              <input
                type="text"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="AI Marketing Technology"
                className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Colors</label>
              <div className="flex gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <input
                    type="color"
                    value={colorPrimary}
                    onChange={(e) => setColorPrimary(e.target.value)}
                    className="w-8 h-8 rounded-lg border-0 cursor-pointer bg-transparent"
                  />
                  <span className="text-xs text-zinc-500 font-mono">{colorPrimary}</span>
                </div>
                <div className="flex items-center gap-2 flex-1">
                  <input
                    type="color"
                    value={colorSecondary}
                    onChange={(e) => setColorSecondary(e.target.value)}
                    className="w-8 h-8 rounded-lg border-0 cursor-pointer bg-transparent"
                  />
                  <span className="text-xs text-zinc-500 font-mono">{colorSecondary}</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wider">Style</label>
              <div className="grid grid-cols-3 gap-2">
                {STYLES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setStyle(s.id)}
                    className={`px-3 py-2 rounded-xl text-xs transition-all btn-press ${
                      style === s.id
                        ? 'bg-accent-purple/15 text-white border border-accent-purple/30'
                        : 'bg-white/[0.02] text-zinc-400 border border-white/[0.04] hover:bg-white/[0.04]'
                    }`}
                  >
                    <p className="font-medium">{s.label}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wider">AI Provider</label>
              <div className="space-y-2">
                {PROVIDERS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setProvider(p.id)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-left transition-all ${
                      provider === p.id
                        ? 'bg-accent-purple/10 border border-accent-purple/25'
                        : 'bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04]'
                    }`}
                  >
                    <div>
                      <p className={`text-sm font-medium ${provider === p.id ? 'text-white' : 'text-zinc-400'}`}>{p.label}</p>
                      <p className="text-xs text-zinc-600">{p.desc}</p>
                    </div>
                    {p.badge && (
                      <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-accent-teal/15 text-accent-teal">
                        {p.badge}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">
                Variations: {count}
              </label>
              <input
                type="range"
                min={1}
                max={8}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full accent-accent-purple"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading || !brandName}
              className="w-full py-3 bg-gradient-to-r from-accent-purple to-accent-teal text-white font-semibold rounded-xl hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-all btn-press"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Generating {count} logos...
                </span>
              ) : (
                `Generate ${count} Logo${count > 1 ? 's' : ''}`
              )}
            </button>

            <p className="text-[11px] text-zinc-600 text-center">
              ~$0.08/logo (Recraft SVG) · ~$0.04/logo (Raster)
            </p>
          </div>
        </div>

        {/* Results — right panel */}
        <div className="lg:col-span-3">
          {error && (
            <div className="glass rounded-2xl p-4 border-accent-red/20 bg-accent-red/5 mb-6">
              <p className="text-sm text-accent-red">{error}</p>
            </div>
          )}

          {results.length === 0 && !loading && (
            <div className="glass rounded-2xl p-16 flex flex-col items-center justify-center text-center">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-accent-purple/10 to-accent-teal/10 flex items-center justify-center mb-4">
                <span className="text-3xl">🎨</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">Create Your Brand Identity</h3>
              <p className="text-sm text-zinc-500 max-w-md">
                Enter your brand details and generate AI-powered logo concepts. Choose between Recraft (SVG vectors), Ideogram (best text), or DALL-E.
              </p>
            </div>
          )}

          {loading && (
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="glass rounded-2xl aspect-square shimmer" />
              ))}
            </div>
          )}

          {results.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-zinc-400">{results.length} logos generated</p>
                <button className="text-xs text-accent-purple hover:text-accent-teal transition-colors">
                  Download All (ZIP)
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {results.map((logo, i) => (
                  <div
                    key={i}
                    className="glass rounded-2xl overflow-hidden group cursor-pointer hover:border-white/10 transition-all ambient-glow"
                  >
                    <div className="aspect-square bg-white/[0.02] flex items-center justify-center p-8">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={logo.url}
                        alt={`Logo variant ${i + 1}`}
                        className="max-w-full max-h-full object-contain"
                      />
                    </div>
                    <div className="p-3 border-t border-white/[0.04]">
                      <p className="text-xs text-zinc-500 truncate">{logo.style}</p>
                      <div className="flex gap-2 mt-2">
                        <button className="flex-1 px-2 py-1.5 text-[10px] font-medium rounded-lg bg-accent-purple/10 text-accent-purple hover:bg-accent-purple/20 transition-colors">
                          Download SVG
                        </button>
                        <button className="flex-1 px-2 py-1.5 text-[10px] font-medium rounded-lg bg-white/[0.04] text-zinc-400 hover:bg-white/[0.08] transition-colors">
                          Download PNG
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
