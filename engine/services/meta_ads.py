"""
Meta Ads Service — Create, manage, and optimize Facebook/Instagram ad campaigns.
Uses the Meta Marketing API v21.0.
"""
import logging
from typing import Optional

import httpx
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com/v21.0"


class MetaAdsClient:
    """Client for Meta (Facebook/Instagram) Ads API."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.account_id = config.META_AD_ACCOUNT_ID
        self.token = config.META_ACCESS_TOKEN

    async def connect(self):
        """Initialize the HTTP client."""
        if not self.token:
            logger.warning("META_ACCESS_TOKEN not set — skipping Meta Ads")
            return

        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            params={"access_token": self.token},
        )
        logger.info(f"Meta Ads client initialized for account {self.account_id}")

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def create_campaign(
        self,
        name: str,
        objective: str = "OUTCOME_TRAFFIC",
        daily_budget: int = 1000,  # in cents
        status: str = "PAUSED",
    ) -> Optional[str]:
        """Create a new ad campaign. Returns campaign ID."""
        if not self.client:
            return None

        try:
            resp = await self.client.post(
                f"/act_{self.account_id}/campaigns",
                data={
                    "name": name,
                    "objective": objective,
                    "status": status,
                    "special_ad_categories": "[]",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            campaign_id = data.get("id")
            logger.info(f"Created Meta campaign: {campaign_id}")
            return campaign_id
        except Exception as e:
            logger.error(f"Meta campaign creation failed: {e}")
            return None

    async def create_ad_set(
        self,
        campaign_id: str,
        name: str,
        daily_budget: int = 1000,
        targeting: dict = None,
        optimization_goal: str = "LINK_CLICKS",
        billing_event: str = "IMPRESSIONS",
        bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
    ) -> Optional[str]:
        """Create an ad set within a campaign."""
        if not self.client:
            return None

        default_targeting = {
            "geo_locations": {"countries": ["US"]},
            "age_min": 18,
            "age_max": 65,
        }

        try:
            resp = await self.client.post(
                f"/act_{self.account_id}/adsets",
                json={
                    "name": name,
                    "campaign_id": campaign_id,
                    "daily_budget": daily_budget,
                    "targeting": targeting or default_targeting,
                    "optimization_goal": optimization_goal,
                    "billing_event": billing_event,
                    "bid_strategy": bid_strategy,
                    "status": "PAUSED",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            ad_set_id = data.get("id")
            logger.info(f"Created Meta ad set: {ad_set_id}")
            return ad_set_id
        except Exception as e:
            logger.error(f"Meta ad set creation failed: {e}")
            return None

    async def create_ad_creative(
        self,
        name: str,
        page_id: str,
        headline: str,
        body: str,
        link_url: str,
        image_url: str = "",
        cta_type: str = "LEARN_MORE",
    ) -> Optional[str]:
        """Create an ad creative."""
        if not self.client:
            return None

        try:
            creative_data = {
                "name": name,
                "object_story_spec": {
                    "page_id": page_id,
                    "link_data": {
                        "message": body,
                        "link": link_url,
                        "name": headline,
                        "call_to_action": {"type": cta_type},
                    },
                },
            }

            if image_url:
                creative_data["object_story_spec"]["link_data"]["picture"] = image_url

            resp = await self.client.post(
                f"/act_{self.account_id}/adcreatives",
                json=creative_data,
            )
            resp.raise_for_status()
            data = resp.json()
            creative_id = data.get("id")
            logger.info(f"Created Meta ad creative: {creative_id}")
            return creative_id
        except Exception as e:
            logger.error(f"Meta ad creative creation failed: {e}")
            return None

    async def create_ad(
        self,
        name: str,
        ad_set_id: str,
        creative_id: str,
        status: str = "PAUSED",
    ) -> Optional[str]:
        """Create an ad using an existing creative and ad set."""
        if not self.client:
            return None

        try:
            resp = await self.client.post(
                f"/act_{self.account_id}/ads",
                data={
                    "name": name,
                    "adset_id": ad_set_id,
                    "creative": f'{{"creative_id": "{creative_id}"}}',
                    "status": status,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            ad_id = data.get("id")
            logger.info(f"Created Meta ad: {ad_id}")
            return ad_id
        except Exception as e:
            logger.error(f"Meta ad creation failed: {e}")
            return None

    async def get_campaign_insights(
        self,
        campaign_id: str,
        date_preset: str = "last_7d",
    ) -> dict:
        """Get performance insights for a campaign."""
        if not self.client:
            return {}

        try:
            resp = await self.client.get(
                f"/{campaign_id}/insights",
                params={
                    "fields": "impressions,clicks,spend,ctr,cpc,actions,cost_per_action_type",
                    "date_preset": date_preset,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            insights = data.get("data", [{}])
            return insights[0] if insights else {}
        except Exception as e:
            logger.error(f"Meta insights fetch failed: {e}")
            return {}

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> bool:
        """Update campaign status (ACTIVE, PAUSED, DELETED)."""
        if not self.client:
            return False

        try:
            resp = await self.client.post(
                f"/{campaign_id}",
                data={"status": status},
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Meta status update failed: {e}")
            return False

    async def update_budget(
        self, ad_set_id: str, daily_budget: int
    ) -> bool:
        """Update ad set daily budget (in cents)."""
        if not self.client:
            return False

        try:
            resp = await self.client.post(
                f"/{ad_set_id}",
                data={"daily_budget": daily_budget},
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Meta budget update failed: {e}")
            return False
