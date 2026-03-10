"""
Analytics Rollup Loop
Calculates daily performance metrics from raw data (runs every hour).
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger("marketing-engine.analytics")


async def run(is_running, redis=None):
    """Analytics rollup loop — runs once per hour."""
    await asyncio.sleep(120)  # Let services initialize
    while is_running():
        try:
            await _rollup_daily_metrics()
        except Exception as e:
            logger.error(f"Analytics rollup error: {e}")
        await asyncio.sleep(3600)


async def _rollup_daily_metrics():
    """Calculate daily performance from raw data."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async with get_session() as session:
        # Content metrics
        content_result = await session.execute(
            text("""
                SELECT campaign_id, platform, count(*) as items
                FROM content_items
                WHERE DATE(created_at) = :today AND status IN ('ready', 'published')
                GROUP BY campaign_id, platform
            """),
            {"today": today},
        )

        for row in content_result.mappings().all():
            await session.execute(
                text("""
                    INSERT INTO daily_performance (campaign_id, date, platform, content_generated)
                    VALUES (:cid, :date, :platform, :items)
                    ON CONFLICT (campaign_id, date, platform)
                    DO UPDATE SET content_generated = EXCLUDED.content_generated
                """),
                {
                    "cid": row["campaign_id"],
                    "date": today,
                    "platform": row["platform"],
                    "items": row["items"],
                },
            )

        # Reddit metrics
        reddit_result = await session.execute(
            text("""
                SELECT campaign_id, count(*) as comments,
                       sum(upvotes) as upvotes,
                       count(CASE WHEN status = 'posted' THEN 1 END) as posted
                FROM reddit_engagements
                WHERE DATE(created_at) = :today
                GROUP BY campaign_id
            """),
            {"today": today},
        )

        for row in reddit_result.mappings().all():
            await session.execute(
                text("""
                    INSERT INTO daily_performance
                        (campaign_id, date, platform, reddit_comments, reddit_upvotes)
                    VALUES (:cid, :date, 'reddit', :comments, :upvotes)
                    ON CONFLICT (campaign_id, date, platform)
                    DO UPDATE SET
                        reddit_comments = EXCLUDED.reddit_comments,
                        reddit_upvotes = EXCLUDED.reddit_upvotes
                """),
                {
                    "cid": row["campaign_id"],
                    "date": today,
                    "comments": row["comments"],
                    "upvotes": row["upvotes"] or 0,
                },
            )

        logger.debug(f"Daily metrics rolled up for {today}")
