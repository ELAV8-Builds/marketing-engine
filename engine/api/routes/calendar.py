"""Content calendar routes."""
import logging

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class CalendarItemCreate(BaseModel):
    campaign_id: str
    scheduled_date: str  # YYYY-MM-DD
    scheduled_time: str = "09:00"  # HH:MM
    platform: str
    content_type: str
    topic: str = ""


# ── Endpoints ────────────────────────────────────────────

@router.post("/calendar")
async def create_calendar_item(body: CalendarItemCreate):
    """Schedule a content item on the calendar."""
    async with get_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO content_calendar
                    (campaign_id, scheduled_date, scheduled_time, platform, content_type, topic, status)
                VALUES (:cid, :date, :time, :platform, :type, :topic, 'pending')
                RETURNING id, scheduled_date, platform, content_type, topic, status
            """),
            {
                "cid": body.campaign_id,
                "date": body.scheduled_date,
                "time": body.scheduled_time,
                "platform": body.platform,
                "type": body.content_type,
                "topic": body.topic,
            },
        )
        row = result.mappings().first()
        return dict(row)


@router.get("/calendar")
async def get_calendar(
    campaign_id: str = "",
    start_date: str = "",
    end_date: str = "",
):
    async with get_session() as session:
        conditions = []
        params: dict = {}
        if campaign_id:
            conditions.append("campaign_id = :cid")
            params["cid"] = campaign_id
        if start_date:
            conditions.append("scheduled_date >= :start")
            params["start"] = start_date
        if end_date:
            conditions.append("scheduled_date <= :end")
            params["end"] = end_date

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        q = f"SELECT * FROM content_calendar{where} ORDER BY scheduled_date, scheduled_time"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"calendar": [dict(r) for r in rows], "count": len(rows)}
