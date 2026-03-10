"""Logo generation routes."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────

class LogoGenerate(BaseModel):
    brand_name: str
    tagline: str = ""
    industry: str = ""
    style: str = "minimal"  # minimal, bold, playful, luxury, tech, organic
    provider: str = "recraft"  # recraft, ideogram, dalle
    color_primary: str = "#7c5cfc"
    color_secondary: str = "#5eead4"
    count: int = 4


# ── Endpoints ────────────────────────────────────────────

@router.post("/logos/generate")
async def generate_logos(body: LogoGenerate):
    """Generate logo concepts using AI image generation APIs."""
    import httpx

    style_prompts = {
        "minimal": "minimalist, clean lines, simple geometric shapes, modern, whitespace",
        "bold": "bold, strong typography, impactful, high contrast, memorable",
        "playful": "playful, creative, colorful, fun, whimsical, rounded shapes",
        "luxury": "luxury, elegant, premium, refined, gold accents, serif typography",
        "tech": "tech, futuristic, digital, modern, circuit-inspired, gradient",
        "organic": "organic, natural, flowing curves, leaf motifs, earthy, soft",
    }

    style_desc = style_prompts.get(body.style, style_prompts["minimal"])

    base_prompt = (
        f'Professional logo design for "{body.brand_name}"'
        f'{f", tagline: {body.tagline}" if body.tagline else ""}'
        f'{f", industry: {body.industry}" if body.industry else ""}. '
        f'Style: {style_desc}. '
        f'Colors: {body.color_primary} and {body.color_secondary}. '
        f'Logo on clean background, vector style, scalable, brand-ready. '
        f'No mockups, no text except the brand name.'
    )

    logos = []

    if body.provider == "recraft":
        # Recraft V4 -- native SVG vector logos
        recraft_key = config.env("RECRAFT_API_KEY")
        if not recraft_key:
            raise HTTPException(status_code=400, detail="RECRAFT_API_KEY not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(body.count):
                variation_prompt = f"{base_prompt} Variation {i + 1} of {body.count}."
                try:
                    resp = await client.post(
                        "https://external.api.recraft.ai/v1/images/generations",
                        headers={"Authorization": f"Bearer {recraft_key}"},
                        json={
                            "prompt": variation_prompt,
                            "style": "vector_illustration",
                            "model": "recraftv3",
                            "size": "1024x1024",
                            "response_format": "url",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    image_url = data.get("data", [{}])[0].get("url", "")
                    if image_url:
                        logos.append({
                            "url": image_url,
                            "style": f"{body.style} - variation {i + 1}",
                            "prompt": variation_prompt,
                            "provider": "recraft",
                            "format": "svg",
                        })
                except Exception as e:
                    logger.error(f"Recraft logo generation failed: {e}")

    elif body.provider == "ideogram":
        # Ideogram V3 -- best text rendering
        ideogram_key = config.env("IDEOGRAM_API_KEY")
        if not ideogram_key:
            raise HTTPException(status_code=400, detail="IDEOGRAM_API_KEY not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(body.count):
                variation_prompt = f"{base_prompt} Variation {i + 1}."
                try:
                    resp = await client.post(
                        "https://api.ideogram.ai/generate",
                        headers={
                            "Api-Key": ideogram_key,
                            "Content-Type": "application/json",
                        },
                        json={
                            "image_request": {
                                "prompt": variation_prompt,
                                "model": "V_2",
                                "magic_prompt_option": "AUTO",
                                "aspect_ratio": "ASPECT_1_1",
                            },
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    images = data.get("data", [])
                    if images:
                        logos.append({
                            "url": images[0].get("url", ""),
                            "style": f"{body.style} - variation {i + 1}",
                            "prompt": variation_prompt,
                            "provider": "ideogram",
                            "format": "png",
                        })
                except Exception as e:
                    logger.error(f"Ideogram logo generation failed: {e}")

    elif body.provider == "dalle":
        # DALL-E 3 via LiteLLM or direct OpenAI
        openai_key = config.env("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY not configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(body.count):
                variation_prompt = f"{base_prompt} Variation {i + 1}."
                try:
                    resp = await client.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {openai_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "dall-e-3",
                            "prompt": variation_prompt,
                            "n": 1,
                            "size": "1024x1024",
                            "quality": "standard",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    images = data.get("data", [])
                    if images:
                        logos.append({
                            "url": images[0].get("url", ""),
                            "style": f"{body.style} - variation {i + 1}",
                            "prompt": variation_prompt,
                            "provider": "dalle",
                            "format": "png",
                        })
                except Exception as e:
                    logger.error(f"DALL-E logo generation failed: {e}")

    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {body.provider}")

    return {
        "logos": logos,
        "count": len(logos),
        "provider": body.provider,
        "style": body.style,
        "brand_name": body.brand_name,
    }
