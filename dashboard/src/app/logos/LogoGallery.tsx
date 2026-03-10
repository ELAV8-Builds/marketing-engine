'use client';

import { LogoResult } from './LogoGenerator';

interface LogoGalleryProps {
  results: LogoResult[];
  loading: boolean;
  count: number;
}

export default function LogoGallery({ results, loading, count }: LogoGalleryProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="glass rounded-2xl aspect-square shimmer" />
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="glass rounded-2xl p-16 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-accent-purple/10 to-accent-teal/10 flex items-center justify-center mb-4">
          <span className="text-3xl">🎨</span>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">Create Your Brand Identity</h3>
        <p className="text-sm text-zinc-500 max-w-md">
          Enter your brand details and generate AI-powered logo concepts. Choose between Recraft (SVG vectors), Ideogram (best text), or DALL-E.
        </p>
      </div>
    );
  }

  return (
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
  );
}
