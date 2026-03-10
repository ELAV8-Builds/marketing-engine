"""
Marketing Engine — Main Orchestrator
Runs the continuous marketing loops and FastAPI server.
"""
import asyncio
import logging
import sys
import signal as sig
from datetime import datetime, timezone

import redis.asyncio as aioredis
import uvicorn

import config
from db.database import init_db, close_db
from api.server import app

from loops import content_loop, reddit_loop, ad_loop, analytics_loop, health_loop

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("marketing-engine")


class MarketingEngine:
    """Main orchestrator for all marketing automation loops."""

    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self._running = False

    def is_running(self) -> bool:
        """Check if the engine is still running (passed to loop modules)."""
        return self._running

    async def start(self):
        """Initialize services and start all loops."""
        logger.info("=" * 60)
        logger.info("MARKETING ENGINE — Starting")
        logger.info(f"  LLM endpoint: {config.LITELLM_URL}")
        logger.info(f"  Reddit: {'configured' if config.REDDIT_CLIENT_ID else 'not configured'}")
        logger.info(f"  Meta Ads: {'configured' if config.META_ACCESS_TOKEN else 'not configured'}")
        logger.info(f"  Google Ads: {'configured' if config.GOOGLE_ADS_DEVELOPER_TOKEN else 'not configured'}")
        logger.info(f"  TikTok Ads: {'configured' if config.TIKTOK_ACCESS_TOKEN else 'not configured'}")
        logger.info(f"  HeyGen: {'configured' if config.HEYGEN_API_KEY else 'not configured'}")
        logger.info(f"  Pexels: {'configured' if config.PEXELS_API_KEY else 'not configured'}")
        logger.info(f"  Daily post target: {config.DAILY_POSTS_TARGET}")
        logger.info("=" * 60)

        # Initialize database
        await init_db()

        # Connect Redis
        try:
            self.redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} — continuing without pub/sub")
            self.redis = None

        self._running = True

        # Run all loops concurrently
        await asyncio.gather(
            content_loop.run(self.is_running, self.redis),
            reddit_loop.run(self.is_running, self.redis),
            ad_loop.run(self.is_running, self.redis),
            analytics_loop.run(self.is_running, self.redis),
            health_loop.run(self.is_running, self.redis),
        )

    async def stop(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self._running = False
        if self.redis:
            await self.redis.close()
        await close_db()
        logger.info("Shutdown complete")


# ── Entry Point ───────────────────────────────────────────

async def main():
    engine = MarketingEngine()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for s in (sig.SIGTERM, sig.SIGINT):
        loop.add_signal_handler(s, lambda: asyncio.create_task(engine.stop()))

    # Start FastAPI server in background
    server_config = uvicorn.Config(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info",
    )
    server = uvicorn.Server(server_config)

    # Run both the marketing engine and API server
    await asyncio.gather(
        engine.start(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
