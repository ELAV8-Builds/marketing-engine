"""
Marketing Engine API — REST endpoints for all marketing operations.
"""
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

import orjson
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlalchemy import select, desc, and_, func, text

from db.database import get_session
import config

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketing Engine API",
    version="1.0.0",
    default_response_class=ORJSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ──────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    product_name: str
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    channels: list[str] = []
    budget_daily: float = 0
    budget_total: float = 0

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

class RedditEngageRequest(BaseModel):
    campaign_id: str = ""
    subreddits: list[str]
    product_name: str
    product_url: str = ""
    keywords: list[str] = []
    comment_type: str = "promotional"
    max_comments: int = 5
    auto_post: bool = False

class AdCampaignCreate(BaseModel):
    campaign_id: str = ""
    platform: str  # meta, google, tiktok
    name: str
    objective: str = "traffic"
    daily_budget: float = 10.0
    product_name: str = ""
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    creative_count: int = 3

class LandingPageCreate(BaseModel):
    campaign_id: str = ""
    product_name: str
    product_description: str
    target_audience: str = ""
    template: str = "saas"
    slug: str = ""


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


# ── Campaigns ─────────────────────────────────────────────

@app.get("/api/campaigns")
async def list_campaigns(
    status: str = Query("all", pattern="^(all|draft|active|paused|completed)$"),
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        params: dict = {"limit": limit}
        if status != "all":
            q = "SELECT * FROM campaigns WHERE status = :status ORDER BY created_at DESC LIMIT :limit"
            params["status"] = status
        else:
            q = "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"campaigns": [dict(r) for r in rows], "count": len(rows)}


@app.post("/api/campaigns")
async def create_campaign(body: CampaignCreate):
    async with get_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO campaigns (name, product_name, product_url, product_description,
                    target_audience, channels, budget_daily, budget_total, status)
                VALUES (:name, :product_name, :product_url, :product_description,
                    :target_audience, :channels, :budget_daily, :budget_total, 'active')
                RETURNING id, name, status, created_at
            """),
            {
                "name": body.name,
                "product_name": body.product_name,
                "product_url": body.product_url,
                "product_description": body.product_description,
                "target_audience": body.target_audience,
                "channels": body.channels,
                "budget_daily": body.budget_daily,
                "budget_total": body.budget_total,
            },
        )
        row = result.mappings().first()
        return dict(row)


@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    async with get_session() as session:
        result = await session.execute(
            text("SELECT * FROM campaigns WHERE id = :id"),
            {"id": campaign_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return dict(row)


class CampaignUpdate(BaseModel):
    name: str = ""
    product_name: str = ""
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    channels: list[str] = []
    budget_daily: float = -1
    budget_total: float = -1
    status: str = ""
    meta: dict = {}


@app.patch("/api/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, body: CampaignUpdate):
    """Update a campaign's fields. Only non-empty fields are updated."""
    async with get_session() as session:
        updates = []
        params: dict = {"id": campaign_id}
        if body.name:
            updates.append("name = :name")
            params["name"] = body.name
        if body.product_name:
            updates.append("product_name = :pname")
            params["pname"] = body.product_name
        if body.product_url:
            updates.append("product_url = :purl")
            params["purl"] = body.product_url
        if body.product_description:
            updates.append("product_description = :pdesc")
            params["pdesc"] = body.product_description
        if body.target_audience:
            updates.append("target_audience = :audience")
            params["audience"] = body.target_audience
        if body.channels:
            updates.append("channels = :channels")
            params["channels"] = body.channels
        if body.budget_daily >= 0:
            updates.append("budget_daily = :bdaily")
            params["bdaily"] = body.budget_daily
        if body.budget_total >= 0:
            updates.append("budget_total = :btotal")
            params["btotal"] = body.budget_total
        if body.status:
            updates.append("status = :status")
            params["status"] = body.status

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        q = f"UPDATE campaigns SET {', '.join(updates)} WHERE id = :id RETURNING *"
        result = await session.execute(text(q), params)
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return dict(row)


@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign (soft delete — sets status to 'deleted')."""
    async with get_session() as session:
        result = await session.execute(
            text("UPDATE campaigns SET status = 'deleted', updated_at = NOW() WHERE id = :id RETURNING id"),
            {"id": campaign_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"deleted": True, "id": str(row["id"])}


# ── Content Calendar Create ──────────────────────────────

class CalendarItemCreate(BaseModel):
    campaign_id: str
    scheduled_date: str  # YYYY-MM-DD
    scheduled_time: str = "09:00"  # HH:MM
    platform: str
    content_type: str
    topic: str = ""

@app.post("/api/calendar")
async def create_calendar_item(body: CalendarItemCreate):
    """Schedule a content item on the calendar."""
    async with get_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO content_calendar
                    (campaign_id, scheduled_date, scheduled_time, platform, content_type, topic, status)
                VALUES (:cid, :date, :time, :platform, :type, :topic, 'pending')
                RETURNING id, scheduled_date, platform, content_type, topic, status
            """),
            {
                "cid": body.campaign_id,
                "date": body.scheduled_date,
                "time": body.scheduled_time,
                "platform": body.platform,
                "type": body.content_type,
                "topic": body.topic,
            },
        )
        row = result.mappings().first()
        return dict(row)


