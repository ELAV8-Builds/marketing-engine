"""
Reddit Monitoring Loop
Scans subreddits for engagement opportunities (checks every N minutes, configurable).
"""
import asyncio
import logging

from sqlalchemy import text

import config
from db.database import get_session

logger = logging.getLogger("marketing-engine.reddit")


async def run(is_running, redis=None):
    """Reddit monitoring loop — runs at configured interval."""
    await asyncio.sleep(20)  # Let services initialize
    if not config.REDDIT_CLIENT_ID:
        logger.info("Reddit not configured — skipping monitor loop")
        return

    while is_running():
        try:
            await _scan_reddit()
        except Exception as e:
            logger.error(f"Reddit monitor loop error: {e}")
        await asyncio.sleep(config.REDDIT_CHECK_INTERVAL_MINUTES * 60)


async def _scan_reddit():
    """Scan active campaigns for Reddit engagement opportunities."""
    from services.reddit import RedditClient
    from services import llm

    async with get_session() as session:
        # Get active campaigns with Reddit channel
        result = await session.execute(
            text("""
                SELECT * FROM campaigns
                WHERE status = 'active'
                AND 'reddit' = ANY(channels)
            """)
        )
        campaigns = result.mappings().all()

        if not campaigns:
            return

        client = RedditClient()
        await client.connect()

        try:
            for campaign in campaigns:
                # Get configured subreddits from campaign metadata
                subreddits = campaign.get("meta", {}).get("subreddits", [])
                if not subreddits:
                    continue

                keywords = campaign.get("meta", {}).get("keywords", [])

                for sub in subreddits:
                    posts = await client.get_new_posts(sub, limit=5)

                    for post in posts:
                        # Check if we already engaged with this post
                        existing = await session.execute(
                            text("""
                                SELECT id FROM reddit_engagements
                                WHERE post_id = :post_id AND campaign_id = :campaign_id
                            """),
                            {"post_id": post["id"], "campaign_id": campaign["id"]},
                        )
                        if existing.first():
                            continue

                        # Check keyword relevance
                        if keywords:
                            title_lower = post["title"].lower()
                            body_lower = (post.get("body", "") or "").lower()
                            relevant = any(
                                kw.lower() in title_lower or kw.lower() in body_lower
                                for kw in keywords
                            )
                            if not relevant:
                                continue

                        # Generate comment
                        comment_data = await llm.generate_reddit_comment(
                            post_title=post["title"],
                            post_body=post.get("body", ""),
                            subreddit=sub,
                            product_name=campaign["product_name"],
                            product_url=campaign.get("product_url", ""),
                            comment_type="promotional",
                        )

                        # Store (don't auto-post by default)
                        await session.execute(
                            text("""
                                INSERT INTO reddit_engagements
                                    (campaign_id, subreddit, post_id, post_title,
                                     comment_text, comment_type, confidence_score, status)
                                VALUES (:cid, :sub, :pid, :title, :comment, 'promotional',
                                        :confidence, 'pending_review')
                            """),
                            {
                                "cid": campaign["id"],
                                "sub": sub,
                                "pid": post["id"],
                                "title": post["title"],
                                "comment": comment_data.get("comment", ""),
                                "confidence": comment_data.get("confidence", 0),
                            },
                        )

                        logger.info(
                            f"Reddit: Generated comment for r/{sub} post '{post['title'][:50]}' "
                            f"(confidence: {comment_data.get('confidence', 0):.2f})"
                        )

        finally:
            await client.close()
