"""
Ad Optimization Loop
Pulls ad performance from Meta, Google, and TikTok platforms (every N hours, configurable).
"""
import asyncio
import logging

from sqlalchemy import text

import config
from db.database import get_session

logger = logging.getLogger("marketing-engine.ads")


async def run(is_running, redis=None):
    """Ad optimization loop — runs at configured interval."""
    await asyncio.sleep(60)  # Let services initialize
    has_any_ads = (
        config.META_ACCESS_TOKEN
        or config.GOOGLE_ADS_DEVELOPER_TOKEN
        or config.TIKTOK_ACCESS_TOKEN
    )
    if not has_any_ads:
        logger.info("No ad platforms configured — skipping optimization loop")
        return

    while is_running():
        try:
            await _optimize_ads()
        except Exception as e:
            logger.error(f"Ad optimization loop error: {e}")
        await asyncio.sleep(config.AD_OPTIMIZE_INTERVAL_HOURS * 3600)


async def _optimize_ads():
    """Pull ad performance from all platforms and update local stats."""
    await _sync_meta_ads()
    await _sync_google_ads()
    await _sync_tiktok_ads()


# ── Meta Ads ──────────────────────────────────────────────


async def _sync_meta_ads():
    """Sync Meta Ads campaign performance."""
    if not config.META_ACCESS_TOKEN:
        return

    from services.meta_ads import MetaAdsClient

    async with get_session() as session:
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
                insights = await meta.get_campaign_insights(ext_id, date_preset="last_7d")
                if not insights:
                    continue

                total_impressions = sum(i.get("impressions", 0) for i in insights) if isinstance(insights, list) else int(insights.get("impressions", 0))
                total_clicks = sum(i.get("clicks", 0) for i in insights) if isinstance(insights, list) else int(insights.get("clicks", 0))
                total_spend = sum(float(i.get("spend", 0)) for i in insights) if isinstance(insights, list) else float(insights.get("spend", 0))
                total_conversions = 0
                if isinstance(insights, list):
                    for i in insights:
                        for a in i.get("actions", []):
                            if a.get("action_type") == "purchase":
                                total_conversions += int(a.get("value", 0))
                elif isinstance(insights, dict):
                    for a in insights.get("actions", []):
                        if a.get("action_type") == "purchase":
                            total_conversions += int(a.get("value", 0))

                ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

                await _update_ad_stats(
                    session, campaign["id"],
                    total_impressions, total_clicks, total_spend, total_conversions, ctr, cpc,
                )

                logger.info(
                    f"Meta sync: {campaign['name']} — "
                    f"{total_impressions} imp, {total_clicks} clicks, ${total_spend:.2f}"
                )

                if total_impressions >= 1000 and ctr < 0.5:
                    logger.warning(f"Low CTR for {campaign['name']}: {ctr:.2f}%")
        finally:
            await meta.close()


# ── Google Ads ────────────────────────────────────────────


async def _sync_google_ads():
    """Sync Google Ads campaign performance."""
    if not config.GOOGLE_ADS_DEVELOPER_TOKEN:
        return

    from services.google_ads import GoogleAdsClient

    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT * FROM ad_campaigns
                WHERE platform = 'google' AND status = 'active'
                AND external_campaign_id IS NOT NULL
            """)
        )
        campaigns = result.mappings().all()
        if not campaigns:
            return

        google = GoogleAdsClient()
        await google.connect()

        try:
            perf = await google.get_campaign_performance(days=7)
            for campaign in campaigns:
                # Match by external_campaign_id
                for row in perf:
                    camp_data = row.get("campaign", {})
                    metrics = row.get("metrics", {})
                    if str(camp_data.get("id")) in str(campaign["external_campaign_id"]):
                        impressions = int(metrics.get("impressions", 0))
                        clicks = int(metrics.get("clicks", 0))
                        spend = int(metrics.get("costMicros", 0)) / 1_000_000
                        conversions = int(float(metrics.get("conversions", 0)))
                        ctr = float(metrics.get("ctr", 0)) * 100
                        cpc = int(metrics.get("averageCpc", 0)) / 1_000_000

                        await _update_ad_stats(
                            session, campaign["id"],
                            impressions, clicks, spend, conversions, ctr, cpc,
                        )
                        logger.info(f"Google sync: {campaign['name']} — {impressions} imp, {clicks} clicks")
                        break
        finally:
            await google.close()


# ── TikTok Ads ────────────────────────────────────────────


async def _sync_tiktok_ads():
    """Sync TikTok Ads campaign performance."""
    if not config.TIKTOK_ACCESS_TOKEN:
        return

    from services.tiktok_ads import TikTokAdsClient

    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT * FROM ad_campaigns
                WHERE platform = 'tiktok' AND status = 'active'
                AND external_campaign_id IS NOT NULL
            """)
        )
        campaigns = result.mappings().all()
        if not campaigns:
            return

        tiktok = TikTokAdsClient()
        await tiktok.connect()

        try:
            perf = await tiktok.get_campaign_performance()
            for campaign in campaigns:
                for row in perf:
                    dims = row.get("dimensions", {})
                    metrics = row.get("metrics", {})
                    if str(dims.get("campaign_id")) == str(campaign["external_campaign_id"]):
                        impressions = int(metrics.get("impressions", 0))
                        clicks = int(metrics.get("clicks", 0))
                        spend = float(metrics.get("spend", 0))
                        conversions = int(metrics.get("conversions", 0))
                        ctr = float(metrics.get("ctr", 0)) * 100
                        cpc = float(metrics.get("cpc", 0))

                        await _update_ad_stats(
                            session, campaign["id"],
                            impressions, clicks, spend, conversions, ctr, cpc,
                        )
                        logger.info(f"TikTok sync: {campaign['name']} — {impressions} imp, {clicks} clicks")
                        break
        finally:
            await tiktok.close()


# ── Shared helper ─────────────────────────────────────────


async def _update_ad_stats(
    session, campaign_id,
    impressions: int, clicks: int, spend: float,
    conversions: int, ctr: float, cpc: float,
):
    """Update ad campaign stats in the database."""
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
            "id": campaign_id,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "conversions": conversions,
            "ctr": ctr,
            "cpc": cpc,
        },
    )
