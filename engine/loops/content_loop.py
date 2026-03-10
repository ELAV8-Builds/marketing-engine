"""
Content Generation Loop
Generates scheduled content from the content calendar (checks every 30 minutes).
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import text

import config
from db.database import get_session

logger = logging.getLogger("marketing-engine.content")


async def run(is_running, redis=None):
    """Content generation loop — runs every 30 minutes."""
    await asyncio.sleep(10)  # Let services initialize
    while is_running():
        try:
            await _generate_scheduled_content(redis)
        except Exception as e:
            logger.error(f"Content generation loop error: {e}")
        await asyncio.sleep(30 * 60)


async def _generate_scheduled_content(redis=None):
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
                if redis:
                    await redis.publish(
                        "marketing:events",
                        f"content_generated:{content_type}:{platform}",
                    )

            except Exception as e:
                logger.error(f"Failed to generate content item {item['id']}: {e}")
                await session.execute(
                    text("UPDATE content_calendar SET status = 'failed' WHERE id = :id"),
                    {"id": item["id"]},
                )