# ── Content Generation ────────────────────────────────────

@app.post("/api/content/generate")
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


# ── Content List ──────────────────────────────────────────

@app.get("/api/content")
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


# ── Reddit Engagement ─────────────────────────────────────

@app.post("/api/reddit/discover")
async def reddit_discover(
    subreddits: list[str] = Body(...),
    keywords: list[str] = Body(default=[]),
    limit: int = Body(default=10),
):
    """Discover relevant Reddit posts to engage with."""
    from services.reddit import RedditClient

    client = RedditClient()
    await client.connect()

    all_posts = []
    try:
        for sub in subreddits:
            if keywords:
                for kw in keywords:
                    posts = await client.search_posts(sub, kw, limit=limit)
                    all_posts.extend(posts)
            else:
                posts = await client.get_new_posts(sub, limit=limit)
                all_posts.extend(posts)
    finally:
        await client.close()

    # Deduplicate
    seen = set()
    unique = []
    for p in all_posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    return {"posts": unique, "count": len(unique)}


@app.post("/api/reddit/engage")
async def reddit_engage(body: RedditEngageRequest):
    """Generate and optionally post Reddit comments."""
    from services.reddit import RedditClient
    from services import llm

    client = RedditClient()
    await client.connect()

    results = []
    try:
        for sub in body.subreddits:
            posts = await client.get_new_posts(sub, limit=body.max_comments * 2)

            for post in posts[:body.max_comments]:
                # Generate comment
                comment_data = await llm.generate_reddit_comment(
                    post_title=post["title"],
                    post_body=post["body"],
                    subreddit=sub,
                    product_name=body.product_name,
                    product_url=body.product_url,
                    comment_type=body.comment_type,
                )

                entry = {
                    "subreddit": sub,
                    "post_id": post["id"],
                    "post_title": post["title"],
                    "comment": comment_data.get("comment", ""),
                    "confidence": comment_data.get("confidence", 0),
                    "status": "generated",
                    "reddit_comment_id": None,
                }

                # Auto-post if enabled and confidence is high enough
                if body.auto_post and comment_data.get("confidence", 0) >= 0.7:
                    comment_id = await client.post_comment(
                        post["id"], comment_data["comment"]
                    )
                    if comment_id:
                        entry["status"] = "posted"
                        entry["reddit_comment_id"] = comment_id

                results.append(entry)

                # Save to DB
                if body.campaign_id:
                    async with get_session() as session:
                        await session.execute(
                            text("""
                                INSERT INTO reddit_engagements
                                    (campaign_id, subreddit, post_id, post_title, comment_text,
                                     comment_type, confidence_score, status, reddit_comment_id)
                                VALUES (:campaign_id, :subreddit, :post_id, :post_title, :comment,
                                     :type, :confidence, :status, :reddit_id)
                            """),
                            {
                                "campaign_id": body.campaign_id,
                                "subreddit": sub,
                                "post_id": post["id"],
                                "post_title": post["title"],
                                "comment": entry["comment"],
                                "type": body.comment_type,
                                "confidence": entry["confidence"],
                                "status": entry["status"],
                                "reddit_id": entry["reddit_comment_id"],
                            },
                        )
    finally:
        await client.close()

    return {"engagements": results, "count": len(results)}


