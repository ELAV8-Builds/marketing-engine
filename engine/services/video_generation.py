"""
Faceless Video Generation — Script -> Voice -> Visuals -> Compose
Supports both stock-footage and HeyGen avatar modes.
"""
import logging
import os
import uuid
from pathlib import Path

import config
from services._video_helpers import compose_video, generate_tts, get_video_duration

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("/app/media") if os.path.exists("/app/media") else Path("./media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


async def generate_faceless_video(
    script: dict,
    voice: str = "en-US-AriaNeural",
    mode: str = "stock",  # "stock" | "avatar"
    resolution: str = "1080x1920",  # portrait for Shorts/TikTok
) -> dict:
    """
    Full faceless video pipeline.

    Args:
        script: Output from llm.generate_video_script() — contains scenes with narration + visual queries
        voice: Edge-TTS voice name or ElevenLabs voice ID
        mode: "stock" for Pexels footage, "avatar" for HeyGen
        resolution: Video resolution

    Returns:
        {"video_path": str, "duration": float, "title": str, "description": str}
    """
    job_id = str(uuid.uuid4())[:8]
    job_dir = MEDIA_DIR / "videos" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    title = script.get("title", "Untitled")
    scenes = script.get("scenes", [])
    description = script.get("description", "")
    tags = script.get("tags", [])

    if not scenes:
        raise ValueError("Script has no scenes")

    logger.info(f"[{job_id}] Starting faceless video: {title} ({len(scenes)} scenes, mode={mode})")

    if mode == "avatar":
        return await _generate_avatar_video(job_id, job_dir, script, voice)
    else:
        return await _generate_stock_video(job_id, job_dir, script, voice, resolution)


async def _generate_stock_video(
    job_id: str,
    job_dir: Path,
    script: dict,
    voice: str,
    resolution: str,
) -> dict:
    """Generate video using stock footage + TTS voiceover."""
    from services.pexels import PexelsClient

    scenes = script.get("scenes", [])

    # Step 1: Generate voiceover for each scene
    audio_files = []
    for i, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        if not narration:
            continue

        audio_path = job_dir / f"audio_{i:03d}.mp3"
        await generate_tts(narration, voice, str(audio_path))
        audio_files.append(str(audio_path))
        logger.info(f"[{job_id}] TTS scene {i+1}/{len(scenes)} done")

    # Step 2: Download stock footage for each scene
    video_files = []
    if config.PEXELS_API_KEY:
        pexels = PexelsClient()
        for i, scene in enumerate(scenes):
            query = scene.get("visual_query", "technology abstract")
            video_path = job_dir / f"clip_{i:03d}.mp4"

            downloaded = await pexels.download_video(query, str(video_path))
            if downloaded:
                video_files.append(str(video_path))
                logger.info(f"[{job_id}] Stock clip {i+1}/{len(scenes)}: '{query}'")
            else:
                logger.warning(f"[{job_id}] No stock clip for '{query}'")
    else:
        logger.warning(f"[{job_id}] Pexels not configured — skipping stock footage")

    # Step 3: Compose with ffmpeg
    if audio_files and video_files:
        output_path = job_dir / "final.mp4"
        await compose_video(
            audio_files, video_files, str(output_path), resolution, script
        )
        duration = await get_video_duration(str(output_path))

        logger.info(f"[{job_id}] Video composed: {output_path} ({duration:.1f}s)")

        return {
            "video_path": str(output_path),
            "duration": duration,
            "title": script.get("title", ""),
            "description": script.get("description", ""),
            "tags": script.get("tags", []),
            "job_id": job_id,
        }
    elif audio_files:
        # Audio-only output (could be used for podcast or audio posts)
        return {
            "audio_files": audio_files,
            "title": script.get("title", ""),
            "description": script.get("description", ""),
            "tags": script.get("tags", []),
            "job_id": job_id,
            "status": "audio_only",
        }
    else:
        return {
            "job_id": job_id,
            "status": "script_only",
            "script": script,
        }


async def _generate_avatar_video(
    job_id: str,
    job_dir: Path,
    script: dict,
    voice: str,
) -> dict:
    """Generate video using HeyGen AI avatar."""
    from services.heygen import HeyGenClient

    if not config.HEYGEN_API_KEY:
        raise ValueError("HeyGen API key not configured")

    heygen = HeyGenClient()
    await heygen.connect()

    # Combine all scene narration into one script
    full_narration = " ".join(
        scene.get("narration", "") for scene in script.get("scenes", [])
    )

    if not full_narration.strip():
        raise ValueError("No narration in script")

    # Get available avatars and voices
    avatars = await heygen.list_avatars()
    if not avatars:
        raise ValueError("No HeyGen avatars available")

    avatar_id = avatars[0].get("avatar_id", avatars[0].get("id", ""))

    # Create video (heygen.create_video takes `script` not `script_text`)
    video_id = await heygen.create_video(
        script=full_narration,
        avatar_id=avatar_id,
        voice_id=voice,
        aspect_ratio="9:16",  # Portrait for Shorts/TikTok
    )

    if not video_id:
        raise ValueError("Failed to create HeyGen video")

    logger.info(f"[{job_id}] HeyGen video submitted: {video_id}")

    # Wait for completion — returns video URL string or None
    video_url = await heygen.wait_for_video(video_id, timeout=600)

    if not video_url:
        raise ValueError(f"HeyGen video generation failed or timed out: {video_id}")

    return {
        "video_url": video_url,
        "video_id": video_id,
        "title": script.get("title", ""),
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "job_id": job_id,
        "mode": "avatar",
    }
