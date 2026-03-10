"""Video generation routes."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class VideoGenerateRequest(BaseModel):
    campaign_id: str = ""
    topic: str
    product_name: str = ""
    product_url: str = ""
    mode: str = "stock"  # "stock" | "avatar"
    voice: str = "en-US-AriaNeural"
    upload_to: list[str] = []  # ["youtube", "tiktok"]


# ── Endpoints ────────────────────────────────────────────

@router.post("/video/generate")
async def generate_video(body: VideoGenerateRequest):
    """Generate a faceless video from a topic."""
    from services import llm
    from services.video import generate_faceless_video, upload_to_youtube

    # Step 1: Generate script
    script = await llm.generate_video_script(
        topic=body.topic,
        product_name=body.product_name,
        product_url=body.product_url,
    )

    if not script or not script.get("scenes"):
        raise HTTPException(status_code=500, detail="Failed to generate video script")

    # Step 2: Generate video
    result = await generate_faceless_video(
        script=script,
        voice=body.voice,
        mode=body.mode,
    )

    # Step 3: Upload if requested
    uploads = {}
    if "youtube" in body.upload_to and result.get("video_path"):
        yt_result = await upload_to_youtube(
            video_path=result["video_path"],
            title=result.get("title", body.topic),
            description=result.get("description", ""),
            tags=result.get("tags", []),
        )
        uploads["youtube"] = yt_result

    result["uploads"] = uploads

    # Save to DB
    if body.campaign_id:
        async with get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO content_items
                        (campaign_id, content_type, platform, title, body, media_url, status)
                    VALUES (:cid, 'video_short', 'youtube', :title, :desc, :url, :status)
                """),
                {
                    "cid": body.campaign_id,
                    "title": result.get("title", body.topic),
                    "desc": result.get("description", ""),
                    "url": result.get("video_path", result.get("video_url", "")),
                    "status": "published" if uploads.get("youtube", {}).get("status") == "uploaded" else "ready",
                },
            )

    return result