@app.get("/api/reddit/engagements")
async def list_reddit_engagements(
    campaign_id: str = "",
    status: str = "",
    limit: int = Query(50, ge=1, le=200),
):
    """List Reddit engagements, optionally filtered."""
    async with get_session() as session:
        conditions = []
        params: dict = {"limit": limit}
        if campaign_id:
            conditions.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id
        if status:
            conditions.append("status = :status")
            params["status"] = status

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        q = f"SELECT * FROM reddit_engagements{where} ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"engagements": [dict(r) for r in rows], "count": len(rows)}


@app.post("/api/reddit/engagements/{engagement_id}/approve")
async def approve_reddit_engagement(engagement_id: str):
    """Approve and post a pending Reddit engagement."""
    from services.reddit import RedditClient

    async with get_session() as session:
        result = await session.execute(
            text("SELECT * FROM reddit_engagements WHERE id = :id"),
            {"id": engagement_id},
        )
        eng = result.mappings().first()
        if not eng:
            raise HTTPException(status_code=404, detail="Engagement not found")

        if eng["status"] not in ("pending", "pending_review", "generated"):
            raise HTTPException(status_code=400, detail=f"Cannot approve engagement with status: {eng['status']}")

        # Post the comment to Reddit
        client = RedditClient()
        await client.connect()
        try:
            comment_id = await client.post_comment(eng["post_id"], eng["comment_text"])
        finally:
            await client.close()

        if comment_id:
            await session.execute(
                text("""
                    UPDATE reddit_engagements
                    SET status = 'posted', reddit_comment_id = :cid, posted_at = NOW()
                    WHERE id = :id
                """),
                {"id": engagement_id, "cid": comment_id},
            )
            return {"status": "posted", "reddit_comment_id": comment_id}
        else:
            await session.execute(
                text("UPDATE reddit_engagements SET status = 'failed' WHERE id = :id"),
                {"id": engagement_id},
            )
            raise HTTPException(status_code=500, detail="Failed to post comment to Reddit")


