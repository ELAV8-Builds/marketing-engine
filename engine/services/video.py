"""
Faceless Video Pipeline — backward-compatible re-export wrapper.

All generation logic lives in video_generation.py.
All upload logic lives in video_upload.py.

This module re-exports the public API so that existing imports
(e.g. `from services.video import generate_faceless_video, upload_to_youtube`)
continue to work without changes.
"""

from services.video_generation import (  # noqa: F401
    generate_faceless_video,
    MEDIA_DIR,
)
from services.video_upload import upload_to_youtube  # noqa: F401

__all__ = [
    "generate_faceless_video",
    "upload_to_youtube",
    "MEDIA_DIR",
]
