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

export default function VideoPage() {
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
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Video Generator</h1>
        <p className="text-zinc-400 mt-1">Create faceless videos with AI script + stock footage or avatar</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-400 mb-1">Topic *</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="5 Morning Habits That Changed My Life"
              className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1">Product Name</label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="Optional product mention"
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1">Product URL</label>
              <input
                type="text"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1">Video Mode</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
              >
                <option value="stock">Stock Footage (Pexels)</option>
                <option value="avatar">AI Avatar (HeyGen)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-1">Voice</label>
              <select
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
              >
                {VOICES.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="uploadYt"
              checked={uploadYouTube}
              onChange={(e) => setUploadYouTube(e.target.checked)}
              className="rounded border-zinc-700 bg-zinc-800 text-purple-500"
            />
            <label htmlFor="uploadYt" className="text-sm text-zinc-400">
              Auto-upload to YouTube after generation
            </label>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading || !topic}
            className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Generating Video...
              </span>
            ) : (
              'Generate Video'
            )}
          </button>

          {mode === 'stock' && (
            <p className="text-xs text-zinc-500">
              Generates script → TTS voiceover → downloads stock footage → composes with FFmpeg
            </p>
          )}
          {mode === 'avatar' && (
            <p className="text-xs text-zinc-500">
              Generates script → sends to HeyGen AI avatar → polls until video ready
            </p>
          )}
        </div>

        {/* Result */}
        <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
          {error && (
            <div className="p-4 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm mb-4">
              {error}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
              <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <p>Enter a topic and click Generate to create a video</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-400">
              <svg className="animate-spin h-12 w-12 mb-4 text-purple-500" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <p className="text-sm">Generating video — this may take 1-5 minutes...</p>
              <p className="text-xs text-zinc-500 mt-1">Script → Voice → Footage → Compose</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-900/50 text-green-400">
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
                <p className="text-sm text-zinc-400">{result.description}</p>
              )}

              {(result.video_path || result.video_url) && (
                <div className="p-3 bg-zinc-800 rounded-lg">
                  <p className="text-xs text-zinc-500 mb-1">Video Location</p>
                  <p className="text-sm text-zinc-300 font-mono break-all">
                    {result.video_url || result.video_path}
                  </p>
                </div>
              )}

              {result.uploads && Object.entries(result.uploads).map(([platform, upload]) => (
                <div key={platform} className="p-3 bg-zinc-800 rounded-lg">
                  <p className="text-xs text-zinc-500 mb-1">YouTube Upload</p>
                  {upload.status === 'uploaded' && upload.url ? (
                    <a href={upload.url} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 text-sm">
                      {upload.url}
                    </a>
                  ) : (
                    <p className="text-sm text-zinc-400">{upload.status}</p>
                  )}
                </div>
              ))}

              {result.job_id && (
                <p className="text-xs text-zinc-500">Job ID: {result.job_id}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