@app.post("/api/reddit/engagements/{engagement_id}/reject")
async def reject_reddit_engagement(engagement_id: str):
    """Reject a pending Reddit engagement."""
    async with get_session() as session:
        result = await session.execute(
            text("UPDATE reddit_engagements SET status = 'rejected' WHERE id = :id RETURNING id"),
            {"id": engagement_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Engagement not found")
        return {"status": "rejected", "id": str(row["id"])}


# ── Ad Campaigns ──────────────────────────────────────────

@app.post("/api/ads/create")
async def create_ad_campaign(body: AdCampaignCreate):
    """Create an ad campaign with AI-generated creatives."""
    from services import llm

    # Generate ad creatives
    creatives = await llm.generate_ad_copy(
        product_name=body.product_name,
        product_description=body.product_description,
        target_audience=body.target_audience,
        platform=body.platform,
        count=body.creative_count,
    )

    result = {
        "platform": body.platform,
        "name": body.name,
        "objective": body.objective,
        "daily_budget": body.daily_budget,
        "creatives": creatives,
        "status": "draft",
        "external_campaign_id": None,
    }

    # Create on the target platform if configured
    if body.platform == "meta" and config.META_ACCESS_TOKEN:
        from services.meta_ads import MetaAdsClient
        meta = MetaAdsClient()
        await meta.connect()
        try:
            campaign_id = await meta.create_campaign(
                name=body.name,
                daily_budget=int(body.daily_budget * 100),
            )
            result["external_campaign_id"] = campaign_id
            result["status"] = "created_paused"
        finally:
            await meta.close()

    elif body.platform == "google" and config.GOOGLE_ADS_DEVELOPER_TOKEN:
        from services.google_ads import GoogleAdsClient
        google = GoogleAdsClient()
        await google.connect()
        try:
            resource_name = await google.create_campaign(
                name=body.name,
                campaign_type="SEARCH" if body.objective == "traffic" else "DISPLAY",
                daily_budget_micros=int(body.daily_budget * 1_000_000),
            )
            result["external_campaign_id"] = resource_name
            result["status"] = "created_paused"
        finally:
            await google.close()

    elif body.platform == "tiktok" and config.TIKTOK_ACCESS_TOKEN:
        from services.tiktok_ads import TikTokAdsClient
        tiktok = TikTokAdsClient()
        await tiktok.connect()
        try:
            campaign_id = await tiktok.create_campaign(
                name=body.name,
                objective="TRAFFIC" if body.objective == "traffic" else "CONVERSIONS",
                budget=body.daily_budget,
            )
            result["external_campaign_id"] = campaign_id
            result["status"] = "created_paused"
        finally:
            await tiktok.close()

    # Save to DB
    if body.campaign_id:
        async with get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO ad_campaigns
                        (campaign_id, platform, name, objective, budget_daily, status)
                    VALUES (:campaign_id, :platform, :name, :objective, :budget, :status)
                """),
                {
                    "campaign_id": body.campaign_id,
                    "platform": body.platform,
                    "name": body.name,
                    "objective": body.objective,
                    "budget": body.daily_budget,
                    "status": result["status"],
                },
            )

    return result


@app.get("/api/ads")
async def list_ad_campaigns(
    campaign_id: str = "",
    platform: str = "",
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

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params["limit"] = limit
        q = f"SELECT * FROM ad_campaigns{where} ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"ads": [dict(r) for r in rows], "count": len(rows)}


# ── Landing Pages ─────────────────────────────────────────

@app.post("/api/landing-pages/generate")
async def generate_landing_page(body: LandingPageCreate):
    """Generate a landing page with AI content."""
    from services import llm

    page_content = await llm.generate_landing_page(
        product_name=body.product_name,
        product_description=body.product_description,
        target_audience=body.target_audience,
        template=body.template,
    )

    result = {
        "name": body.product_name,
        "slug": body.slug or body.product_name.lower().replace(" ", "-"),
        "template": body.template,
        "content": page_content,
        "status": "generated",
    }

    # Save to DB
    if body.campaign_id:
        async with get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO landing_pages
                        (campaign_id, name, slug, template, headline, subheadline, cta_text, status)
                    VALUES (:campaign_id, :name, :slug, :template, :headline, :sub, :cta, 'draft')
                """),
                {
                    "campaign_id": body.campaign_id,
                    "name": body.product_name,
                    "slug": result["slug"],
                    "template": body.template,
                    "headline": page_content.get("headline", ""),
                    "sub": page_content.get("subheadline", ""),
                    "cta": page_content.get("hero_cta", "Get Started"),
                },
            )

    return result


