"""
Faceless Video Pipeline — Script → Voice → Visuals → Compose → Upload
Supports both stock-footage and HeyGen avatar modes.
"""
import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path

import config

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
        await _generate_tts(narration, voice, str(audio_path))
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
        await _compose_video(
            audio_files, video_files, str(output_path), resolution, script
        )
        duration = await _get_video_duration(str(output_path))

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

    # Create video
    video_id = await heygen.create_video(
        script_text=full_narration,
        avatar_id=avatar_id,
        voice_id=voice,
        aspect_ratio="9:16",  # Portrait for Shorts/TikTok
    )

    if not video_id:
        raise ValueError("Failed to create HeyGen video")

    logger.info(f"[{job_id}] HeyGen video submitted: {video_id}")

    # Wait for completion
    result = await heygen.wait_for_video(video_id, timeout=600)

    return {
        "video_url": result.get("video_url", ""),
        "video_id": video_id,
        "title": script.get("title", ""),
        "description": script.get("description", ""),
        "tags": script.get("tags", []),
        "job_id": job_id,
        "mode": "avatar",
    }


async def _generate_tts(text: str, voice: str, output_path: str):
    """Generate TTS audio using edge-tts (free, 300+ voices)."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def _compose_video(
    audio_files: list[str],
    video_files: list[str],
    output_path: str,
    resolution: str = "1080x1920",
    script: dict = None,
):
    """Compose final video from audio + video clips using ffmpeg."""
    width, height = resolution.split("x")

    # Create input file list for concatenation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")
        video_list_path = f.name

    # Concatenate video clips
    concat_path = output_path.replace(".mp4", "_concat.mp4")
    concat_cmd = (
        f"ffmpeg -y -f concat -safe 0 -i {video_list_path} "
        f"-vf 'scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1' "
        f"-c:v libx264 -preset fast -crf 23 -an {concat_path}"
    )
    proc = await asyncio.create_subprocess_shell(
        concat_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"ffmpeg concat failed: {stderr.decode()[:500]}")

    # Concatenate audio files
    audio_concat_path = output_path.replace(".mp4", "_audio.mp3")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for af in audio_files:
            f.write(f"file '{af}'\n")
        audio_list_path = f.name

    audio_cmd = (
        f"ffmpeg -y -f concat -safe 0 -i {audio_list_path} "
        f"-c:a libmp3lame -q:a 2 {audio_concat_path}"
    )
    proc = await asyncio.create_subprocess_shell(
        audio_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    # Merge video + audio (trim video to audio length)
    merge_cmd = (
        f"ffmpeg -y -i {concat_path} -i {audio_concat_path} "
        f"-c:v copy -c:a aac -shortest {output_path}"
    )
    proc = await asyncio.create_subprocess_shell(
        merge_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"ffmpeg merge failed: {stderr.decode()[:500]}")

    # Cleanup temp files
    for p in [video_list_path, audio_list_path, concat_path, audio_concat_path]:
        try:
            os.unlink(p)
        except OSError:
            pass


async def _get_video_duration(path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = (
        f"ffprobe -v quiet -show_entries format=duration "
        f"-of default=noprint_wrappers=1:nokey=1 '{path}'"
    )
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    try:
        return float(stdout.decode().strip())
    except (ValueError, AttributeError):
        return 0.0


async def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] = None,
    category_id: str = "22",  # People & Blogs
    privacy: str = "public",
) -> dict:
    """Upload a video to YouTube via the Data API v3."""
    import httpx

    if not config.YOUTUBE_API_KEY:
        logger.warning("YouTube API not configured — skipping upload")
        return {"status": "skipped", "reason": "not_configured"}

    # Refresh OAuth token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": config.YOUTUBE_CLIENT_ID,
                "client_secret": config.YOUTUBE_CLIENT_SECRET,
                "refresh_token": config.YOUTUBE_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
        if token_resp.status_code != 200:
            return {"status": "error", "reason": "token_refresh_failed"}

        access_token = token_resp.json()["access_token"]

        # Upload video (resumable upload)
        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": (tags or [])[:30],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Step 1: Initialize upload
        init_resp = await client.post(
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            json=metadata,
        )

        if init_resp.status_code != 200:
            return {"status": "error", "reason": f"init_failed: {init_resp.text[:200]}"}

        upload_url = init_resp.headers.get("Location")
        if not upload_url:
            return {"status": "error", "reason": "no_upload_url"}

        # Step 2: Upload the video file
        with open(video_path, "rb") as f:
            video_data = f.read()

        upload_resp = await client.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_data)),
            },
            content=video_data,
            timeout=600.0,
        )

        if upload_resp.status_code in (200, 201):
            data = upload_resp.json()
            video_id = data.get("id", "")
            logger.info(f"YouTube upload success: https://youtube.com/watch?v={video_id}")
            return {
                "status": "uploaded",
                "video_id": video_id,
                "url": f"https://youtube.com/watch?v={video_id}",
            }
        else:
            return {"status": "error", "reason": f"upload_failed: {upload_resp.status_code}"}
