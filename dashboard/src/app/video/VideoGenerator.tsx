'use client';

import { useState } from 'react';
import { generateVideo } from '@/lib/api';

const VOICES = [
  { id: 'en-US-AriaNeural', name: 'Aria (US Female)', type: 'edge-tts' },
  { id: 'en-US-GuyNeural', name: 'Guy (US Male)', type: 'edge-tts' },
  { id: 'en-GB-SoniaNeural', name: 'Sonia (UK Female)', type: 'edge-tts' },
  { id: 'en-AU-NatashaNeural', name: 'Natasha (AU Female)', type: 'edge-tts' },
  { id: 'en-US-JennyNeural', name: 'Jenny (US Female)', type: 'edge-tts' },
];

type VideoResult = {
  video_path?: string;
  video_url?: string;
  title?: string;
  description?: string;
  duration?: number;
  job_id?: string;
  status?: string;
  uploads?: Record<string, { status?: string; url?: string }>;
};

interface VideoGeneratorProps {
  onVideoGenerated: () => void;
}

export default function VideoGenerator({ onVideoGenerated }: VideoGeneratorProps) {
  const [topic, setTopic] = useState('');
  const [productName, setProductName] = useState('');
  const [productUrl, setProductUrl] = useState('');
  const [mode, setMode] = useState('stock');
  const [voice, setVoice] = useState('en-US-AriaNeural');
  const [uploadYouTube, setUploadYouTube] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!topic) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const data = await generateVideo({
        topic,
        product_name: productName,
        product_url: productUrl,
        mode,
        voice,
        upload_to: uploadYouTube ? ['youtube'] : [],
      });
      setResult(data as VideoResult);
      onVideoGenerated();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Form */}
      <div className="glass rounded-2xl p-6 space-y-5">
        <div>
          <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Topic *</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="5 Morning Habits That Changed My Life"
            className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm glow-ring"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Product Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="Optional product mention"
              className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Product URL</label>
            <input
              type="text"
              value={productUrl}
              onChange={(e) => setProductUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white placeholder-zinc-600 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-400 mb-2 uppercase tracking-wider">Video Mode</label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setMode('stock')}
              className={`p-4 rounded-xl text-left transition-all ${
                mode === 'stock'
                  ? 'bg-accent-purple/10 border border-accent-purple/25'
                  : 'bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04]'
              }`}
            >
              <span className="text-xl mb-1 block">🎞️</span>
              <p className="text-sm font-medium text-white">Stock Footage</p>
              <p className="text-xs text-zinc-500 mt-0.5">Pexels HD clips + TTS voiceover</p>
            </button>
            <button
              onClick={() => setMode('avatar')}
              className={`p-4 rounded-xl text-left transition-all ${
                mode === 'avatar'
                  ? 'bg-accent-teal/10 border border-accent-teal/25'
                  : 'bg-white/[0.02] border border-white/[0.04] hover:bg-white/[0.04]'
              }`}
            >
              <span className="text-xl mb-1 block">🧑‍💼</span>
              <p className="text-sm font-medium text-white">AI Avatar</p>
              <p className="text-xs text-zinc-500 mt-0.5">HeyGen realistic avatar</p>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-400 mb-1.5 uppercase tracking-wider">Voice</label>
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            className="w-full px-4 py-2.5 bg-surface-3 border border-white/[0.06] rounded-xl text-white text-sm"
          >
            {VOICES.map((v) => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>
        </div>

        <label className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.04] cursor-pointer hover:bg-white/[0.04] transition-colors">
          <input
            type="checkbox"
            checked={uploadYouTube}
            onChange={(e) => setUploadYouTube(e.target.checked)}
            className="rounded border-zinc-700 bg-zinc-800 text-accent-purple w-4 h-4"
          />
          <div>
            <p className="text-sm text-white">Auto-upload to YouTube</p>
            <p className="text-xs text-zinc-500">Publish as YouTube Short after generation</p>
          </div>
        </label>

        <button
          onClick={handleGenerate}
          disabled={loading || !topic}
          className="w-full py-3.5 bg-gradient-to-r from-accent-purple to-accent-teal text-white font-semibold rounded-xl hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed transition-all btn-press"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Generating Video...
            </span>
          ) : (
            'Generate Video'
          )}
        </button>
      </div>

      {/* Result */}
      <div className="glass rounded-2xl p-6">
        {error && (
          <div className="p-4 bg-accent-red/5 border border-accent-red/20 rounded-xl text-accent-red text-sm mb-4">
            {error}
          </div>
        )}

        {!result && !loading && !error && (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-accent-purple/10 to-accent-teal/10 flex items-center justify-center mb-4">
              <span className="text-3xl">🎬</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-1">Create Your First Video</h3>
            <p className="text-sm text-zinc-500 max-w-sm">
              Enter a topic and the AI will write a script, generate voiceover, find matching stock footage, and compose the final video.
            </p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
            <div className="relative">
              <div className="w-16 h-16 border-2 border-accent-purple/20 border-t-accent-purple rounded-full animate-spin" />
              <span className="absolute inset-0 flex items-center justify-center text-xl">🎬</span>
            </div>
            <p className="text-sm text-zinc-400 mt-6">Generating video — this may take 1-5 minutes...</p>
            <div className="flex gap-2 mt-3">
              {['Script', 'Voice', 'Footage', 'Compose'].map((step, i) => (
                <span key={step} className="px-2 py-1 text-[10px] rounded-lg bg-white/[0.04] text-zinc-500">
                  {step}
                </span>
              ))}
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-accent-green/10 text-accent-green">
                {result.status || 'Complete'}
              </span>
              {result.duration && (
                <span className="text-xs text-zinc-500">{result.duration.toFixed(1)}s</span>
              )}
            </div>

            {result.title && (
              <h3 className="text-lg font-semibold text-white">{result.title}</h3>
            )}

            {result.description && (
              <p className="text-sm text-zinc-400 leading-relaxed">{result.description}</p>
            )}

            {(result.video_path || result.video_url) && (
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">Video Location</p>
                <p className="text-sm text-zinc-300 font-mono break-all">
                  {result.video_url || result.video_path}
                </p>
              </div>
            )}

            {result.uploads && Object.entries(result.uploads).map(([platform, upload]) => (
              <div key={platform} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">YouTube Upload</p>
                {upload.status === 'uploaded' && upload.url ? (
                  <a href={upload.url} target="_blank" rel="noopener noreferrer" className="text-accent-purple hover:text-accent-teal text-sm transition-colors">
                    {upload.url} →
                  </a>
                ) : (
                  <p className="text-sm text-zinc-400">{upload.status}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
