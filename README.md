# Marketing Engine

AI-powered marketing automation platform. Generate content, manage ads, engage on Reddit, and build landing pages — all from one API + dashboard.

## Architecture

```
┌──────────────────────┐     ┌──────────────────────┐
│  Python Engine       │     │  Next.js Dashboard    │
│  (Docker/VPS)        │────▶│  (Vercel)             │
│                      │ API │                       │
│  • AI Content Gen    │     │  • Campaign mgmt      │
│  • Faceless Video    │     │  • Content generator   │
│  • Reddit Automation │     │  • Reddit tracker      │
│  • Ad Management     │     │  • Ad performance      │
│  • Landing Pages     │     │  • Analytics            │
│  • FastAPI + Workers │     │  • Settings             │
└──────────┬───────────┘     └───────────────────────┘
           │
    ┌──────┴──────┐
    │  PostgreSQL  │
    │  + Redis     │
    └─────────────┘
```

## Features

- **Faceless Video Pipeline** — Script → TTS Voice → Stock Footage → Compose → Upload
  - Edge-TTS (free, 300+ voices) or HeyGen AI avatars
  - Auto-download from Pexels stock library
  - FFmpeg compositing with Ken Burns effects
  - Direct YouTube upload via Data API v3

- **Reddit Engagement** — Find posts, generate contextual comments, track performance
  - PRAW async integration
  - AI-generated comments with confidence scoring
  - Keyword-based post discovery
  - Campaign-level engagement tracking

- **Ad Campaign Management** — Create and optimize across Meta/Google/TikTok
  - AI-generated ad creatives (headlines, body, CTA)
  - Meta Ads API v21.0 integration
  - Auto-optimization with performance tracking
  - Budget management and spend analytics

- **Landing Page Generator** — AI-generated pages with SEO optimization
  - Headline, features, FAQ, social proof generation
  - Multiple templates (SaaS, ecommerce, agency)
  - SEO meta tags auto-generation

- **Content Calendar** — Scheduled content generation across all channels
  - Daily post targets
  - Multi-platform distribution
  - Automated generation from calendar entries

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/ELAV8-Builds/marketing-engine.git
cd marketing-engine
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker Compose

```bash
docker compose up -d
```

This starts:
- **Engine** on port 8300
- **PostgreSQL** on port 5434
- **Redis** on port 6381

### 3. Dashboard

Deploy the dashboard to Vercel:

```bash
cd dashboard
npx vercel --prod
```

Set `NEXT_PUBLIC_ENGINE_URL` to your engine's public URL.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service status |
| `GET` | `/api/campaigns` | List campaigns |
| `POST` | `/api/campaigns` | Create campaign |
| `POST` | `/api/content/generate` | Generate AI content |
| `GET` | `/api/content` | List content items |
| `POST` | `/api/video/generate` | Generate faceless video |
| `POST` | `/api/reddit/discover` | Find Reddit posts |
| `POST` | `/api/reddit/engage` | Generate Reddit comments |
| `POST` | `/api/ads/create` | Create ad campaign with AI creatives |
| `GET` | `/api/ads` | List ad campaigns |
| `POST` | `/api/landing-pages/generate` | Generate landing page |
| `GET` | `/api/landing-pages` | List landing pages |
| `GET` | `/api/analytics/overview` | Cross-channel analytics |
| `GET` | `/api/analytics/daily` | Daily performance |
| `GET` | `/api/calendar` | Content calendar |

## Required API Keys

| Service | Cost | Purpose |
|---------|------|---------|
| LiteLLM / LLM | Varies | AI content generation (routes via LiteLLM) |
| Pexels | Free | Stock video and images |
| HeyGen | $5-29/mo | AI avatar videos |
| Reddit (PRAW) | Free | Reddit monitoring + posting |
| Meta Ads | Free (+ ad spend) | Facebook/Instagram ads |
| Google Ads | Free (+ ad spend) | Search/Display ads |
| TikTok Marketing | Free (+ ad spend) | TikTok ads |
| YouTube Data API | Free | Video upload |
| ElevenLabs | $5-22/mo | Premium voice-over (optional) |

**Estimated cost (tools only):** ~$10-50/mo + ad spend

## Tech Stack

- **Engine**: Python 3.12, FastAPI, asyncpg, SQLAlchemy async, httpx, edge-tts, ffmpeg
- **Dashboard**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Infrastructure**: PostgreSQL, Redis, Docker Compose
- **AI**: LiteLLM (multi-model routing), Pexels, HeyGen, PRAW
