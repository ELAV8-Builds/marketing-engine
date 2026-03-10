"""Landing page routes."""
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from db.database import get_session
import config

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class LandingPageCreate(BaseModel):
    campaign_id: str = ""
    product_name: str
    product_description: str
    target_audience: str = ""
    template: str = "saas"
    slug: str = ""


class LandingPageDeploy(BaseModel):
    landing_page_id: str
    custom_domain: str = ""


# ── Endpoints ────────────────────────────────────────────

@router.post("/landing-pages/generate")
async def generate_landing_page(body: LandingPageCreate):
    """Generate a landing page with AI content."""
    from services import llm

    page_content = await llm.generate_landing_page(
        product_name=body.product_name,
        product_description=body.product_description,
        target_audience=body.target_audience,
        template=body.template,
    )

    result = {
        "name": body.product_name,
        "slug": body.slug or body.product_name.lower().replace(" ", "-"),
        "template": body.template,
        "content": page_content,
        "status": "generated",
    }

    # Save to DB
    if body.campaign_id:
        async with get_session() as session:
            await session.execute(
                text("""
                    INSERT INTO landing_pages
                        (campaign_id, name, slug, template, headline, subheadline, cta_text, status)
                    VALUES (:campaign_id, :name, :slug, :template, :headline, :sub, :cta, 'draft')
                """),
                {
                    "campaign_id": body.campaign_id,
                    "name": body.product_name,
                    "slug": result["slug"],
                    "template": body.template,
                    "headline": page_content.get("headline", ""),
                    "sub": page_content.get("subheadline", ""),
                    "cta": page_content.get("hero_cta", "Get Started"),
                },
            )

    return result


@router.get("/landing-pages")
async def list_landing_pages(
    campaign_id: str = "",
    limit: int = Query(50, ge=1, le=200),
):
    async with get_session() as session:
        conditions = []
        params = {}
        if campaign_id:
            conditions.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        params["limit"] = limit
        q = f"SELECT * FROM landing_pages{where} ORDER BY created_at DESC LIMIT :limit"
        result = await session.execute(text(q), params)
        rows = result.mappings().all()
        return {"pages": [dict(r) for r in rows], "count": len(rows)}


@router.post("/landing-pages/{page_id}/deploy")
async def deploy_landing_page(page_id: str):
    """Deploy a landing page to Vercel."""
    import httpx

    if not config.VERCEL_TOKEN:
        raise HTTPException(status_code=400, detail="Vercel token not configured")

    async with get_session() as session:
        result = await session.execute(
            text("SELECT * FROM landing_pages WHERE id = :id"),
            {"id": page_id},
        )
        page = result.mappings().first()
        if not page:
            raise HTTPException(status_code=404, detail="Landing page not found")

        slug = page["slug"]
        headline = page.get("headline", "")
        subheadline = page.get("subheadline", "")
        cta_text = page.get("cta_text", "Get Started")
        cta_url = page.get("cta_url", "#")
        body_html = page.get("body_html", "")

        # Generate a simple HTML landing page
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{headline}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a2e;background:#fff}}
.hero{{min-height:80vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);color:#fff;margin-bottom:1rem;max-width:800px}}
.hero p{{font-size:1.25rem;color:rgba(255,255,255,0.9);margin-bottom:2rem;max-width:600px}}
.cta-btn{{display:inline-block;padding:1rem 2.5rem;background:#fff;color:#764ba2;font-size:1.125rem;font-weight:700;border-radius:8px;text-decoration:none;transition:transform 0.2s}}
.cta-btn:hover{{transform:translateY(-2px)}}
.content{{max-width:800px;margin:3rem auto;padding:0 2rem;line-height:1.7;font-size:1.125rem}}
</style>
</head>
<body>
<section class="hero">
<h1>{headline}</h1>
<p>{subheadline}</p>
<a href="{cta_url}" class="cta-btn">{cta_text}</a>
</section>
<section class="content">{body_html}</section>
</body>
</html>"""

        # Deploy to Vercel using the deployments API
        try:
            async with httpx.AsyncClient() as client:
                deploy_resp = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {config.VERCEL_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": f"lp-{slug}",
                        "files": [
                            {
                                "file": "index.html",
                                "data": html_content,
                            }
                        ],
                        "projectSettings": {
                            "framework": None,
                        },
                    },
                    timeout=60.0,
                )
                deploy_resp.raise_for_status()
                deploy_data = deploy_resp.json()

                deployed_url = f"https://{deploy_data.get('url', '')}"
                deployment_id = deploy_data.get("id", "")

                # Update DB with deployment info
                await session.execute(
                    text("""
                        UPDATE landing_pages SET
                            deployed_url = :url,
                            vercel_deployment_id = :did,
                            status = 'deployed',
                            updated_at = NOW()
                        WHERE id = :id
                    """),
                    {"id": page_id, "url": deployed_url, "did": deployment_id},
                )

                return {
                    "status": "deployed",
                    "url": deployed_url,
                    "deployment_id": deployment_id,
                }

        except Exception as e:
            logger.error(f"Vercel deployment failed: {e}")
            raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)[:200]}")
