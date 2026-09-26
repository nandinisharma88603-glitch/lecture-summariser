from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "between",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "more",
    "most",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "she",
    "so",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "too",
    "up",
    "us",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
}

SUMMARY_LENGTHS: Dict[str, Tuple[int, int, int]] = {
    "short": (70, 25, 4),
    "medium": (140, 60, 7),
    "long": (220, 100, 10),
}


@dataclass
class SummaryResult:
    summary_text: str
    key_points: List[str]
    keywords: List[str]
    method: str
    warnings: List[str] = field(default_factory=list)


class NLPSummarizer:
    """AI + NLP summarization with a transformer-first strategy."""

    def __init__(self) -> None:
        self._hf_summarizer = None
        self._hf_error: Optional[str] = None

    def summarize(self, text: str, summary_length: str = "medium") -> SummaryResult:
        warnings: List[str] = []
        cleaned = self._normalize_text(text)
        if not cleaned:
            return SummaryResult(
                summary_text="No meaningful text was extracted from the source.",
                key_points=[],
                keywords=[],
                method="none",
                warnings=["Input had no extractable text."],
            )

        length_key = summary_length if summary_length in SUMMARY_LENGTHS else "medium"
        summary = self._summarize_with_transformer(cleaned, length_key, warnings)
        method = "transformers"

        if not summary:
            method = "extractive-nlp"
            summary = self._extractive_summary(cleaned, length_key)
            if self._hf_error:
                warnings.append(f"Transformer summarization unavailable: {self._hf_error}")

        key_points = self._build_key_points(summary)
        keywords = self._extract_keywords(cleaned)

        return SummaryResult(
            summary_text=summary,
            key_points=key_points,
            keywords=keywords,
            method=method,
            warnings=warnings,
        )

    def _summarize_with_transformer(
        self, text: str, summary_length: str, warnings: List[str]
    ) -> Optional[str]:
        summarizer = self._get_hf_summarizer()
        if summarizer is None:
            return None

        max_length, min_length, _ = SUMMARY_LENGTHS[summary_length]
        chunks = self._chunk_text(text, max_words=420)
        partial_summaries: List[str] = []

        for chunk in chunks:
            try:
                response = summarizer(
                    chunk,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                )
                item = response[0]["summary_text"].strip()
                if item:
                    partial_summaries.append(item)
            except Exception as exc:
                warnings.append(f"One chunk could not be summarized by transformer: {exc}")

        if not partial_summaries:
            return None

        merged = " ".join(partial_summaries)
        if len(partial_summaries) == 1:
            return merged

        # Second pass to compress merged summary for large multi-chunk inputs.
        try:
            second_pass = summarizer(
                merged,
                max_length=max_length,
                min_length=max(25, min_length // 2),
                do_sample=False,
            )
            return second_pass[0]["summary_text"].strip()
        except Exception:
            return merged

    def _get_hf_summarizer(self):
        if self._hf_summarizer is not None:
            return self._hf_summarizer
        if self._hf_error is not None:
            return None

        try:
            from transformers import pipeline

            self._hf_summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
            )
            return self._hf_summarizer
        except Exception as exc:
            self._hf_error = str(exc)
            return None

    def _extractive_summary(self, text: str, summary_length: str) -> str:
        _, _, target_sentences = SUMMARY_LENGTHS[summary_length]
        sentences = self._split_sentences(text)
        if len(sentences) <= target_sentences:
            return " ".join(sentences)

        frequency = self._word_frequency(text)
        sentence_scores = []

        for index, sentence in enumerate(sentences):
            words = re.findall(r"[A-Za-z']+", sentence.lower())
            if not words:
                continue
            score = sum(frequency.get(word, 0.0) for word in words) / len(words)
            sentence_scores.append((score, index, sentence))

        top = sorted(sentence_scores, reverse=True)[:target_sentences]
        selected = sorted(top, key=lambda item: item[1])
        return " ".join(sentence for _, _, sentence in selected)

    def _word_frequency(self, text: str) -> Dict[str, float]:
        words = re.findall(r"[A-Za-z']+", text.lower())
        filtered = [w for w in words if len(w) > 2 and w not in STOPWORDS]
        if not filtered:
            return {}

        counts = Counter(filtered)
        max_count = max(counts.values()) or 1
        return {word: value / max_count for word, value in counts.items()}

    def _build_key_points(self, summary: str, max_points: int = 6) -> List[str]:
        sentences = self._split_sentences(summary)
        if not sentences:
            return []
        cleaned = []
        for sentence in sentences[:max_points]:
            plain = sentence.strip().rstrip(".")
            if plain:
                cleaned.append(plain)
        return cleaned

    def _extract_keywords(self, text: str, top_n: int = 12) -> List[str]:
        words = re.findall(r"[A-Za-z']+", text.lower())
        words = [w for w in words if len(w) > 3 and w not in STOPWORDS]
        counts = Counter(words)
        return [word for word, _ in counts.most_common(top_n)]

    def _chunk_text(self, text: str, max_words: int) -> List[str]:
        words = text.split()
        if len(words) <= max_words:
            return [text]
        chunks = []
        for start in range(0, len(words), max_words):
            chunk = " ".join(words[start : start + max_words])
            chunks.append(chunk)
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
