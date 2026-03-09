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
        "services": {
            "reddit": bool(config.REDDIT_CLIENT_ID),
            "meta_ads": bool(config.META_ACCESS_TOKEN),
            "heygen": bool(config.HEYGEN_API_KEY),
            "pexels": bool(config.PEXELS_API_KEY),
        },
    }


# ── Campaigns ─────────────────────────────────────────────

@app.get("/api/campaigns")
async def list_campaigns(
    status: str = Query("all", pattern="^(all|draft|active|paused|completed)$"),
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        q = "SELECT * FROM campaigns ORDER BY created_at DESC"
        if status != "all":
            q = f"SELECT * FROM campaigns WHERE status = '{status}' ORDER BY created_at DESC"
        q += f" LIMIT {limit}"
        result = await session.execute(text(q))
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
        q = f"SELECT * FROM content_items{where} ORDER BY created_at DESC LIMIT {limit}"
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

    # Create on Meta if configured
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
        q = f"SELECT * FROM ad_campaigns{where} ORDER BY created_at DESC LIMIT {limit}"
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
        q = f"SELECT * FROM landing_pages{where} ORDER BY created_at DESC LIMIT {limit}"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"pages": [dict(r) for r in rows], "count": len(rows)}


# ── Analytics ─────────────────────────────────────────────

@app.get("/api/analytics/overview")
async def analytics_overview(campaign_id: str = ""):
    """Get high-level analytics across all channels."""
    async with get_session() as session:
        where = f"WHERE campaign_id = '{campaign_id}'" if campaign_id else ""

        # Content stats
        content_q = f"SELECT count(*), status FROM content_items {where} GROUP BY status"
        content_result = await session.execute(text(content_q))
        content_stats = {r["status"]: r["count"] for r in content_result.mappings().all()}

        # Reddit stats
        reddit_q = f"SELECT count(*), status FROM reddit_engagements {where} GROUP BY status"
        reddit_result = await session.execute(text(reddit_q))
        reddit_stats = {r["status"]: r["count"] for r in reddit_result.mappings().all()}

        # Ad stats
        ad_q = f"""SELECT platform, sum(impressions) as impressions, sum(clicks) as clicks,
                   sum(spend_total) as spend, sum(conversions) as conversions
                   FROM ad_campaigns {where} GROUP BY platform"""
        ad_result = await session.execute(text(ad_q))
        ad_stats = [dict(r) for r in ad_result.mappings().all()]

        # Landing page stats
        lp_q = f"SELECT count(*), sum(visits) as visits, sum(conversions) as conversions FROM landing_pages {where}"
        lp_result = await session.execute(text(lp_q))
        lp_stats = dict(lp_result.mappings().first() or {})

        return {
            "content": content_stats,
            "reddit": reddit_stats,
            "ads": ad_stats,
            "landing_pages": lp_stats,
        }


@app.get("/api/analytics/daily")
async def daily_analytics(
    campaign_id: str = "",
    days: int = Query(30, ge=1, le=365),
):
    async with get_session() as session:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        where = f"WHERE date >= '{cutoff}'"
        if campaign_id:
            where += f" AND campaign_id = '{campaign_id}'"

        q = f"SELECT * FROM daily_performance {where} ORDER BY date DESC"
        result = await session.execute(text(q))
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
        if campaign_id:
            conditions.append(f"campaign_id = '{campaign_id}'")
        if start_date:
            conditions.append(f"scheduled_date >= '{start_date}'")
        if end_date:
            conditions.append(f"scheduled_date <= '{end_date}'")

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        q = f"SELECT * FROM content_calendar{where} ORDER BY scheduled_date, scheduled_time"
        result = await session.execute(text(q))
        rows = result.mappings().all()
        return {"calendar": [dict(r) for r in rows], "count": len(rows)}
