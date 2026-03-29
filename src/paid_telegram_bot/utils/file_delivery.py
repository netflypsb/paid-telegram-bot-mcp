"""Smart file delivery utilities.

Handles automatic media type detection, batch ZIP compression,
and retry with exponential backoff for file sends.
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".3gp"}
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac"}
VOICE_EXTENSIONS = {".ogg", ".oga"}
ANIMATION_EXTENSIONS = {".gif"}

MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_BATCH_FILES = 10


def detect_media_type(file_path: str | Path) -> str:
    """Detect the appropriate Telegram media type for a file.

    Returns one of: photo, video, audio, voice, animation, document
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in ANIMATION_EXTENSIONS:
        return "animation"
    if ext in PHOTO_EXTENSIONS:
        # Check file size — photos over 10MB must be sent as documents
        if path.exists() and path.stat().st_size > MAX_PHOTO_SIZE:
            return "document"
        return "photo"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in VOICE_EXTENSIONS:
        return "voice"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "document"


def create_batch_zip(file_paths: list[str | Path], zip_name: str = "files.zip") -> io.BytesIO:
    """Create a ZIP archive from multiple files for batch delivery.

    Args:
        file_paths: List of file paths to include in the ZIP
        zip_name: Name for the ZIP file

    Returns:
        BytesIO buffer containing the ZIP file
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            path = Path(fp)
            if path.exists() and path.is_file():
                zf.write(path, path.name)
            else:
                logger.warning("Skipping missing file: %s", fp)
    buffer.seek(0)
    return buffer


def should_batch_as_zip(file_paths: list[str | Path]) -> bool:
    """Determine if files should be sent as a ZIP batch.

    Returns True if there are more than MAX_BATCH_FILES files,
    or the total size exceeds the document limit.
    """
    if len(file_paths) > MAX_BATCH_FILES:
        return True

    total_size = 0
    for fp in file_paths:
        path = Path(fp)
        if path.exists():
            total_size += path.stat().st_size
    return total_size > MAX_DOCUMENT_SIZE
