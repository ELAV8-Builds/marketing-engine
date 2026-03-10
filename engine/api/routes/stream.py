"""SSE event stream route."""
import logging

from fastapi import APIRouter

import config

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Endpoints ────────────────────────────────────────────

@router.get("/stream")
async def event_stream():
    """Server-Sent Events stream for real-time dashboard updates."""
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    async def generate():
        """Generate SSE events from Redis pub/sub."""
        import redis.asyncio as aioredis

        try:
            redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
            pubsub = redis.pubsub()
            await pubsub.subscribe("marketing:events")

            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Stream connected'})}\n\n"

            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
                if message and message["type"] == "message":
                    event_data = message["data"]
                    yield f"data: {json.dumps({'type': 'event', 'data': event_data})}\n\n"
                else:
                    # Send heartbeat every 30s
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:200]})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
