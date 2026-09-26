# 🎓 Smart Lecture Summarizer — AI-Powered Lecture to Notes

[![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web_App-black?style=flat&logo=flask)](https://flask.palletsprojects.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-yellow?style=flat&logo=huggingface)](https://huggingface.co)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=flat&logo=openai)](https://github.com/openai/whisper)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

## 🧠 Overview

**Smart Lecture Summarizer** is an AI-powered web application that converts long lecture materials — text, PDFs, images, audio, and video — into concise structured notes and downloadable PDF summaries.

Built with a modular pipeline architecture using state-of-the-art NLP, OCR, and speech-to-text technologies.

---

## ✨ Features

| Input Type | Processing Method |
|---|---|
| 📄 Text / Markdown | Direct NLP summarization |
| 📑 PDF Handouts | PyPDF text extraction |
| 🖼️ Image Slides | OCR via PyTesseract + Pillow |
| 🎙️ Audio Lectures | Speech-to-text via OpenAI Whisper |
| 🎥 Video Lectures | Audio transcription + Keyframe OCR |

### Output
- ✅ Concise structured notes
- ✅ Key points extraction
- ✅ Downloadable PDF summary
- ✅ Graceful fallback if dependencies unavailable

---

## 🏗️ Architecture

```
User Upload (Web UI)
        │
        ▼
┌─────────────────────┐
│   Pipeline          │  ← Auto-detects input type
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Extractor│ │ Input Types  │
│        │ │ • PDF        │
│        │ │ • Image/OCR  │
│        │ │ • Audio      │
│        │ │ • Video      │
└────┬───┘ └──────────────┘
     │
     ▼
┌─────────────────────┐
│   NLP Engine        │  ← HuggingFace Transformers
│   (Summarization)   │     Extractive fallback
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   PDF Exporter      │  ← ReportLab
│   (Download Notes)  │
└─────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.x |
| Web Framework | Flask |
| AI Summarization | HuggingFace Transformers (abstractive) |
| Fallback NLP | Extractive summarizer (offline) |
| Speech-to-Text | OpenAI Whisper |
| PDF Extraction | PyPDF |
| OCR | PyTesseract + Pillow |
| Video Processing | OpenCV + MoviePy |
| PDF Generation | ReportLab |
| Frontend | HTML, CSS |

---

## 📁 Project Structure

```
smart-lecture-summarizer/
│
├── app.py                  ← Flask entry point
├── requirements.txt        ← Python dependencies
├── style.css               ← Frontend styling
│
├── config/                 ← App configuration
├── extractor/              ← Input extraction modules
│   ├── pdf_extractor.py
│   ├── image_extractor.py
│   ├── audio_extractor.py
│   └── video_extractor.py
│
├── nlp_engine/             ← Summarization logic
│   ├── abstractive.py      ← HuggingFace transformer
│   └── extractive.py       ← Offline fallback
│
├── pipeline/               ← Auto-detection pipeline
│   └── pipeline.py
│
├── pdf_exporter/           ← PDF generation
│   └── exporter.py
│
└── templates/
    ├── base.html
    ├── index.html          ← Upload page
    └── result.html         ← Summary output page
```

---

## 🚀 Setup & Run

### 1. Clone the Repository
```bash
git clone https://github.com/Miini252003/smart-lecture-summarizer.git
cd smart-lecture-summarizer
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies

**Tesseract OCR** (required for image/slide processing):
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- Windows: [Download installer](https://github.com/tesseract-ocr/tesseract)
- Mac: `brew install tesseract`

**FFmpeg** (required for audio/video processing):
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Windows: [Download](https://ffmpeg.org/download.html)
- Mac: `brew install ffmpeg`

### 5. Run the App
```bash
python app.py
```

### 6. Open in Browser
```
http://127.0.0.1:5000
```

---

## 📦 Key Dependencies

```
flask
transformers
torch
openai-whisper
pypdf
Pillow
pytesseract
opencv-python
moviepy
reportlab
```

---

## ⚙️ How It Works

```
Step 1 → Upload your lecture file via the web interface
Step 2 → Pipeline auto-detects the source type
Step 3 → Content extraction is applied:
          • PDF → text extraction
          • Image → OCR
          • Audio → Whisper transcription
          • Video → audio transcription + keyframe OCR
Step 4 → AI/NLP summarization generates concise notes
Step 5 → Download your summary as a PDF
```

---

## 🔄 Fallback Behavior

| Scenario | Behavior |
|---|---|
| Transformer model fails to load | Automatically uses extractive NLP summarizer |
| Whisper not installed | App runs, shows warning on result page |
| OCR dependencies missing | App runs, shows warning on result page |

> The app is designed for **graceful degradation** — it always tries to deliver a summary even if some components are unavailable.

---

## 🔬 Limitations & Future Work

### Current Limitations
- Transformer model loading requires internet on first run
- Large video files may take longer to process
- OCR accuracy depends on image/slide quality

### Future Work
- Add support for YouTube URL input
- Multilingual summarization
- Chapter-wise breakdown for long lectures
- Integration with LangChain for Q&A on lecture content

---

## 👩‍💻 Author

**Divyanshi Rana**
B.Tech Computer Science & Engineering (AI/ML)
IIMT College of Engineering, Greater Noida, Uttar Pradesh

---

## 📫 Connect

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Divyanshi_Rana-0077B5?style=flat&logo=linkedin)](https://linkedin.com/in/divyanshi-rana)
[![GitHub](https://img.shields.io/badge/GitHub-Miini252003-181717?style=flat&logo=github)](https://github.com/Miini252003)
[![Email](https://img.shields.io/badge/Email-divyanshirana2004@gmail.com-D14836?style=flat&logo=gmail)](mailto:divyanshirana2004@gmail.com)

---

## ⭐ Star This Repo

If you found this project useful, please give it a ⭐ — it helps others discover it!
