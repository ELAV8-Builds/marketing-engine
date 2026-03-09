'use client';

import { useEffect, useState } from 'react';
import { fetchRedditEngagements, approveEngagement, rejectEngagement, RedditEngagement } from '@/lib/api';

interface RedditPost {
  id: string;
  title: string;
  subreddit: string;
  score: number;
  num_comments: number;
  url: string;
}

export default function RedditPage() {
  const [engagements, setEngagements] = useState<RedditEngagement[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [showDiscover, setShowDiscover] = useState(false);
  const [posts, setPosts] = useState<RedditPost[]>([]);
  const [subreddit, setSubreddit] = useState('');
  const [keywords, setKeywords] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  async function loadEngagements() {
    try {
      const data = await fetchRedditEngagements('', filter);
      setEngagements(data.engagements || []);
    } catch {
      // Engine offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEngagements();
  }, [filter]);

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

  const handleApprove = async (id: string) => {
    setActionLoading(id);
    try {
      await approveEngagement(id);
      await loadEngagements();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Approve failed');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: string) => {
    setActionLoading(id);
    try {
      await rejectEngagement(id);
      await loadEngagements();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Reject failed');
    } finally {
      setActionLoading(null);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'posted': return 'bg-green-900/50 text-green-400';
      case 'pending': case 'pending_review': case 'generated': return 'bg-yellow-900/50 text-yellow-400';
      case 'rejected': return 'bg-red-900/50 text-red-400';
      case 'failed': return 'bg-red-900/50 text-red-400';
      default: return 'bg-zinc-800 text-zinc-400';
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Reddit Engagement</h1>
          <p className="text-sm text-zinc-400 mt-1">AI-generated comments with approval workflow</p>
        </div>
        <button
          onClick={() => setShowDiscover(!showDiscover)}
          className="px-4 py-2 bg-[#FF5700] text-white text-sm rounded-lg hover:opacity-80 transition-opacity"
        >
          Discover Posts
        </button>
      </div>

      {showDiscover && (
        <div className="bg-zinc-900 rounded-xl p-6 border border-zinc-800 mb-6">
          <h2 className="text-lg font-bold text-white mb-4">Find Reddit Posts</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-zinc-400">Subreddits (comma-separated)</label>
              <input
                type="text"
                value={subreddit}
                onChange={(e) => setSubreddit(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white focus:border-purple-500 focus:outline-none"
                placeholder="SaaS, startups, smallbusiness"
              />
            </div>
            <div>
              <label className="text-xs text-zinc-400">Keywords (optional)</label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                className="w-full mt-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white focus:border-purple-500 focus:outline-none"
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
                  className="flex items-center justify-between px-4 py-3 bg-zinc-800 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{post.title}</p>
                    <p className="text-xs text-zinc-500">
                      r/{post.subreddit} · {post.score} pts · {post.num_comments} comments
                    </p>
                  </div>
                  <a
                    href={post.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-3 text-xs text-purple-400 hover:underline whitespace-nowrap"
                  >
                    View →
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {['', 'pending_review', 'posted', 'rejected'].map((f) => (
          <button
            key={f}
            onClick={() => { setFilter(f); setLoading(true); }}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              filter === f
                ? 'bg-purple-600 text-white'
                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
            }`}
          >
            {f === '' ? 'All' : f === 'pending_review' ? 'Pending Review' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : engagements.length === 0 ? (
        <div className="bg-zinc-900 rounded-xl p-12 border border-zinc-800 text-center">
          <p className="text-4xl mb-3">💬</p>
          <p className="text-white font-medium">No Reddit engagements yet</p>
          <p className="text-sm text-zinc-400 mt-1">
            Discover posts and generate AI comments to engage
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {engagements.map((eng) => (
            <div key={eng.id} className="bg-zinc-900 rounded-xl border border-zinc-800 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-zinc-500">r/{eng.subreddit}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${statusColor(eng.status)}`}>
                      {eng.status}
                    </span>
                    <span className="text-xs text-zinc-500">
                      confidence: {(eng.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-white font-medium mb-2">{eng.post_title}</p>
                  <div className="p-3 bg-zinc-800 rounded-lg">
                    <p className="text-sm text-zinc-300 whitespace-pre-wrap">{eng.comment_text}</p>
                  </div>
                </div>

                {(eng.status === 'pending' || eng.status === 'pending_review' || eng.status === 'generated') && (
                  <div className="flex flex-col gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleApprove(eng.id)}
                      disabled={actionLoading === eng.id}
                      className="px-3 py-1.5 text-xs bg-green-600 hover:bg-green-700 disabled:bg-zinc-700 text-white rounded-lg transition-colors"
                    >
                      {actionLoading === eng.id ? '...' : 'Approve & Post'}
                    </button>
                    <button
                      onClick={() => handleReject(eng.id)}
                      disabled={actionLoading === eng.id}
                      className="px-3 py-1.5 text-xs bg-red-600 hover:bg-red-700 disabled:bg-zinc-700 text-white rounded-lg transition-colors"
                    >
                      {actionLoading === eng.id ? '...' : 'Reject'}
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-4 mt-2 text-xs text-zinc-500">
                <span>{eng.upvotes} upvotes</span>
                <span>{new Date(eng.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
