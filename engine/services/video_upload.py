"""
Video Upload — YouTube (and future platform) upload logic.
"""
import logging

import config

logger = logging.getLogger(__name__)


async def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] = None,
    category_id: str = "22",  # People & Blogs
    privacy: str = "public",
) -> dict:
    """Upload a video to YouTube via the Data API v3."""
    import httpx

    if not config.YOUTUBE_API_KEY:
        logger.warning("YouTube API not configured — skipping upload")
        return {"status": "skipped", "reason": "not_configured"}

    # Refresh OAuth token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": config.YOUTUBE_CLIENT_ID,
                "client_secret": config.YOUTUBE_CLIENT_SECRET,
                "refresh_token": config.YOUTUBE_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
        if token_resp.status_code != 200:
            return {"status": "error", "reason": "token_refresh_failed"}

        access_token = token_resp.json()["access_token"]

        # Upload video (resumable upload)
        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": (tags or [])[:30],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Step 1: Initialize upload
        init_resp = await client.post(
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json=metadata,
        )

        if init_resp.status_code != 200:
            return {"status": "error", "reason": f"init_failed: {init_resp.text[:200]}"}

        upload_url = init_resp.headers.get("Location")
        if not upload_url:
            return {"status": "error", "reason": "no_upload_url"}

        # Step 2: Upload the video file
        with open(video_path, "rb") as f:
            video_data = f.read()

        upload_resp = await client.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_data)),
            },
            content=video_data,
            timeout=600.0,
        )

        if upload_resp.status_code in (200, 201):
            data = upload_resp.json()
            video_id = data.get("id", "")
            logger.info(f"YouTube upload success: https://youtube.com/watch?v={video_id}")
            return {
                "status": "uploaded",
                "video_id": video_id,
                "url": f"https://youtube.com/watch?v={video_id}",
            }
        else:
            return {"status": "error", "reason": f"upload_failed: {upload_resp.status_code}"}
