from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - optional dependency
    A4 = None
    canvas = None


class PDFExporter:
    def export_summary(self, payload: Dict, output_path: Path) -> None:
        if canvas is None or A4 is None:
            raise RuntimeError("`reportlab` is not installed. Install it to enable PDF export.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        left = 45
        right = width - 45
        y = height - 55
        line_height = 15

        c.setFont("Helvetica-Bold", 16)
        c.drawString(left, y, "Smart Lecture Summary")
        y -= 28

        c.setFont("Helvetica", 10)
        c.drawString(left, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y -= 20

        y = self._section_title(c, left, y, "Overview")
        overview_text = payload.get("summary_text", "No summary available.")
        y = self._draw_paragraph(c, overview_text, left, right, y, line_height)

        key_points: List[str] = payload.get("key_points", [])
        y = self._section_title(c, left, y, "Key Points")
        if not key_points:
            y = self._draw_paragraph(c, "No key points identified.", left, right, y, line_height)
        else:
            for point in key_points:
                y = self._draw_bullet(c, point, left, right, y, line_height)
                if y < 70:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 50

        keywords = payload.get("keywords", [])
        y = self._section_title(c, left, y, "Keywords")
        keywords_line = ", ".join(keywords) if keywords else "No keywords extracted."
        y = self._draw_paragraph(c, keywords_line, left, right, y, line_height)

        source_meta = payload.get("source", {})
        y = self._section_title(c, left, y, "Source Metadata")
        source_lines = [
            f"Source Type: {source_meta.get('source_type', 'unknown')}",
            f"Input File: {source_meta.get('input_file', 'N/A')}",
            f"Summarization Method: {payload.get('method', 'N/A')}",
            f"Text Length: {source_meta.get('text_length', 0)} characters",
        ]
        for line in source_lines:
            y = self._draw_paragraph(c, line, left, right, y, line_height)

        warnings = payload.get("warnings", [])
        if warnings:
            y = self._section_title(c, left, y, "Warnings")
            for note in warnings:
                y = self._draw_bullet(c, note, left, right, y, line_height)
                if y < 70:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 50

        c.save()

    def _section_title(self, c, left: int, y: float, title: str) -> float:
        if y < 80:
            c.showPage()
            y = A4[1] - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left, y, title)
        return y - 18

    def _draw_bullet(
        self,
        c,
        text: str,
        left: int,
        right: float,
        y: float,
        line_height: int,
    ) -> float:
        wrapped = self._wrap_text(c, text, right - (left + 18))
        c.setFont("Helvetica", 11)
        if wrapped:
            c.drawString(left, y, u"\u2022")
            c.drawString(left + 12, y, wrapped[0])
            y -= line_height
            for line in wrapped[1:]:
                c.drawString(left + 12, y, line)
                y -= line_height
        return y - 4

    def _draw_paragraph(
        self,
        c,
        text: str,
        left: int,
        right: float,
        y: float,
        line_height: int,
    ) -> float:
        c.setFont("Helvetica", 11)
        lines = self._wrap_text(c, text, right - left)
        for line in lines:
            if y < 70:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = A4[1] - 50
            c.drawString(left, y, line)
            y -= line_height
        return y - 6

    def _wrap_text(self, c, text: str, max_width: float) -> List[str]:
        words = text.split()
        if not words:
            return [""]

        lines: List[str] = []
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if c.stringWidth(trial, "Helvetica", 11) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines
