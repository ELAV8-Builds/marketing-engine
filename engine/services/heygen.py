"""
HeyGen API — AI avatar video generation.
"""
import logging
import asyncio
from typing import Optional

import httpx
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.heygen.com"


class HeyGenClient:
    """Client for HeyGen video generation API."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        if not config.HEYGEN_API_KEY:
            logger.warning("HEYGEN_API_KEY not set — avatar videos unavailable")
            return

        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=60.0,
            headers={"X-Api-Key": config.HEYGEN_API_KEY},
        )
        logger.info("HeyGen client initialized")

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def list_avatars(self) -> list[dict]:
        """List available avatars."""
        if not self.client:
            return []

        try:
            resp = await self.client.get("/v2/avatars")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("avatars", [])
        except Exception as e:
            logger.error(f"HeyGen list avatars failed: {e}")
            return []

    async def list_voices(self) -> list[dict]:
        """List available voices."""
        if not self.client:
            return []

        try:
            resp = await self.client.get("/v2/voices")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("voices", [])
        except Exception as e:
            logger.error(f"HeyGen list voices failed: {e}")
            return []

    async def create_video(
        self,
        script: str,
        avatar_id: str = "Daisy-inskirt-20220818",
        voice_id: str = "en-US-JennyNeural",
        aspect_ratio: str = "9:16",  # Portrait for shorts
        test: bool = False,
    ) -> Optional[str]:
        """Create an avatar video. Returns video_id for polling."""
        if not self.client:
            return None

        try:
            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": avatar_id,
                            "avatar_style": "normal",
                        },
                        "voice": {
                            "type": "text",
                            "input_text": script,
                            "voice_id": voice_id,
                        },
                    }
                ],
                "dimension": {
                    "width": 1080 if aspect_ratio == "9:16" else 1920,
                    "height": 1920 if aspect_ratio == "9:16" else 1080,
                },
                "test": test,
            }

            resp = await self.client.post("/v2/video/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            video_id = data.get("data", {}).get("video_id")
            logger.info(f"HeyGen video creation started: {video_id}")
            return video_id
        except Exception as e:
            logger.error(f"HeyGen video creation failed: {e}")
            return None

    async def get_video_status(self, video_id: str) -> dict:
        """Check video generation status."""
        if not self.client:
            return {}

        try:
            resp = await self.client.get(f"/v1/video_status.get?video_id={video_id}")
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"HeyGen status check failed: {e}")
            return {}

    async def wait_for_video(
        self, video_id: str, timeout: int = 600, poll_interval: int = 10
    ) -> Optional[str]:
        """Poll until video is ready. Returns video URL."""
        elapsed = 0
        while elapsed < timeout:
            status = await self.get_video_status(video_id)
            state = status.get("status", "")

            if state == "completed":
                url = status.get("video_url")
                logger.info(f"HeyGen video ready: {url}")
                return url
            elif state == "failed":
                logger.error(f"HeyGen video failed: {status.get('error')}")
                return None

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.error(f"HeyGen video timed out after {timeout}s")
        return None
