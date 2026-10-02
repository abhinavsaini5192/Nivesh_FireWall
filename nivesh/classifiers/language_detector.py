"""Language detection classifier for Engine 1.

Supports:
- English ('en')
- Hindi in Devanagari script ('hi')
- Hinglish ('hinglish') - Romanized Hindi or mixed Hindi-English code-switching

Never translates content. Produces language code and confidence score.
"""

import re
from typing import Tuple

# Devanagari character range regex
DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")

# Common transliterated Hindi words / particles used in Indian conversational English (Hinglish)
HINGLISH_VOCABULARY = {
    "hai", "hain", "karo", "karein", "karna", "karne", "abhi", "paise", "paisa",
    "bhai", "dekho", "dekhiye", "milega", "milegi", "hoga", "hogi", "aap", "aapko",
    "hum", "mera", "meri", "mere", "dost", "dosto", "kamaye", "kamana", "chahiye",
    "hota", "hoti", "loot", "yahan", "wahan", "suno", "namaste", "dhanyawad",
    "munafa", "nivesh", "khata", "kijiye", "jaldi", "pakka", "sach", "batao",
    "bhejo", "bhejiye", "kya", "kyun", "kaise", "kab", "sabhi", "sab", "achha",
    "accha", "badhiya", "zabardast", "bano", "banoge", "lijiye", "dijiye", "mat",
    "sahi", "galat", "sirji", "bhaiya", "rupaye", "rupiya", "lao", "milte", "rakam"
}

# Common English stopwords for lexical identification
ENGLISH_COMMON_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their",
    "what", "so", "up", "out", "if", "about", "who", "get", "which",
    "go", "me", "when", "make", "can", "like", "time", "no", "just",
    "him", "know", "take", "people", "into", "year", "your", "good",
    "some", "could", "them", "see", "other", "than", "then", "now",
    "look", "only", "come", "its", "over", "think", "also", "back",
    "after", "use", "two", "how", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give",
    "day", "most", "us", "group", "advisor", "registered", "returns",
    "investment", "invest", "trading", "download", "join", "app", "pay",
    "contact", "guaranteed", "profit", "loss", "market", "stock"
}


class LanguageDetector:
    """Detects primary language and dialect (English, Hindi, Hinglish)."""

    def detect(self, text: str) -> Tuple[str, float]:
        """Returns (language_code, confidence).
        
        Languages:
        - 'en': English
        - 'hi': Hindi (Devanagari script)
        - 'hinglish': Hindi-English code-mixed or Romanized Hindi
        """
        if not text or not text.strip():
            return "en", 1.0

        clean_text = text.strip()

        # 1. Check for Devanagari script
        devanagari_chars = len(DEVANAGARI_PATTERN.findall(clean_text))
        total_letters = sum(1 for c in clean_text if c.isalpha())

        if total_letters > 0:
            devanagari_ratio = devanagari_chars / total_letters
            if devanagari_ratio > 0.40:
                confidence = min(0.99, round(0.70 + (devanagari_ratio * 0.29), 2))
                return "hi", confidence

        # 2. Check tokens for Hinglish vs English in Latin script
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{2,}\b", clean_text)]
        if not words:
            return "en", 0.80

        hinglish_count = sum(1 for w in words if w in HINGLISH_VOCABULARY)
        english_count = sum(1 for w in words if w in ENGLISH_COMMON_WORDS)

        # If any significant Hinglish vocabulary is detected, it is Hinglish (mixed)
        if hinglish_count >= 1:
            hinglish_density = hinglish_count / len(words)
            # Mixed language: e.g. "Sir guaranteed return hai, abhi join karo"
            confidence = min(0.98, round(0.75 + min(0.23, hinglish_density * 0.5), 2))
            return "hinglish", confidence

        # If predominantly English
        if english_count > 0:
            english_ratio = english_count / len(words)
            confidence = min(0.99, round(0.80 + (english_ratio * 0.19), 2))
            return "en", confidence

        return "en", 0.75
