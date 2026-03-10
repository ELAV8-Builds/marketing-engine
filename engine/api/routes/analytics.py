"""Analytics routes."""
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Endpoints ────────────────────────────────────────────

@router.get("/analytics/overview")
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


@router.get("/analytics/daily")
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
