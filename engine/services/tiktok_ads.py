"""
TikTok Marketing API — Campaign creation and management.
"""
import logging
from typing import Optional

import httpx
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"


class TikTokAdsClient:
    """Client for TikTok Marketing API."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.advertiser_id = config.TIKTOK_ADVERTISER_ID

    async def connect(self):
        """Initialize the HTTP client."""
        if not config.TIKTOK_ACCESS_TOKEN:
            logger.warning("TIKTOK_ACCESS_TOKEN not set — skipping TikTok Ads")
            return

        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Access-Token": config.TIKTOK_ACCESS_TOKEN,
                "Content-Type": "application/json",
            },
        )
        logger.info(f"TikTok Ads client initialized for advertiser {self.advertiser_id}")

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def create_campaign(
        self,
        name: str,
        objective: str = "TRAFFIC",
        budget: float = 50.0,
        budget_mode: str = "BUDGET_MODE_DAY",
    ) -> Optional[str]:
        """Create a TikTok ad campaign. Returns campaign_id."""
        if not self.client:
            return None

        try:
            resp = await self.client.post(
                "/campaign/create/",
                json={
                    "advertiser_id": self.advertiser_id,
                    "campaign_name": name,
                    "objective_type": objective,
                    "budget_mode": budget_mode,
                    "budget": budget,
                    "operation_status": "DISABLE",  # start paused
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                campaign_id = data["data"]["campaign_id"]
                logger.info(f"Created TikTok campaign: {campaign_id}")
                return campaign_id
            else:
                logger.error(f"TikTok campaign error: {data.get('message')}")
                return None
        except Exception as e:
            logger.error(f"TikTok campaign creation failed: {e}")
            return None

    async def get_campaign_performance(
        self,
        start_date: str = "",
        end_date: str = "",
    ) -> list[dict]:
        """Get campaign performance metrics."""
        if not self.client:
            return []

        try:
            from datetime import date, timedelta
            if not start_date:
                start_date = (date.today() - timedelta(days=7)).isoformat()
            if not end_date:
                end_date = date.today().isoformat()

            resp = await self.client.get(
                "/report/integrated/get/",
                params={
                    "advertiser_id": self.advertiser_id,
                    "service_type": "AUCTION",
                    "report_type": "BASIC",
                    "data_level": "AUCTION_CAMPAIGN",
                    "dimensions": '["campaign_id"]',
                    "metrics": '["spend","impressions","clicks","conversions","ctr","cpc","cpa"]',
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("list", [])
            return []
        except Exception as e:
            logger.error(f"TikTok performance fetch failed: {e}")
            return []

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        """Update campaign status (ENABLE/DISABLE/DELETE)."""
        if not self.client:
            return False

        try:
            resp = await self.client.post(
                "/campaign/status/update/",
                json={
                    "advertiser_id": self.advertiser_id,
                    "campaign_ids": [campaign_id],
                    "operation_status": status,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("code") == 0
        except Exception as e:
            logger.error(f"TikTok status update failed: {e}")
            return False
