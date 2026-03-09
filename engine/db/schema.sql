-- Marketing Engine Database Schema

-- ── Campaigns ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_url TEXT,
    product_description TEXT,
    target_audience TEXT,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, active, paused, completed
    channels TEXT[] DEFAULT '{}',  -- youtube, tiktok, instagram, reddit, meta_ads, google_ads
    budget_daily NUMERIC(12,2) DEFAULT 0,
    budget_total NUMERIC(12,2) DEFAULT 0,
    spent_total NUMERIC(12,2) DEFAULT 0,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Content Items ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    content_type TEXT NOT NULL,  -- video_short, video_long, reddit_comment, blog_post, ad_creative, landing_page
    platform TEXT NOT NULL,  -- youtube, tiktok, instagram, reddit, meta, google, website
    title TEXT,
    body TEXT,
    script TEXT,
    media_url TEXT,
    thumbnail_url TEXT,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, generating, ready, published, failed
    published_at TIMESTAMPTZ,
    published_url TEXT,
    external_id TEXT,  -- Platform-specific ID (YouTube video ID, Reddit comment ID, etc.)
    metrics JSONB DEFAULT '{}',  -- views, likes, comments, shares, clicks, etc.
    generation_params JSONB DEFAULT '{}',  -- Parameters used to generate this content
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_campaign ON content_items(campaign_id);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_items(status);
CREATE INDEX IF NOT EXISTS idx_content_platform ON content_items(platform);

-- ── Reddit Accounts ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS reddit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    karma INTEGER DEFAULT 0,
    account_age_days INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'warming',  -- warming, active, cooldown, banned
    last_comment_at TIMESTAMPTZ,
    total_comments INTEGER DEFAULT 0,
    promotional_comments INTEGER DEFAULT 0,
    organic_comments INTEGER DEFAULT 0,
    subreddits TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Reddit Engagements ──────────────────────────────────
CREATE TABLE IF NOT EXISTS reddit_engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    account_id UUID REFERENCES reddit_accounts(id) ON DELETE SET NULL,
    subreddit TEXT NOT NULL,
    post_id TEXT NOT NULL,
    post_title TEXT,
    comment_text TEXT NOT NULL,
    comment_type TEXT NOT NULL DEFAULT 'promotional',  -- promotional, organic, seed
    confidence_score NUMERIC(5,2),
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, posted, deleted, flagged
    reddit_comment_id TEXT,
    upvotes INTEGER DEFAULT 0,
    click_throughs INTEGER DEFAULT 0,
    posted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reddit_campaign ON reddit_engagements(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reddit_subreddit ON reddit_engagements(subreddit);

-- ── Ad Campaigns ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    platform TEXT NOT NULL,  -- meta, google, tiktok
    external_campaign_id TEXT,
    name TEXT NOT NULL,
    objective TEXT,  -- traffic, conversions, awareness, engagement
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, active, paused, completed
    budget_daily NUMERIC(12,2) DEFAULT 0,
    spend_total NUMERIC(12,2) DEFAULT 0,
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    ctr NUMERIC(8,4) DEFAULT 0,
    cpc NUMERIC(8,4) DEFAULT 0,
    cpa NUMERIC(12,2) DEFAULT 0,
    roas NUMERIC(8,4) DEFAULT 0,
    target_audience JSONB DEFAULT '{}',
    creative_ids TEXT[] DEFAULT '{}',
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ad_campaign ON ad_campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ad_platform ON ad_campaigns(platform);

-- ── Ad Creatives ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ad_creatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_campaign_id UUID REFERENCES ad_campaigns(id) ON DELETE SET NULL,
    creative_type TEXT NOT NULL,  -- image, video, carousel, text
    headline TEXT,
    body_text TEXT,
    cta_text TEXT,
    media_url TEXT,
    landing_url TEXT,
    external_id TEXT,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, active, paused, rejected
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Landing Pages ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS landing_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    template TEXT,  -- product, saas, newsletter, waitlist
    headline TEXT,
    subheadline TEXT,
    body_html TEXT,
    cta_text TEXT DEFAULT 'Get Started',
    cta_url TEXT,
    deployed_url TEXT,
    vercel_project_id TEXT,
    vercel_deployment_id TEXT,
    status TEXT NOT NULL DEFAULT 'draft',  -- draft, deployed, ab_testing
    visits INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversion_rate NUMERIC(8,4) DEFAULT 0,
    variants JSONB DEFAULT '[]',  -- A/B test variants
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Analytics Events ────────────────────────────────────
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,  -- impression, click, conversion, view, comment, like, share
    platform TEXT NOT NULL,
    source TEXT,  -- reddit, youtube, meta_ad, google_ad, organic, etc.
    content_id UUID,
    value NUMERIC(12,2) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analytics_campaign ON analytics_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_time ON analytics_events(event_time);

-- ── Daily Performance ───────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    platform TEXT NOT NULL,
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend NUMERIC(12,2) DEFAULT 0,
    revenue NUMERIC(12,2) DEFAULT 0,
    content_published INTEGER DEFAULT 0,
    reddit_comments INTEGER DEFAULT 0,
    engagement_rate NUMERIC(8,4) DEFAULT 0,
    UNIQUE(campaign_id, date, platform)
);

-- ── Content Calendar ────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    platform TEXT NOT NULL,
    content_type TEXT NOT NULL,
    topic TEXT,
    content_id UUID REFERENCES content_items(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',  -- scheduled, generating, published, skipped
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON content_calendar(scheduled_date);