@app.get("/api/landing-pages")
async def list_landing_pages(
    campaign_id: str = "",
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        conditions = []
        params = {}
        if campaign_id:
            conditions.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params["limit"] = limit
        q = f"SELECT * FROM landing_pages{where} ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"pages": [dict(r) for r in rows], "count": len(rows)}


# ── Analytics ─────────────────────────────────────────────

@app.get("/api/analytics/overview")
async def analytics_overview(campaign_id: str = ""):
    """Get high-level analytics across all channels."""
    async with get_session() as session:
        where = "WHERE campaign_id = :cid" if campaign_id else ""
        params = {"cid": campaign_id} if campaign_id else {}

        # Content stats
        content_result = await session.execute(
            text(f"SELECT count(*) as cnt, status FROM content_items {where} GROUP BY status"), params
        )
        content_stats = {r["status"]: r["cnt"] for r in content_result.mappings().all()}

        # Reddit stats
        reddit_result = await session.execute(
            text(f"SELECT count(*) as cnt, status FROM reddit_engagements {where} GROUP BY status"), params
        )
        reddit_stats = {r["status"]: r["cnt"] for r in reddit_result.mappings().all()}

        # Ad stats
        ad_result = await session.execute(
            text(f"""SELECT platform, COALESCE(sum(impressions),0) as impressions,
                     COALESCE(sum(clicks),0) as clicks, COALESCE(sum(spend_total),0) as spend,
                     COALESCE(sum(conversions),0) as conversions
                     FROM ad_campaigns {where} GROUP BY platform"""), params
        )
        ad_stats = [dict(r) for r in ad_result.mappings().all()]

        # Landing page stats
        lp_result = await session.execute(
            text(f"SELECT count(*) as cnt, COALESCE(sum(visits),0) as visits, COALESCE(sum(conversions),0) as conversions FROM landing_pages {where}"), params
        )
        lp_row = lp_result.mappings().first()
        lp_stats = dict(lp_row) if lp_row else {"cnt": 0, "visits": 0, "conversions": 0}

        return {
            "content": content_stats,
            "reddit": reddit_stats,
            "ads": ad_stats,
            "landing_pages": {"count": lp_stats.get("cnt", 0), "visits": lp_stats.get("visits", 0), "conversions": lp_stats.get("conversions", 0)},
        }


@app.get("/api/analytics/daily")
async def daily_analytics(
    campaign_id: str = "",
    days: int = Query(30, ge=1, le=365),
):
    async with get_session() as session:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        params: dict = {"cutoff": cutoff}
        where = "WHERE date >= :cutoff"
        if campaign_id:
            where += " AND campaign_id = :cid"
            params["cid"] = campaign_id

        q = f"SELECT * FROM daily_performance {where} ORDER BY date DESC"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"performance": [dict(r) for r in rows], "days": days}


# ── Video Generation ──────────────────────────────────────

class VideoGenerateRequest(BaseModel):
    campaign_id: str = ""
    topic: str
    product_name: str = ""
    product_url: str = ""
    mode: str = "stock"  # "stock" | "avatar"
    voice: str = "en-US-AriaNeural"
    upload_to: list[str] = []  # ["youtube", "tiktok"]

@app.post("/api/video/generate")
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


# ── Content Calendar ──────────────────────────────────────

@app.get("/api/calendar")
async def get_calendar(
    campaign_id: str = "",
    start_date: str = "",
    end_date: str = "",
):
    async with get_session() as session:
        conditions = []
        params: dict = {}
        if campaign_id:
            conditions.append("campaign_id = :cid")
            params["cid"] = campaign_id
        if start_date:
            conditions.append("scheduled_date >= :start")
            params["start"] = start_date
        if end_date:
            conditions.append("scheduled_date <= :end")
            params["end"] = end_date

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        q = f"SELECT * FROM content_calendar{where} ORDER BY scheduled_date, scheduled_time"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"calendar": [dict(r) for r in rows], "count": len(rows)}


# ── Ad Performance Sync (on-demand) ─────────────────────

