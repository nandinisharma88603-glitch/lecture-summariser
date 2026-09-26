from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from smart_lecture_summarizer.config import (
    ALLOWED_EXTENSIONS,
    BASE_DIR,
    OUTPUT_DIR,
    UPLOAD_DIR,
    ensure_directories,
)
from smart_lecture_summarizer.pipeline import SmartLecturePipeline

app = Flask(__name__)
app.secret_key = "smart-lecture-summarizer-secret-key"

ensure_directories()
pipeline = SmartLecturePipeline()


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    uploaded = request.files.get("lecture_file")
    summary_length = request.form.get("summary_length", "medium")

    if uploaded is None or uploaded.filename == "":
        flash("Please upload a file first.")
        return redirect(url_for("index"))

    if not allowed_file(uploaded.filename):
        flash("Unsupported file type. Upload text, PDF, image, audio, or video.")
        return redirect(url_for("index"))

    job_id = uuid.uuid4().hex[:10]
    safe_name = secure_filename(uploaded.filename)
    input_path = UPLOAD_DIR / f"{job_id}_{safe_name}"
    uploaded.save(input_path)

    try:
        result = pipeline.run(input_path=input_path, summary_length=summary_length, job_id=job_id)
    except Exception as exc:  # pragma: no cover - runtime safety for UX
        flash(f"Processing failed: {exc}")
        return redirect(url_for("index"))

    result_path = OUTPUT_DIR / f"{job_id}_result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return render_template(
        "result.html",
        filename=safe_name,
        result=result,
        generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
    )


@app.route("/download/<pdf_name>", methods=["GET"])
def download(pdf_name: str):
    pdf_path = OUTPUT_DIR / secure_filename(pdf_name)
    if not pdf_path.exists():
        flash("Requested PDF could not be found.")
        return redirect(url_for("index"))
    return send_file(pdf_path, as_attachment=True, download_name=pdf_path.name)


if __name__ == "__main__":
    app.run(debug=True)
