from transformers import pipeline
from typing import Tuple

# Load scam / phishing model (CPU, local)
# Lightweight and hackathon-safe
_detector = pipeline(
    "text-classification",
    model="cybersectony/phishing-email-detection-distilbert_v2.1",
    truncation=True
)

# Keyword lists
# General suspicious keywords (need multiple hits)
SUSPICIOUS_KEYWORDS = [
    "urgent",
    "verify",
    "account",
    "blocked",
    "suspended",
    "kyc",
    "refund",
    "debit",
    "credit",
    "bank",
    "upi"
]

# Strong scam indicators (single hit is enough)
STRONG_KEYWORDS = {
    "otp",
    "upi pin",
    "pin",
    "one time password"
}


def detect_scam(text: str) -> Tuple[bool, float]:
    """
    Detect whether a message is likely a scam.

    Returns:
        is_scam (bool)
        scam_confidence (float between 0 and 1)
    """

    text_lower = text.lower()

    # 1️ Model-based prediction

    result = _detector(text_lower, max_length=512)[0]

    label = result["label"].lower()
    raw_score = float(result["score"])

    is_scam = False

    # Many models use labels like PHISHING / SPAM / FRAUD
    if "phish" in label or "spam" in label or "fraud" in label:
        is_scam = True

    # 2️ Strong keyword override (India-specific reality)
   
    if any(sk in text_lower for sk in STRONG_KEYWORDS):
        is_scam = True
        raw_score = max(raw_score, 0.85)

    # 3️ General keyword reinforcement
  
    keyword_hits = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in text_lower)

    if keyword_hits >= 2:
        is_scam = True
        raw_score = max(raw_score, 0.6)

    # 4️ Normalize score to "scam confidence"
    
    if is_scam:
        scam_confidence = raw_score
    else:
        scam_confidence = raw_score  # high confidence that it is NOT a scam

    return is_scam, scam_confidence