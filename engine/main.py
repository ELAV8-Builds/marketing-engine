"""
Marketing Engine — Main Orchestrator
Runs the continuous marketing loops and FastAPI server.
"""
import asyncio
import logging
import sys
import signal as sig
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
import uvicorn
from sqlalchemy import text

import config
from db.database import init_db, close_db, get_session
from api.server import app

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("marketing-engine")


class MarketingEngine:
    """Main orchestrator for all marketing automation loops."""

    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self._running = False

    async def start(self):
        """Initialize services and start all loops."""
        logger.info("=" * 60)
        logger.info("MARKETING ENGINE — Starting")
        logger.info(f"  LLM endpoint: {config.LITELLM_URL}")
        logger.info(f"  Reddit: {'configured' if config.REDDIT_CLIENT_ID else 'not configured'}")
        logger.info(f"  Meta Ads: {'configured' if config.META_ACCESS_TOKEN else 'not configured'}")
        logger.info(f"  HeyGen: {'configured' if config.HEYGEN_API_KEY else 'not configured'}")
        logger.info(f"  Pexels: {'configured' if config.PEXELS_API_KEY else 'not configured'}")
        logger.info(f"  Daily post target: {config.DAILY_POSTS_TARGET}")
        logger.info("=" * 60)

        # Initialize database
        await init_db()

        # Connect Redis
        try:
            self.redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
            await self.redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} — continuing without pub/sub")
            self.redis = None

        self._running = True

        # Run all loops concurrently
        await asyncio.gather(
            self._content_generation_loop(),
            self._reddit_monitor_loop(),
            self._ad_optimization_loop(),
            self._analytics_rollup_loop(),
            self._health_heartbeat_loop(),
        )

    async def stop(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        self._running = False
        if self.redis:
            await self.redis.close()
        await close_db()
        logger.info("Shutdown complete")

    # ── Loop: Content Generation (daily) ─────────────────────

    async def _content_generation_loop(self):
        """Generate scheduled content from the content calendar."""
        await asyncio.sleep(10)  # Let services initialize
        while self._running:
            try:
                await self._generate_scheduled_content()
            except Exception as e:
                logger.error(f"Content generation loop error: {e}")
            # Check every 30 minutes
            await asyncio.sleep(30 * 60)

    async def _generate_scheduled_content(self):
        """Check content calendar for items due and generate them."""
        from services import llm

        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")

        async with get_session() as session:
            # Get pending calendar items for today
            result = await session.execute(
                text("""
                    SELECT cc.*, c.product_name, c.product_url, c.product_description,
                           c.target_audience
                    FROM content_calendar cc
                    JOIN campaigns c ON cc.campaign_id = c.id
                    WHERE cc.scheduled_date = :today
                    AND cc.status = 'pending'
                    ORDER BY cc.scheduled_time
                """),
                {"today": today},
            )
            items = result.mappings().all()

            if not items:
                logger.debug("No pending content calendar items for today")
                return

            logger.info(f"Processing {len(items)} content calendar items")

            for item in items:
                try:
                    content_type = item["content_type"]
                    platform = item["platform"]

                    if content_type == "video_short":
                        content = await llm.generate_video_script(
                            topic=item.get("topic", ""),
                            product_name=item["product_name"],
                            product_url=item.get("product_url", ""),
                        )
                    elif content_type == "blog_post":
                        content = await llm.generate(
                            prompt=(
                                f"Write an SEO-optimized blog post about: {item.get('topic', '')}\n"
                                f"Product: {item['product_name']}\n"
                                f"Target audience: {item.get('target_audience', '')}\n"
                                "Include title, meta description, and full article (800-1200 words)."
                            ),
                            model=config.LITELLM_CREATIVE_MODEL,
                            max_tokens=3000,
                        )
                        content = {"content": content}
                    elif content_type == "ad_creative":
                        content = await llm.generate_ad_copy(
                            product_name=item["product_name"],
                            product_description=item.get("product_description", ""),
                            target_audience=item.get("target_audience", ""),
                            platform=platform,
                        )
                    else:
                        content = {"raw": await llm.generate(
                            prompt=f"Generate {content_type} content for {platform}: {item.get('topic', '')}",
                        )}

                    # Save content item
                    await session.execute(
                        text("""
                            INSERT INTO content_items
                                (campaign_id, content_type, platform, title, body, status)
                            VALUES (:campaign_id, :type, :platform, :title, :body, 'ready')
                        """),
                        {
                            "campaign_id": item["campaign_id"],
                            "type": content_type,
                            "platform": platform,
                            "title": item.get("topic", item["product_name"]),
                            "body": str(content)[:5000],
                        },
                    )

                    # Mark calendar item as completed
                    await session.execute(
                        text("UPDATE content_calendar SET status = 'completed' WHERE id = :id"),
                        {"id": item["id"]},
                    )

                    logger.info(f"Generated {content_type} for {platform}: {item.get('topic', 'untitled')}")

                    # Publish event via Redis
                    if self.redis:
                        await self.redis.publish(
                            "marketing:events",
                            f"content_generated:{content_type}:{platform}",
                        )

                except Exception as e:
                    logger.error(f"Failed to generate content item {item['id']}: {e}")
                    await session.execute(
                        text("UPDATE content_calendar SET status = 'failed' WHERE id = :id"),
                        {"id": item["id"]},
                    )

    # ── Loop: Reddit Monitoring (every 30 min) ───────────────

    async def _reddit_monitor_loop(self):
        """Monitor subreddits for engagement opportunities."""
        await asyncio.sleep(20)
        if not config.REDDIT_CLIENT_ID:
            logger.info("Reddit not configured — skipping monitor loop")
            return

        while self._running:
            try:
                await self._scan_reddit()
            except Exception as e:
                logger.error(f"Reddit monitor loop error: {e}")
            await asyncio.sleep(config.REDDIT_CHECK_INTERVAL_MINUTES * 60)

    async def _scan_reddit(self):
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

    # ── Loop: Ad Optimization (every 6 hours) ────────────────

    async def _ad_optimization_loop(self):
        """Optimize ad campaigns by shifting budget to winners."""
        await asyncio.sleep(60)
        if not config.META_ACCESS_TOKEN:
            logger.info("Meta Ads not configured — skipping optimization loop")
            return

        while self._running:
            try:
                await self._optimize_ads()
            except Exception as e:
                logger.error(f"Ad optimization loop error: {e}")
            await asyncio.sleep(config.AD_OPTIMIZE_INTERVAL_HOURS * 3600)

    async def _optimize_ads(self):
        """Pull ad performance and optimize budgets."""
        from services.meta_ads import MetaAdsClient

        async with get_session() as session:
            # Get active Meta ad campaigns
            result = await session.execute(
                text("""
                    SELECT * FROM ad_campaigns
                    WHERE platform = 'meta' AND status = 'active'
                    AND external_campaign_id IS NOT NULL
                """)
            )
            campaigns = result.mappings().all()

            if not campaigns:
                return

            meta = MetaAdsClient()
            await meta.connect()

            try:
                for campaign in campaigns:
                    ext_id = campaign["external_campaign_id"]

                    # Get insights
                    insights = await meta.get_campaign_insights(ext_id, date_preset="last_7d")
                    if not insights:
                        continue

                    # Update local stats
                    total_impressions = sum(i.get("impressions", 0) for i in insights)
                    total_clicks = sum(i.get("clicks", 0) for i in insights)
                    total_spend = sum(float(i.get("spend", 0)) for i in insights)
                    total_conversions = sum(
                        sum(a.get("value", 0) for a in i.get("actions", [])
                            if a.get("action_type") == "purchase")
                        for i in insights
                    )

                    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

                    await session.execute(
                        text("""
                            UPDATE ad_campaigns SET
                                impressions = :impressions,
                                clicks = :clicks,
                                spend_total = :spend,
                                conversions = :conversions,
                                ctr = :ctr,
                                cpc = :cpc,
                                last_synced_at = NOW()
                            WHERE id = :id
                        """),
                        {
                            "id": campaign["id"],
                            "impressions": total_impressions,
                            "clicks": total_clicks,
                            "spend": total_spend,
                            "conversions": total_conversions,
                            "ctr": ctr,
                            "cpc": cpc,
                        },
                    )

                    logger.info(
                        f"Ad sync: {campaign['name']} — "
                        f"{total_impressions} impressions, {total_clicks} clicks, "
                        f"${total_spend:.2f} spend, CTR: {ctr:.2f}%"
                    )

                    # Auto-pause low performers (CTR < 0.5% after 1000+ impressions)
                    if total_impressions >= 1000 and ctr < 0.5:
                        logger.warning(
                            f"Low CTR for {campaign['name']}: {ctr:.2f}% — consider pausing"
                        )

            finally:
                await meta.close()

    # ── Loop: Analytics Rollup (daily) ───────────────────────

    async def _analytics_rollup_loop(self):
        """Roll up daily performance metrics."""
        await asyncio.sleep(120)
        while self._running:
            try:
                await self._rollup_daily_metrics()
            except Exception as e:
                logger.error(f"Analytics rollup error: {e}")
            # Run once per hour
            await asyncio.sleep(3600)

    async def _rollup_daily_metrics(self):
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

    # ── Loop: Health Heartbeat (every 60s) ───────────────────

    async def _health_heartbeat_loop(self):
        """Log heartbeat and publish health status."""
        while self._running:
            try:
                if self.redis:
                    await self.redis.set(
                        "marketing:heartbeat",
                        datetime.now(timezone.utc).isoformat(),
                        ex=120,
                    )
            except Exception:
                pass
            await asyncio.sleep(60)


# ── Entry Point ───────────────────────────────────────────

async def main():
    engine = MarketingEngine()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for s in (sig.SIGTERM, sig.SIGINT):
        loop.add_signal_handler(s, lambda: asyncio.create_task(engine.stop()))

    # Start FastAPI server in background
    server_config = uvicorn.Config(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="info",
    )
    server = uvicorn.Server(server_config)

    # Run both the marketing engine and API server
    await asyncio.gather(
        engine.start(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
