"""Campaign CRUD routes."""
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    product_name: str
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    channels: list[str] = []
    budget_daily: float = 0
    budget_total: float = 0


class CampaignUpdate(BaseModel):
    name: str = ""
    product_name: str = ""
    product_url: str = ""
    product_description: str = ""
    target_audience: str = ""
    channels: list[str] = []
    budget_daily: float = -1
    budget_total: float = -1
    status: str = ""
    meta: dict = {}


# ── Endpoints ────────────────────────────────────────────

@router.get("/campaigns")
async def list_campaigns(
    status: str = Query("all", pattern="^(all|draft|active|paused|completed)$"),
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        params: dict = {"limit": limit}
        if status != "all":
            q = "SELECT * FROM campaigns WHERE status = :status ORDER BY created_at DESC LIMIT :limit"
            params["status"] = status
        else:
            q = "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"campaigns": [dict(r) for r in rows], "count": len(rows)}


@router.post("/campaigns")
async def create_campaign(body: CampaignCreate):
    async with get_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO campaigns (name, product_name, product_url, product_description,
                    target_audience, channels, budget_daily, budget_total, status)
                VALUES (:name, :product_name, :product_url, :product_description,
                    :target_audience, :channels, :budget_daily, :budget_total, 'active')
                RETURNING id, name, status, created_at
            """),
            {
                "name": body.name,
                "product_name": body.product_name,
                "product_url": body.product_url,
                "product_description": body.product_description,
                "target_audience": body.target_audience,
                "channels": body.channels,
                "budget_daily": body.budget_daily,
                "budget_total": body.budget_total,
            },
        )
        row = result.mappings().first()
        return dict(row)


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    async with get_session() as session:
        result = await session.execute(
            text("SELECT * FROM campaigns WHERE id = :id"),
            {"id": campaign_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return dict(row)


@router.patch("/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, body: CampaignUpdate):
    """Update a campaign's fields. Only non-empty fields are updated."""
    async with get_session() as session:
        updates = []
        params: dict = {"id": campaign_id}
        if body.name:
            updates.append("name = :name")
            params["name"] = body.name
        if body.product_name:
            updates.append("product_name = :pname")
            params["pname"] = body.product_name
        if body.product_url:
            updates.append("product_url = :purl")
            params["purl"] = body.product_url
        if body.product_description:
            updates.append("product_description = :pdesc")
            params["pdesc"] = body.product_description
        if body.target_audience:
            updates.append("target_audience = :audience")
            params["audience"] = body.target_audience
        if body.channels:
            updates.append("channels = :channels")
            params["channels"] = body.channels
        if body.budget_daily >= 0:
            updates.append("budget_daily = :bdaily")
            params["bdaily"] = body.budget_daily
        if body.budget_total >= 0:
            updates.append("budget_total = :btotal")
            params["btotal"] = body.budget_total
        if body.status:
            updates.append("status = :status")
            params["status"] = body.status

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        q = f"UPDATE campaigns SET {', '.join(updates)} WHERE id = :id RETURNING *"
        result = await session.execute(text(q), params)
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return dict(row)


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign (soft delete -- sets status to 'deleted')."""
    async with get_session() as session:
        result = await session.execute(
            text("UPDATE campaigns SET status = 'deleted', updated_at = NOW() WHERE id = :id RETURNING id"),
            {"id": campaign_id},
        )
        row = result.mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"deleted": True, "id": str(row["id"])}
