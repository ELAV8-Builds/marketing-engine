"""
Marketing Engine API — REST endpoints for all marketing operations.
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

import config

from api.routes.campaigns import router as campaigns_router
from api.routes.content import router as content_router
from api.routes.reddit import router as reddit_router
from api.routes.ads import router as ads_router
from api.routes.landing_pages import router as landing_pages_router
from api.routes.analytics import router as analytics_router
from api.routes.video import router as video_router
from api.routes.logos import router as logos_router
from api.routes.calendar import router as calendar_router
from api.routes.stream import router as stream_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketing Engine API",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.1.0",
        "services": {
            "litellm": bool(config.LITELLM_URL),
            "reddit": bool(config.REDDIT_CLIENT_ID),
            "meta_ads": bool(config.META_ACCESS_TOKEN),
            "google_ads": bool(config.GOOGLE_ADS_DEVELOPER_TOKEN),
            "tiktok_ads": bool(config.TIKTOK_ACCESS_TOKEN),
            "heygen": bool(config.HEYGEN_API_KEY),
            "pexels": bool(config.PEXELS_API_KEY),
            "elevenlabs": bool(config.ELEVENLABS_API_KEY),
            "youtube": bool(config.YOUTUBE_API_KEY),
        },
    }


# ── Register routers ─────────────────────────────────────

app.include_router(campaigns_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(reddit_router, prefix="/api")
app.include_router(ads_router, prefix="/api")
app.include_router(landing_pages_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(video_router, prefix="/api")
app.include_router(logos_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