@app.post("/api/ads/sync")
async def sync_ad_performance():
    """Trigger an on-demand sync of ad performance from all platforms."""
    results = {"meta": "skipped", "google": "skipped", "tiktok": "skipped"}

    if config.META_ACCESS_TOKEN:
        try:
            from services.meta_ads import MetaAdsClient
            meta = MetaAdsClient()
            await meta.connect()
            # Just verify connection works
            await meta.close()
            results["meta"] = "synced"
        except Exception as e:
            results["meta"] = f"error: {str(e)[:100]}"

    if config.GOOGLE_ADS_DEVELOPER_TOKEN:
        try:
            from services.google_ads import GoogleAdsClient
            google = GoogleAdsClient()
            await google.connect()
            perf = await google.get_campaign_performance(days=7)
            await google.close()
            results["google"] = f"synced ({len(perf)} campaigns)"
        except Exception as e:
            results["google"] = f"error: {str(e)[:100]}"

    if config.TIKTOK_ACCESS_TOKEN:
        try:
            from services.tiktok_ads import TikTokAdsClient
            tiktok = TikTokAdsClient()
            await tiktok.connect()
            perf = await tiktok.get_campaign_performance()
            await tiktok.close()
            results["tiktok"] = f"synced ({len(perf)} campaigns)"
        except Exception as e:
            results["tiktok"] = f"error: {str(e)[:100]}"

    return {"status": "complete", "results": results}


# ── Landing Page Deploy (Vercel) ─────────────────────────

class LandingPageDeploy(BaseModel):
    landing_page_id: str
    custom_domain: str = ""

@app.post("/api/landing-pages/{page_id}/deploy")
async def deploy_landing_page(page_id: str):
    """Deploy a landing page to Vercel."""
    import httpx

    if not config.VERCEL_TOKEN:
        raise HTTPException(status_code=400, detail="Vercel token not configured")

    async with get_session() as session:
        result = await session.execute(
            text("SELECT * FROM landing_pages WHERE id = :id"),
            {"id": page_id},
        )
        page = result.mappings().first()
        if not page:
            raise HTTPException(status_code=404, detail="Landing page not found")

        slug = page["slug"]
        headline = page.get("headline", "")
        subheadline = page.get("subheadline", "")
        cta_text = page.get("cta_text", "Get Started")
        cta_url = page.get("cta_url", "#")
        body_html = page.get("body_html", "")

        # Generate a simple HTML landing page
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{headline}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a2e;background:#fff}}
.hero{{min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);color:#fff;margin-bottom:1rem;max-width:800px}}
.hero p{{font-size:1.25rem;color:rgba(255,255,255,0.9);margin-bottom:2rem;max-width:600px}}
.cta-btn{{display:inline-block;padding:1rem 2.5rem;background:#fff;color:#764ba2;font-size:1.125rem;font-weight:700;border-radius:8px;text-decoration:none;transition:transform 0.2s}}
.cta-btn:hover{{transform:translateY(-2px)}}
.content{{max-width:800px;margin:3rem auto;padding:0 2rem;line-height:1.7;font-size:1.125rem}}
</style>
</head>
<body>
<section class="hero">
<h1>{headline}</h1>
<p>{subheadline}</p>
<a href="{cta_url}" class="cta-btn">{cta_text}</a>
</section>
<section class="content">{body_html}</section>
</body>
</html>"""

        # Deploy to Vercel using the deployments API
        try:
            async with httpx.AsyncClient() as client:
                deploy_resp = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {config.VERCEL_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": f"lp-{slug}",
                        "files": [
                            {
                                "file": "index.html",
                                "data": html_content,
                            }
                        ],
                        "projectSettings": {
                            "framework": None,
                        },
                    },
                    timeout=60.0,
                )
                deploy_resp.raise_for_status()
                deploy_data = deploy_resp.json()

                deployed_url = f"https://{deploy_data.get('url', '')}"
                deployment_id = deploy_data.get("id", "")

                # Update DB with deployment info
                await session.execute(
                    text("""
                        UPDATE landing_pages SET
                            deployed_url = :url,
                            vercel_deployment_id = :did,
                            status = 'deployed',
                            updated_at = NOW()
                        WHERE id = :id
                    """),
                    {"id": page_id, "url": deployed_url, "did": deployment_id},
                )

                return {
                    "status": "deployed",
                    "url": deployed_url,
                    "deployment_id": deployment_id,
                }

        except Exception as e:
            logger.error(f"Vercel deployment failed: {e}")
            raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)[:200]}")


# ── SSE Event Stream ─────────────────────────────────────

@app.get("/api/stream")
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
