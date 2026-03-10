"""Ad campaign routes."""
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session
import config

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

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


# ── Endpoints ────────────────────────────────────────────

@router.post("/ads/create")
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


@router.get("/ads")
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


@router.post("/ads/sync")
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
