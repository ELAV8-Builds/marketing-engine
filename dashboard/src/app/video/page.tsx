'use client';

import { useState, useEffect } from 'react';
import { fetchContent, ContentItem } from '@/lib/api';
import VideoGenerator from './VideoGenerator';
import VideoGallery from './VideoGallery';

export default function VideoPage() {
  const [tab, setTab] = useState<'create' | 'gallery'>('create');
  const [videos, setVideos] = useState<ContentItem[]>([]);
  const [galleryLoading, setGalleryLoading] = useState(true);

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      const data = await fetchContent('', 'youtube', 50);
      setVideos(data.content.filter(c => c.content_type === 'video_short' || c.media_url));
    } catch {
      // Engine offline
    } finally {
      setGalleryLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Video Studio</h1>
          <p className="text-sm text-zinc-500 mt-1">Create faceless videos with AI — stock footage or avatar mode</p>
        </div>

        {/* Tab switcher */}
        <div className="glass rounded-xl p-1 flex gap-1">
          <button
            onClick={() => setTab('create')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === 'create' ? 'bg-accent-purple/15 text-white' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Create New
          </button>
          <button
            onClick={() => setTab('gallery')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === 'gallery' ? 'bg-accent-purple/15 text-white' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Gallery ({videos.length})
          </button>
        </div>
      </div>

      {tab === 'create' && (
        <VideoGenerator onVideoGenerated={loadVideos} />
      )}

      {tab === 'gallery' && (
        <VideoGallery videos={videos} loading={galleryLoading} />
      )}
    </div>
  );
}
