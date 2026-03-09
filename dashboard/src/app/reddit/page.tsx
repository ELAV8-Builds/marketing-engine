'use client';

import { useEffect, useState } from 'react';
import { fetchContent, ContentItem } from '@/lib/api';

interface RedditPost {
  id: string;
  title: string;
  subreddit: string;
  score: number;
  num_comments: number;
  url: string;
}

export default function RedditPage() {
  const [engagements, setEngagements] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [showDiscover, setShowDiscover] = useState(false);
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [subreddit, setSubreddit] = useState('');
  const [keywords, setKeywords] = useState('');

  async function loadEngagements() {
    try {
      const data = await fetchContent('', 'reddit', 100);
      setEngagements(data.content);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEngagements();
  }, []);

  const handleDiscover = async () => {
    if (!subreddit) return;
    setDiscovering(true);
    try {
      const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8300';
      const res = await fetch(`${ENGINE_URL}/api/reddit/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subreddits: subreddit.split(',').map(s => s.trim()),
          keywords: keywords ? keywords.split(',').map(k => k.trim()) : [],
          limit: 10,
        }),
      });
      const data = await res.json();
      setPosts(data.posts || []);
    } catch {
      alert('Discovery failed — is the engine running?');
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Reddit Engagement</h1>
        <button
          onClick={() => setShowDiscover(!showDiscover)}
          className="px-4 py-2 bg-[#FF5700] text-white text-sm rounded-lg hover:opacity-80 transition-opacity"
        >
          Discover Posts
        </button>
      </div>

      {showDiscover && (
        <div className="bg-bg-card rounded-xl p-6 border border-border-subtle mb-6">
          <h2 className="text-lg font-bold text-white mb-4">Find Reddit Posts</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-muted">Subreddits (comma-separated)</label>
              <input
                type="text"
                value={subreddit}
                onChange={(e) => setSubreddit(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="SaaS, startups, smallbusiness"
              />
            </div>
            <div>
              <label className="text-xs text-text-muted">Keywords (optional)</label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-bg-main border border-border-subtle rounded-lg text-sm text-white focus:border-accent-blue focus:outline-none"
                placeholder="automation, marketing tool"
              />
            </div>
          </div>
          <button
            onClick={handleDiscover}
            disabled={discovering || !subreddit}
            className="mt-4 px-4 py-2 bg-[#FF5700] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
          >
            {discovering ? 'Searching...' : 'Search'}
          </button>

          {posts.length > 0 && (
            <div className="mt-4 space-y-2">
              {posts.map((post) => (
                <div
                  key={post.id}
                  className="flex items-center justify-between px-4 py-3 bg-bg-main rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{post.title}</p>
                    <p className="text-xs text-text-muted">
                      r/{post.subreddit} · {post.score} pts · {post.num_comments} comments
                    </p>
                  </div>
                  <a
                    href={post.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-3 text-xs text-accent-blue hover:underline whitespace-nowrap"
                  >
                    View →
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
        </div>
      ) : engagements.length === 0 ? (
        <div className="bg-bg-card rounded-xl p-12 border border-border-subtle text-center">
          <p className="text-4xl mb-3">💬</p>
          <p className="text-white font-medium">No Reddit engagements yet</p>
          <p className="text-sm text-text-muted mt-1">
            Discover posts and generate AI comments to engage
          </p>
        </div>
      ) : (
        <div className="bg-bg-card rounded-xl border border-border-subtle overflow-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-subtle text-xs text-text-muted">
                <th className="py-3 px-4 text-left">Post</th>
                <th className="py-3 px-4 text-left">Subreddit</th>
                <th className="py-3 px-4 text-left">Status</th>
                <th className="py-3 px-4 text-left">Score</th>
                <th className="py-3 px-4 text-left">Created</th>
              </tr>
            </thead>
            <tbody>
              {engagements.map((e) => (
                <tr key={e.id} className="border-b border-border-subtle hover:bg-bg-hover">
                  <td className="py-3 px-4 text-sm text-white max-w-xs truncate">{e.title}</td>
                  <td className="py-3 px-4 text-sm text-text-muted">{e.platform}</td>
                  <td className="py-3 px-4 text-sm">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      e.status === 'published' ? 'bg-accent-green/20 text-accent-green' :
                      e.status === 'ready' ? 'bg-accent-blue/20 text-accent-blue' :
                      'bg-text-muted/20 text-text-muted'
                    }`}>
                      {e.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm font-mono text-text-muted">—</td>
                  <td className="py-3 px-4 text-xs text-text-muted">
                    {new Date(e.created_at).toLocaleDateString()}
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
