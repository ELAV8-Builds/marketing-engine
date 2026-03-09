"""
Google Ads Service — Campaign creation, management, and optimization.
Uses the Google Ads API REST interface.
"""
import logging
from typing import Optional

import httpx
import config

logger = logging.getLogger(__name__)

BASE_URL = "https://googleads.googleapis.com/v17"


class GoogleAdsClient:
    """Client for Google Ads API."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.customer_id = config.GOOGLE_ADS_CUSTOMER_ID
        self.developer_token = config.GOOGLE_ADS_DEVELOPER_TOKEN
        self.access_token: Optional[str] = None

    async def connect(self):
        """Initialize the HTTP client and refresh OAuth token."""
        if not self.developer_token:
            logger.warning("GOOGLE_ADS_DEVELOPER_TOKEN not set — skipping Google Ads")
            return

        # Refresh OAuth2 token
        try:
            async with httpx.AsyncClient() as temp_client:
                token_resp = await temp_client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": config.GOOGLE_ADS_CLIENT_ID,
                        "client_secret": config.GOOGLE_ADS_CLIENT_SECRET,
                        "refresh_token": config.GOOGLE_ADS_REFRESH_TOKEN,
                        "grant_type": "refresh_token",
                    },
                )
                if token_resp.status_code == 200:
                    self.access_token = token_resp.json()["access_token"]
                else:
                    logger.error(f"Google Ads OAuth refresh failed: {token_resp.text[:200]}")
                    return
        except Exception as e:
            logger.error(f"Google Ads OAuth error: {e}")
            return

        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "developer-token": self.developer_token,
                "Content-Type": "application/json",
            },
        )
        logger.info(f"Google Ads client initialized for customer {self.customer_id}")

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def search(self, query: str) -> list[dict]:
        """Execute a GAQL (Google Ads Query Language) search."""
        if not self.client:
            return []

        try:
            resp = await self.client.post(
                f"/customers/{self.customer_id}/googleAds:searchStream",
                json={"query": query},
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for batch in data:
                results.extend(batch.get("results", []))
            return results
        except Exception as e:
            logger.error(f"Google Ads search failed: {e}")
            return []

    async def create_campaign(
        self,
        name: str,
        campaign_type: str = "SEARCH",
        daily_budget_micros: int = 10_000_000,  # $10.00
        status: str = "PAUSED",
    ) -> Optional[str]:
        """Create a Google Ads campaign. Returns resource name."""
        if not self.client:
            return None

        try:
            # First create a budget
            budget_resp = await self.client.post(
                f"/customers/{self.customer_id}/campaignBudgets:mutate",
                json={
                    "operations": [{
                        "create": {
                            "name": f"Budget for {name}",
                            "amountMicros": str(daily_budget_micros),
                            "deliveryMethod": "STANDARD",
                        }
                    }]
                },
            )
            budget_resp.raise_for_status()
            budget_resource = budget_resp.json()["results"][0]["resourceName"]

            # Then create the campaign
            campaign_resp = await self.client.post(
                f"/customers/{self.customer_id}/campaigns:mutate",
                json={
                    "operations": [{
                        "create": {
                            "name": name,
                            "advertisingChannelType": campaign_type,
                            "status": status,
                            "campaignBudget": budget_resource,
                            "manualCpc": {},
                        }
                    }]
                },
            )
            campaign_resp.raise_for_status()
            resource_name = campaign_resp.json()["results"][0]["resourceName"]
            logger.info(f"Created Google Ads campaign: {resource_name}")
            return resource_name
        except Exception as e:
            logger.error(f"Google Ads campaign creation failed: {e}")
            return None

    async def get_campaign_performance(
        self, days: int = 7
    ) -> list[dict]:
        """Get campaign performance for the last N days."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc
            FROM campaign
            WHERE segments.date DURING LAST_{days}_DAYS
            ORDER BY metrics.impressions DESC
        """
        return await self.search(query)

    async def update_campaign_status(
        self, campaign_resource_name: str, status: str
    ) -> bool:
        """Update campaign status (ENABLED, PAUSED, REMOVED)."""
        if not self.client:
            return False

        try:
            resp = await self.client.post(
                f"/customers/{self.customer_id}/campaigns:mutate",
                json={
                    "operations": [{
                        "update": {
                            "resourceName": campaign_resource_name,
                            "status": status,
                        },
                        "updateMask": "status",
                    }]
                },
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Google Ads status update failed: {e}")
            return False
