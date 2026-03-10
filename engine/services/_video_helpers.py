"""
Internal helpers for the video generation pipeline:
TTS generation, ffmpeg composition, and duration probing.
"""
import asyncio
import logging
import os
import tempfile

import config

logger = logging.getLogger(__name__)


async def generate_tts(text: str, voice: str, output_path: str):
    """Generate TTS audio. Uses ElevenLabs if configured and voice is an ElevenLabs ID, else edge-tts."""

    # ElevenLabs voice IDs are 20-char alphanumeric strings, edge-tts voices have dashes
    if config.ELEVENLABS_API_KEY and "-" not in voice and len(voice) >= 15:
        await _generate_elevenlabs_tts(text, voice, output_path)
    else:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)


async def _generate_elevenlabs_tts(text: str, voice_id: str, output_path: str):
    """Generate TTS audio using ElevenLabs API (premium, natural voices)."""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": config.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.0,
                        "use_speaker_boost": True,
                    },
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"ElevenLabs TTS generated: {output_path}")
    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e} — falling back to edge-tts")
        import edge_tts
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(output_path)


async def compose_video(
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


async def get_video_duration(path: str) -> float:
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
