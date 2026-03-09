const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8300';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${ENGINE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API Error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────────────

export interface Campaign {
  id: string;
  name: string;
  product_name: string;
  product_url: string;
  product_description: string;
  target_audience: string;
  channels: string[];
  budget_daily: number;
  budget_total: number;
  status: string;
  created_at: string;
}

export interface ContentItem {
  id: string;
  campaign_id: string;
  content_type: string;
  platform: string;
  title: string;
  body: string;
  media_url: string;
  status: string;
  created_at: string;
}

export interface RedditEngagement {
  id: string;
  campaign_id: string;
  subreddit: string;
  post_id: string;
  post_title: string;
  comment_text: string;
  comment_type: string;
  confidence_score: number;
  status: string;
  upvotes: number;
  created_at: string;
}

export interface AdCampaign {
  id: string;
  campaign_id: string;
  platform: string;
  name: string;
  objective: string;
  budget_daily: number;
  impressions: number;
  clicks: number;
  spend_total: number;
  conversions: number;
  ctr: number;
  cpc: number;
  status: string;
  created_at: string;
}

export interface LandingPage {
  id: string;
  campaign_id: string;
  name: string;
  slug: string;
  template: string;
  headline: string;
  visits: number;
  conversions: number;
  status: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  services: Record<string, boolean>;
}

export interface AnalyticsOverview {
  content: Record<string, number>;
  reddit: Record<string, number>;
  ads: Array<{
    platform: string;
    impressions: number;
    clicks: number;
    spend: number;
    conversions: number;
  }>;
  landing_pages: {
    count: number;
    visits: number;
    conversions: number;
  };
}

export interface DailyPerformance {
  id: string;
  campaign_id: string;
  date: string;
  platform: string;
  impressions: number;
  clicks: number;
  spend: number;
  content_generated: number;
  reddit_comments: number;
  reddit_upvotes: number;
}

// ── API Functions ──────────────────────────────────────────

export async function fetchHealth(): Promise<HealthStatus> {
  return apiFetch('/api/health');
}

export async function fetchCampaigns(status = 'all', limit = 50): Promise<{ campaigns: Campaign[]; count: number }> {
  return apiFetch(`/api/campaigns?status=${status}&limit=${limit}`);
}

export async function createCampaign(data: Partial<Campaign>): Promise<Campaign> {
  return apiFetch('/api/campaigns', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchContent(campaign_id = '', platform = '', limit = 50): Promise<{ content: ContentItem[]; count: number }> {
  const params = new URLSearchParams();
  if (campaign_id) params.set('campaign_id', campaign_id);
  if (platform) params.set('platform', platform);
  params.set('limit', String(limit));
  return apiFetch(`/api/content?${params}`);
}

export async function generateContent(data: {
  campaign_id?: string;
  content_type: string;
  platform: string;
  topic?: string;
  product_name?: string;
  product_url?: string;
  product_description?: string;
  target_audience?: string;
  params?: Record<string, unknown>;
}): Promise<Record<string, unknown>> {
  return apiFetch('/api/content/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchRedditEngagements(campaign_id = ''): Promise<{ engagements?: RedditEngagement[] }> {
  const params = campaign_id ? `?campaign_id=${campaign_id}` : '';
  return apiFetch(`/api/content${params}`);
}

export async function fetchAdCampaigns(campaign_id = '', platform = ''): Promise<{ ads: AdCampaign[]; count: number }> {
  const params = new URLSearchParams();
  if (campaign_id) params.set('campaign_id', campaign_id);
  if (platform) params.set('platform', platform);
  return apiFetch(`/api/ads?${params}`);
}

export async function createAdCampaign(data: {
  campaign_id?: string;
  platform: string;
  name: string;
  objective?: string;
  daily_budget?: number;
  product_name?: string;
  product_description?: string;
  target_audience?: string;
  creative_count?: number;
}): Promise<Record<string, unknown>> {
  return apiFetch('/api/ads/create', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchLandingPages(campaign_id = ''): Promise<{ pages: LandingPage[]; count: number }> {
  const params = campaign_id ? `?campaign_id=${campaign_id}` : '';
  return apiFetch(`/api/landing-pages${params}`);
}

export async function fetchAnalytics(campaign_id = ''): Promise<AnalyticsOverview> {
  const params = campaign_id ? `?campaign_id=${campaign_id}` : '';
  return apiFetch(`/api/analytics/overview${params}`);
}

export async function fetchDailyPerformance(campaign_id = '', days = 30): Promise<{ performance: DailyPerformance[] }> {
  const params = new URLSearchParams();
  if (campaign_id) params.set('campaign_id', campaign_id);
  params.set('days', String(days));
  return apiFetch(`/api/analytics/daily?${params}`);
}

export async function generateVideo(data: {
  topic: string;
  product_name?: string;
  product_url?: string;
  mode?: string;
  voice?: string;
  campaign_id?: string;
  upload_to?: string[];
}): Promise<Record<string, unknown>> {
  return apiFetch('/api/video/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchCalendar(campaign_id = '', start_date = '', end_date = ''): Promise<{ calendar: unknown[]; count: number }> {
  const params = new URLSearchParams();
  if (campaign_id) params.set('campaign_id', campaign_id);
  if (start_date) params.set('start_date', start_date);
  if (end_date) params.set('end_date', end_date);
  return apiFetch(`/api/calendar?${params}`);
}
