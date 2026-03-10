"""Reddit engagement routes."""
import logging

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class RedditEngageRequest(BaseModel):
    campaign_id: str = ""
    subreddits: list[str]
    product_name: str
    product_url: str = ""
    keywords: list[str] = []
    comment_type: str = "promotional"
    max_comments: int = 5
    auto_post: bool = False


# ── Endpoints ────────────────────────────────────────────

@router.post("/reddit/discover")
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


@router.post("/reddit/engage")
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


@router.get("/reddit/engagements")
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


@router.post("/reddit/engagements/{engagement_id}/approve")
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


@router.post("/reddit/engagements/{engagement_id}/reject")
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
