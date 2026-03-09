"""
Marketing Engine Configuration — All settings via environment variables.
"""
import os

def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

def env_int(key: str, default: int = 0) -> int:
    return int(os.environ.get(key, str(default)))

def env_float(key: str, default: float = 0.0) -> float:
    return float(os.environ.get(key, str(default)))

def env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in ("true", "1", "yes")

# ── Database ─────────────────────────────────────────────
DATABASE_URL = env("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5434/marketing")
REDIS_URL = env("REDIS_URL", "redis://localhost:6381/0")

# ── LLM / AI ────────────────────────────────────────────
LITELLM_URL = env("LITELLM_URL", "http://host.docker.internal:4000")
LITELLM_MODEL = env("LITELLM_MODEL", "coder")  # Default tier
LITELLM_LIGHT_MODEL = env("LITELLM_LIGHT_MODEL", "light")
LITELLM_CREATIVE_MODEL = env("LITELLM_CREATIVE_MODEL", "creative")

# ── Faceless Video ───────────────────────────────────────
PEXELS_API_KEY = env("PEXELS_API_KEY")
HEYGEN_API_KEY = env("HEYGEN_API_KEY")
ELEVENLABS_API_KEY = env("ELEVENLABS_API_KEY")
YOUTUBE_API_KEY = env("YOUTUBE_API_KEY")
YOUTUBE_CLIENT_ID = env("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = env("YOUTUBE_CLIENT_SECRET")
YOUTUBE_REFRESH_TOKEN = env("YOUTUBE_REFRESH_TOKEN")

# ── Reddit ───────────────────────────────────────────────
REDDIT_CLIENT_ID = env("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = env("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = env("REDDIT_USERNAME")
REDDIT_PASSWORD = env("REDDIT_PASSWORD")
REDDIT_USER_AGENT = env("REDDIT_USER_AGENT", "MarketingEngine/1.0")
REDDIT_MIN_ACCOUNT_AGE_DAYS = env_int("REDDIT_MIN_ACCOUNT_AGE_DAYS", 30)
REDDIT_COMMENT_RATIO = env_int("REDDIT_COMMENT_RATIO", 10)  # 10 organic : 1 promotional

# ── Meta Ads ─────────────────────────────────────────────
META_APP_ID = env("META_APP_ID")
META_APP_SECRET = env("META_APP_SECRET")
META_ACCESS_TOKEN = env("META_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = env("META_AD_ACCOUNT_ID")

# ── Google Ads ───────────────────────────────────────────
GOOGLE_ADS_DEVELOPER_TOKEN = env("GOOGLE_ADS_DEVELOPER_TOKEN")
GOOGLE_ADS_CLIENT_ID = env("GOOGLE_ADS_CLIENT_ID")
GOOGLE_ADS_CLIENT_SECRET = env("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REFRESH_TOKEN = env("GOOGLE_ADS_REFRESH_TOKEN")
GOOGLE_ADS_CUSTOMER_ID = env("GOOGLE_ADS_CUSTOMER_ID")

# ── TikTok Ads ───────────────────────────────────────────
TIKTOK_ACCESS_TOKEN = env("TIKTOK_ACCESS_TOKEN")
TIKTOK_ADVERTISER_ID = env("TIKTOK_ADVERTISER_ID")

# ── Landing Pages ────────────────────────────────────────
VERCEL_TOKEN = env("VERCEL_TOKEN")
VERCEL_TEAM_ID = env("VERCEL_TEAM_ID")

# ── Content Calendar ─────────────────────────────────────
DAILY_POSTS_TARGET = env_int("DAILY_POSTS_TARGET", 3)
REDDIT_CHECK_INTERVAL_MINUTES = env_int("REDDIT_CHECK_INTERVAL_MINUTES", 30)
AD_OPTIMIZE_INTERVAL_HOURS = env_int("AD_OPTIMIZE_INTERVAL_HOURS", 6)

# ── Server ───────────────────────────────────────────────
API_HOST = env("API_HOST", "0.0.0.0")
API_PORT = env_int("API_PORT", 8300)
