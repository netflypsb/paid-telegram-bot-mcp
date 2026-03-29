"""Pro-tier File & Media tools (license required)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..bot.bot_manager import get_bot_manager
from ..config import get_config
from ..license import require_license

logger = logging.getLogger(__name__)

# Telegram file size limits
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB

# Extension-based media type routing
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".flac", ".m4a"}
VOICE_EXTENSIONS = {".ogg", ".oga"}


def _detect_media_type(file_path: str) -> str:
    """Detect the media type based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext in PHOTO_EXTENSIONS:
        return "photo"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return "document"


def register_media_tools(mcp: FastMCP) -> None:
    """Register all file/media tools on the MCP server."""

    @mcp.tool()
    async def file_send(
        chat_id: int,
        file_path: str,
        caption: str = "",
        force_document: bool = False,
    ) -> str:
        """Send any file with smart media routing (auto-detects photo/video/audio/document).

        Args:
            chat_id: The Telegram chat ID to send the file to
            file_path: Local file path or URL to send
            caption: Optional caption for the file
            force_document: If True, always send as document regardless of type
        """
        err = require_license("file_send")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        try:
            media_type = "document" if force_document else _detect_media_type(file_path)

            # Check if it's a local file or URL
            is_local = not file_path.startswith(("http://", "https://"))
            if is_local and not Path(file_path).exists():
                return json.dumps({"error": f"File not found: {file_path}"})

            if is_local:
                file_size = Path(file_path).stat().st_size
                if media_type == "photo" and file_size > MAX_PHOTO_SIZE:
                    media_type = "document"
                if file_size > MAX_DOCUMENT_SIZE:
                    return json.dumps({
                        "error": f"File too large ({file_size / 1024 / 1024:.1f} MB). "
                                 f"Telegram limit is {MAX_DOCUMENT_SIZE / 1024 / 1024:.0f} MB."
                    })

            kwargs = {"chat_id": chat_id, "caption": caption or None}

            if is_local:
                with open(file_path, "rb") as f:
                    if media_type == "photo":
                        msg = await manager.bot.send_photo(photo=f, **kwargs)
                    elif media_type == "video":
                        msg = await manager.bot.send_video(video=f, **kwargs)
                    elif media_type == "audio":
                        msg = await manager.bot.send_audio(audio=f, **kwargs)
                    else:
                        msg = await manager.bot.send_document(document=f, **kwargs)
            else:
                if media_type == "photo":
                    msg = await manager.bot.send_photo(photo=file_path, **kwargs)
                elif media_type == "video":
                    msg = await manager.bot.send_video(video=file_path, **kwargs)
                elif media_type == "audio":
                    msg = await manager.bot.send_audio(audio=file_path, **kwargs)
                else:
                    msg = await manager.bot.send_document(document=file_path, **kwargs)

            return json.dumps({
                "status": "sent",
                "message_id": msg.message_id,
                "chat_id": chat_id,
                "media_type": media_type,
            })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def file_download(file_id: str, save_as: str = "") -> str:
        """Download a file received from a user by its file_id.

        Args:
            file_id: The Telegram file_id from a received message
            save_as: Optional local filename to save as (saved in data dir)
        """
        err = require_license("file_download")
        if err:
            return err

        manager = get_bot_manager()
        if not manager.bot:
            return json.dumps({"error": "Bot not running. Use bot_start first."})

        try:
            file = await manager.bot.get_file(file_id)
            config = get_config()
            files_dir = config.files_path
            files_dir.mkdir(parents=True, exist_ok=True)

            if save_as:
                local_path = files_dir / save_as
            else:
                # Use file_unique_id as filename
                ext = Path(file.file_path or "").suffix if file.file_path else ""
                local_path = files_dir / f"{file.file_unique_id}{ext}"

            await file.download_to_drive(str(local_path))

            return json.dumps({
                "status": "downloaded",
                "file_id": file_id,
                "local_path": str(local_path),
                "file_size": file.file_size,
            })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    async def file_list_received(limit: int = 50) -> str:
        """List files that have been downloaded/received from users.

        Args:
            limit: Maximum number of files to list
        """
        err = require_license("file_list_received")
        if err:
            return err

        config = get_config()
        files_dir = config.files_path

        if not files_dir.exists():
            return json.dumps({"count": 0, "files": []})

        files = []
        for f in sorted(files_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and len(files) < limit:
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })

        return json.dumps({"count": len(files), "files": files}, indent=2)
