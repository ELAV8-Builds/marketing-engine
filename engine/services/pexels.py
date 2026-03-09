"""
Pexels API — Free stock video and image sourcing.
"""
import logging
import httpx
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.pexels.com"


async def search_videos(
    query: str,
    per_page: int = 5,
    orientation: str = "portrait",
    min_duration: int = 5,
    max_duration: int = 30,
) -> list[dict]:
    """Search for stock videos on Pexels."""
    if not config.PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY not set — skipping video search")
        return []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/videos/search",
                params={
                    "query": query,
                    "per_page": per_page,
                    "orientation": orientation,
                    "size": "medium",
                },
                headers={"Authorization": config.PEXELS_API_KEY},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

            videos = []
            for v in data.get("videos", []):
                duration = v.get("duration", 0)
                if duration < min_duration or duration > max_duration:
                    continue

                # Get the best quality file that's not too large
                best_file = None
                for vf in v.get("video_files", []):
                    if vf.get("quality") == "hd" and vf.get("width", 0) <= 1920:
                        best_file = vf
                        break
                if not best_file and v.get("video_files"):
                    best_file = v["video_files"][0]

                if best_file:
                    videos.append({
                        "id": v["id"],
                        "url": best_file["link"],
                        "width": best_file.get("width", 0),
                        "height": best_file.get("height", 0),
                        "duration": duration,
                        "query": query,
                    })

            return videos

    except Exception as e:
        logger.error(f"Pexels video search failed: {e}")
        return []


async def search_images(
    query: str,
    per_page: int = 5,
    orientation: str = "landscape",
) -> list[dict]:
    """Search for stock images on Pexels."""
    if not config.PEXELS_API_KEY:
        return []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/v1/search",
                params={
                    "query": query,
                    "per_page": per_page,
                    "orientation": orientation,
                },
                headers={"Authorization": config.PEXELS_API_KEY},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

            images = []
            for photo in data.get("photos", []):
                images.append({
                    "id": photo["id"],
                    "url": photo["src"]["large2x"],
                    "url_medium": photo["src"]["medium"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "alt": photo.get("alt", query),
                })

            return images

    except Exception as e:
        logger.error(f"Pexels image search failed: {e}")
        return []


async def download_video(url: str, output_path: str) -> bool:
    """Download a video file from Pexels."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        logger.error(f"Video download failed: {e}")
        return False
