from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests
import time

from session_manager import SessionManager
from detector import detect_scam
from agent import generate_reply
from extract import extract_intelligence

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise RuntimeError("API_KEY not found in .env file")

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# FastAPI app
app = FastAPI(title="Agentic Honeypot API")


# Session manager (in-memory)
session_manager = SessionManager()

# Request models (GUVI spec)
class Message(BaseModel):
    sender: str
    text: str
    timestamp: str


class IncomingRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: list = []
    metadata: dict = {}

# Helper: merge intelligence into session
def merge_intelligence(session_id: str, intel: dict):
    for key, values in intel.items():
        if not values:
            continue
        session_manager.add_intelligence(session_id, key, values)

# Helper: decide when to finish engagement
def should_finalize(session: dict) -> bool:
    intel = session["intelligence"]
    has_core_intel = (
        len(intel.get("upiIds", [])) > 0 or
        len(intel.get("phishingLinks", [])) > 0 or
        len(intel.get("phoneNumbers", [])) > 0 or
        len(intel.get("bankAccounts", [])) > 0
    )
    enough_turns = session["total_messages"] >= 8
    return has_core_intel and enough_turns

# Helper: send GUVI callback (exactly once)
def send_guvi_callback(session: dict):
    #print("✅ GUVI CALLBACK TRIGGERED for session:", session["sessionId"])
    payload = {
        "sessionId": session["sessionId"],
        "scamDetected": True,
        "totalMessagesExchanged": session["total_messages"],
        "extractedIntelligence": session["intelligence"],
        "agentNotes": "Scammer used urgency and verification tactics to solicit sensitive details."
    }

    try:
        requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        session_manager.mark_callback_sent(session["sessionId"])
    except Exception:
        # Fail-safe: do not crash the API
        pass

# Main endpoint
@app.post("/honeypot/message")
def handle_message(
    body: IncomingRequest,
    x_api_key: str = Header(None)
):
    # 1️ API key validation
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = body.sessionId
    message_text = body.message.text
    sender = body.message.sender

    # 2️ Only respond to scammer messages
    if sender != "scammer":
        return {"status": "ignored", "reply": ""}

    # 3️ Load or create session
    session = session_manager.get_session(session_id)

    # 4️ Increment message count
    session_manager.increment_message_count(session_id)

    # 5️ Scam detection
    is_scam, scam_confidence = detect_scam(message_text)

    # 6️ Update confidence if scam detected
    if is_scam:
        session_manager.update_confidence(
            session_id,
            delta=scam_confidence * 0.4
        )

    # 7️ Activate agent if threshold crossed
    if session["confidence"] >= 0.6 and not session["agent_active"]:
        session_manager.activate_agent(session_id)

    # 8️ Generate reply
    if session["agent_active"]:
        reply_text = generate_reply(message_text)
    else:
        reply_text = "I am not very sure what this means. Can you please explain?"

    # 9️ Build cumulative text for extraction
    history_text = " ".join(
        m.get("text", "") for m in body.conversationHistory
    )
    cumulative_text = f"{history_text} {message_text} {reply_text}"

    # 10 Extract & merge intelligence
    intel = extract_intelligence(cumulative_text)
    merge_intelligence(session_id, intel)

    # 1️1️ Finalize & callback (exactly once)
    if (
        session["agent_active"]
        and not session["callback_sent"]
        and should_finalize(session)
    ):
        send_guvi_callback(session)

    # 1️2️ Return GUVI-compatible response
    return {
        "status": "success",
        "reply": reply_text
    }
