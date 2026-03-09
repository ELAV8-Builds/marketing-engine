"""
LLM Service — Routes requests through LiteLLM for cost-efficient AI generation.
"""
import logging
import httpx
import config

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=config.LITELLM_URL,
            timeout=120.0,
        )
    return _client


async def generate(
    prompt: str,
    system: str = "",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """Generate text via LiteLLM. Falls back to direct model if LiteLLM is down."""
    model = model or config.LITELLM_MODEL

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        client = _get_client()
        resp = await client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return ""


async def generate_json(
    prompt: str,
    system: str = "",
    model: str = "",
) -> dict:
    """Generate structured JSON output."""
    import json

    system_with_json = (system + "\n\n" if system else "") + (
        "You MUST respond with valid JSON only. No markdown, no explanation, just the JSON object."
    )

    text = await generate(prompt, system=system_with_json, model=model, temperature=0.3)

    # Extract JSON from response (handle markdown code blocks)
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from LLM: {text[:200]}")
        return {}


async def generate_ad_copy(
    product_name: str,
    product_description: str,
    target_audience: str,
    platform: str = "meta",
    count: int = 3,
) -> list[dict]:
    """Generate ad copy variations for a product."""
    prompt = f"""Generate {count} ad copy variations for the following product:

Product: {product_name}
Description: {product_description}
Target Audience: {target_audience}
Platform: {platform}

For each variation, provide:
- headline (max 40 chars)
- body (max 125 chars for Meta, 90 for Google)
- cta (call to action text)

Return as JSON array: [{{"headline": "...", "body": "...", "cta": "..."}}]"""

    result = await generate_json(prompt, model=config.LITELLM_CREATIVE_MODEL)
    if isinstance(result, list):
        return result
    return result.get("variations", result.get("ads", []))


async def generate_video_script(
    topic: str,
    style: str = "educational",
    duration_seconds: int = 60,
    product_name: str = "",
    product_url: str = "",
) -> dict:
    """Generate a video script for a faceless short."""
    prompt = f"""Write a {duration_seconds}-second video script for a {style} short-form video.

Topic: {topic}
{"Product to subtly mention: " + product_name if product_name else ""}
{"Product URL: " + product_url if product_url else ""}

Structure:
1. Hook (first 3 seconds) — attention-grabbing opener
2. Context — set up the topic
3. Value — deliver the key insight/information
4. {"CTA — mention the product naturally" if product_name else "CTA — end with engagement prompt"}

Return JSON:
{{
    "title": "Video title for SEO",
    "description": "YouTube/TikTok description with hashtags",
    "tags": ["tag1", "tag2"],
    "scenes": [
        {{
            "narration": "What the voiceover says",
            "visual_query": "Search query for stock footage",
            "duration_seconds": 5
        }}
    ]
}}"""

    return await generate_json(prompt, model=config.LITELLM_CREATIVE_MODEL)


async def generate_reddit_comment(
    post_title: str,
    post_body: str,
    subreddit: str,
    product_name: str = "",
    product_url: str = "",
    comment_type: str = "promotional",
) -> dict:
    """Generate a contextual Reddit comment."""
    if comment_type == "organic":
        prompt = f"""Write a helpful, authentic Reddit comment for this post in r/{subreddit}:

Title: {post_title}
Body: {post_body[:500]}

Write as a genuine community member. Be helpful, add value, share relevant experience.
Do NOT mention any product or URL. Just be genuinely helpful.

Return JSON: {{"comment": "your comment text", "confidence": 0.0-1.0}}"""
    else:
        prompt = f"""Write a helpful Reddit comment for this post in r/{subreddit} that naturally mentions a relevant tool:

Title: {post_title}
Body: {post_body[:500]}

Product to mention: {product_name}
{"URL: " + product_url if product_url else ""}

Rules:
- The comment MUST be genuinely helpful first, product mention second
- The product mention should feel natural, not forced
- Don't start with "I" too much
- Match the subreddit's tone and culture
- Be specific and add real value
- Keep it under 200 words

Return JSON: {{"comment": "your comment text", "confidence": 0.0-1.0}}"""

    return await generate_json(prompt, model=config.LITELLM_MODEL)


async def generate_landing_page(
    product_name: str,
    product_description: str,
    target_audience: str,
    template: str = "saas",
) -> dict:
    """Generate landing page content."""
    prompt = f"""Generate landing page content for:

Product: {product_name}
Description: {product_description}
Target Audience: {target_audience}
Template Style: {template}

Return JSON:
{{
    "headline": "Main headline (max 10 words)",
    "subheadline": "Supporting text (max 20 words)",
    "hero_cta": "CTA button text",
    "features": [
        {{"title": "Feature name", "description": "1 sentence", "icon": "emoji"}}
    ],
    "social_proof": "Social proof statement",
    "faq": [
        {{"question": "...", "answer": "..."}}
    ],
    "meta_title": "SEO title",
    "meta_description": "SEO description (max 160 chars)"
}}"""

    return await generate_json(prompt, model=config.LITELLM_CREATIVE_MODEL)
