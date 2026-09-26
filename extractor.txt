from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageEnhance = None
    ImageFilter = None

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


TEXT_EXTENSIONS = {".txt", ".md"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

_WHISPER_MODELS = {}


@dataclass
class ExtractionResult:
    source_type: str
    text: str
    warnings: List[str] = field(default_factory=list)
    keyframes: List[str] = field(default_factory=list)


class ContentExtractor:
    """Extract raw lecture text from files across modalities."""

    def extract(self, input_path: Path, artifact_dir: Path) -> ExtractionResult:
        suffix = input_path.suffix.lower()
        warnings: List[str] = []
        keyframes: List[str] = []

        if suffix in TEXT_EXTENSIONS:
            return ExtractionResult("text", self._extract_text_file(input_path), warnings, keyframes)

        if suffix in PDF_EXTENSIONS:
            text = self._extract_text_from_pdf(input_path, warnings)
            return ExtractionResult("pdf", text, warnings, keyframes)

        if suffix in IMAGE_EXTENSIONS:
            text = self._extract_text_from_image(input_path, warnings)
            return ExtractionResult("image", text, warnings, keyframes)

        if suffix in AUDIO_EXTENSIONS:
            text = self._transcribe_audio(input_path, warnings)
            return ExtractionResult("audio", text, warnings, keyframes)

        if suffix in VIDEO_EXTENSIONS:
            text, keyframes = self._extract_from_video(input_path, artifact_dir, warnings)
            return ExtractionResult("video", text, warnings, keyframes)

        warnings.append(f"Unsupported extension: {suffix}")
        return ExtractionResult("unknown", "", warnings, keyframes)

    def _extract_text_file(self, input_path: Path) -> str:
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return input_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return input_path.read_text(errors="ignore")

    def _extract_text_from_pdf(self, pdf_path: Path, warnings: List[str]) -> str:
        if PdfReader is None:
            warnings.append("`pypdf` is not installed. Install it to process PDF files.")
            return ""

        pages: List[str] = []
        try:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                pages.append((page.extract_text() or "").strip())
        except Exception as exc:
            warnings.append(f"PDF extraction failed: {exc}")
            return ""

        return "\n".join(part for part in pages if part)

    def _extract_text_from_image(self, image_path: Path, warnings: List[str]) -> str:
        if Image is None or pytesseract is None:
            warnings.append("Install `Pillow` and `pytesseract` for OCR image extraction.")
            return ""

        try:
            prepared = self._prepare_image_for_ocr(image_path)
            return pytesseract.image_to_string(prepared, config="--oem 3 --psm 6").strip()
        except Exception as exc:
            warnings.append(f"Image OCR failed: {exc}")
            return ""

    def _prepare_image_for_ocr(self, image_path: Path):
        image = Image.open(image_path).convert("L")
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = image.filter(ImageFilter.MedianFilter(size=3))
        return image.point(lambda px: 255 if px > 145 else 0)

    def _extract_from_video(
        self, video_path: Path, artifact_dir: Path, warnings: List[str]
    ) -> Tuple[str, List[str]]:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        audio_path = artifact_dir / f"{video_path.stem}_audio.wav"
        transcript = ""
        frame_notes: List[str] = []
        keyframes: List[str] = []

        self._extract_audio_from_video(video_path, audio_path, warnings)
        if audio_path.exists():
            transcript = self._transcribe_audio(audio_path, warnings)

        frame_notes, keyframes = self._extract_keyframe_ocr(video_path, artifact_dir, warnings)
        merged_parts = []
        if transcript.strip():
            merged_parts.append("Audio Transcript:\n" + transcript.strip())
        if frame_notes:
            merged_parts.append("Slide OCR Notes:\n" + "\n".join(frame_notes))

        return "\n\n".join(merged_parts), keyframes

    def _extract_audio_from_video(self, video_path: Path, audio_path: Path, warnings: List[str]) -> None:
        try:
            try:
                from moviepy import VideoFileClip
            except Exception:
                from moviepy.editor import VideoFileClip  # type: ignore
        except Exception:
            warnings.append("Install `moviepy` for extracting audio from video.")
            return

        try:
            with VideoFileClip(str(video_path)) as clip:
                if clip.audio is None:
                    warnings.append("Video has no audio stream.")
                    return
                clip.audio.write_audiofile(str(audio_path), logger=None)
        except Exception as exc:
            warnings.append(f"Video audio extraction failed: {exc}")

    def _extract_keyframe_ocr(
        self, video_path: Path, artifact_dir: Path, warnings: List[str], interval_seconds: int = 20
    ) -> Tuple[List[str], List[str]]:
        if cv2 is None:
            warnings.append("Install `opencv-python` to process video keyframes.")
            return [], []
        if Image is None or pytesseract is None:
            warnings.append("Install `Pillow` and `pytesseract` to run keyframe OCR.")
            return [], []

        frames_dir = artifact_dir / "keyframes"
        frames_dir.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            warnings.append("Could not open video for keyframe extraction.")
            return [], []

        fps = capture.get(cv2.CAP_PROP_FPS) or 1.0
        frame_step = max(int(fps * interval_seconds), 1)

        frame_index = 0
        keyframes: List[str] = []
        notes: List[str] = []
        max_frames = 12

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % frame_step == 0:
                frame_path = frames_dir / f"frame_{frame_index}.jpg"
                cv2.imwrite(str(frame_path), frame)
                keyframes.append(frame_path.as_posix())

                if len(keyframes) <= max_frames:
                    try:
                        ocr_text = self._extract_text_from_image(frame_path, warnings)
                        if ocr_text.strip():
                            snippet = " ".join(ocr_text.split())
                            notes.append(snippet[:280])
                    except Exception:
                        pass

            frame_index += 1

        capture.release()
        return notes, keyframes

    def _transcribe_audio(self, audio_path: Path, warnings: List[str], model_size: str = "base") -> str:
        try:
            import whisper
        except Exception:
            warnings.append(
                "Install `openai-whisper` to transcribe audio/video. "
                "No transcript was produced from the audio track."
            )
            return ""

        try:
            model = _WHISPER_MODELS.get(model_size)
            if model is None:
                model = whisper.load_model(model_size)
                _WHISPER_MODELS[model_size] = model
            result = model.transcribe(str(audio_path), fp16=False)
            return (result.get("text") or "").strip()
        except Exception as exc:
            warnings.append(f"Audio transcription failed: {exc}")
            return ""
