"""
Health Heartbeat Loop
Publishes heartbeat timestamps to Redis (every 60 seconds).
"""
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("marketing-engine.health")


async def run(is_running, redis=None):
    """Health heartbeat loop — runs every 60 seconds."""
    while is_running():
        try:
            if redis:
                await redis.set(
                    "marketing:heartbeat",
                    datetime.now(timezone.utc).isoformat(),
                    ex=120,
                )
        except Exception:
            # Heartbeat failure is non-critical; Redis may be temporarily unavailable
            pass
        await asyncio.sleep(60)
