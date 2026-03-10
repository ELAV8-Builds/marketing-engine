'use client';

import { ContentItem } from '@/lib/api';

interface VideoGalleryProps {
  videos: ContentItem[];
  loading: boolean;
}

export default function VideoGallery({ videos, loading }: VideoGalleryProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="glass rounded-2xl aspect-video shimmer" />
        ))}
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="glass rounded-2xl p-16 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-accent-purple/10 to-accent-teal/10 flex items-center justify-center mb-4">
          <span className="text-3xl">📼</span>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">No Videos Yet</h3>
        <p className="text-sm text-zinc-500 max-w-md">
          Videos you generate will appear here. Switch to the Create tab to make your first video.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {videos.map((video, i) => (
        <div
          key={video.id}
          className="glass rounded-2xl overflow-hidden group hover:border-white/10 transition-all animate-slide-up"
          style={{ animationDelay: `${i * 50}ms` }}
        >
          {/* Video thumbnail placeholder */}
          <div className="aspect-video bg-gradient-to-br from-accent-purple/5 to-accent-teal/5 flex items-center justify-center relative">
            <span className="text-4xl opacity-30">🎬</span>
            {video.media_url && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
                <a
                  href={video.media_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-white/10 backdrop-blur-sm rounded-xl text-white text-sm font-medium hover:bg-white/20 transition-colors"
                >
                  ▶ Watch
                </a>
              </div>
            )}
          </div>
          <div className="p-4">
            <h4 className="text-sm font-medium text-white truncate">{video.title || 'Untitled Video'}</h4>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-2 py-0.5 text-[10px] rounded-full ${
                video.status === 'published'
                  ? 'bg-accent-green/10 text-accent-green'
                  : 'bg-zinc-800 text-zinc-500'
              }`}>
                {video.status}
              </span>
              <span className="text-xs text-zinc-600">
                {new Date(video.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
