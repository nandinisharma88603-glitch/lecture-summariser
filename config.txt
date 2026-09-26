from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
ARTIFACT_DIR = BASE_DIR / "artifacts"

ALLOWED_EXTENSIONS = {
    "txt",
    "md",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "tif",
    "tiff",
    "webp",
    "wav",
    "mp3",
    "m4a",
    "flac",
    "ogg",
    "mp4",
    "mov",
    "mkv",
    "avi",
    "webm",
}


def ensure_directories() -> None:
    for path in (UPLOAD_DIR, OUTPUT_DIR, ARTIFACT_DIR):
        path.mkdir(parents=True, exist_ok=True)
