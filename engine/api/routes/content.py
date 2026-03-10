"""Content generation and listing routes."""
import logging

import orjson
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session
import config

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class ContentGenerate(BaseModel):
    campaign_id: str = ""
    content_type: str  # video_short, reddit_comment, ad_creative, landing_page, blog_post
    platform: str  # youtube, tiktok, instagram, reddit, meta, google, website
    topic: str = ""
    product_name: str = ""
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    params: dict = {}


# ── Endpoints ────────────────────────────────────────────

@router.post("/content/generate")
async def generate_content(body: ContentGenerate):
    """Generate content using AI. Returns content item with generated text/media."""
    from services import llm

    result = {}

    if body.content_type == "video_short":
        script = await llm.generate_video_script(
            topic=body.topic,
            product_name=body.product_name,
            product_url=body.product_url,
        )
        result = {"type": "video_script", "data": script}

    elif body.content_type == "reddit_comment":
        comment = await llm.generate_reddit_comment(
            post_title=body.params.get("post_title", ""),
            post_body=body.params.get("post_body", ""),
            subreddit=body.params.get("subreddit", ""),
            product_name=body.product_name,
            product_url=body.product_url,
            comment_type=body.params.get("comment_type", "promotional"),
        )
        result = {"type": "reddit_comment", "data": comment}

    elif body.content_type == "ad_creative":
        ads = await llm.generate_ad_copy(
            product_name=body.product_name,
            product_description=body.product_description,
            target_audience=body.target_audience,
            platform=body.platform,
            count=body.params.get("count", 3),
        )
        result = {"type": "ad_creatives", "data": ads}

    elif body.content_type == "landing_page":
        page = await llm.generate_landing_page(
            product_name=body.product_name,
            product_description=body.product_description,
            target_audience=body.target_audience,
            template=body.params.get("template", "saas"),
        )
        result = {"type": "landing_page", "data": page}

    elif body.content_type == "blog_post":
        post = await llm.generate(
            prompt=f"Write an SEO-optimized blog post about: {body.topic}\n\n"
                   f"Product to mention: {body.product_name}\n"
                   f"Target audience: {body.target_audience}\n\n"
                   f"Include a title, meta description, and the full article (800-1200 words).",
            model=config.LITELLM_CREATIVE_MODEL,
            max_tokens=3000,
        )
        result = {"type": "blog_post", "data": {"content": post}}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown content type: {body.content_type}")

    # Save to database
    if body.campaign_id and result.get("data"):
        async with get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO content_items (campaign_id, content_type, platform, title, body,
                        generation_params, status)
                    VALUES (:campaign_id, :content_type, :platform, :title, :body, :params, 'ready')
                """),
                {
                    "campaign_id": body.campaign_id,
                    "content_type": body.content_type,
                    "platform": body.platform,
                    "title": body.topic or body.product_name,
                    "body": str(result["data"])[:5000],
                    "params": orjson.dumps(body.params).decode(),
                },
            )

    return result


@router.get("/content")
async def list_content(
    campaign_id: str = "",
    platform: str = "",
    status: str = "",
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        conditions = []
        params = {}
        if campaign_id:
            conditions.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id
        if platform:
            conditions.append("platform = :platform")
            params["platform"] = platform
        if status:
            conditions.append("status = :status")
            params["status"] = status

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params["limit"] = limit
        q = f"SELECT * FROM content_items{where} ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"content": [dict(r) for r in rows], "count": len(rows)}
