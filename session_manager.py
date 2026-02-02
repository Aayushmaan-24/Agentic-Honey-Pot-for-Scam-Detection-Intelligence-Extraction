from typing import Dict, Any
import time


class SessionManager:
    def __init__(self):
        # In-memory session store
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str) -> Dict[str, Any]:
        session = {
            "sessionId": session_id,
            "confidence": 0.0,
            "agent_active": False,
            "total_messages": 0,
            "intelligence": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            },
            "callback_sent": False,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]

    def update_confidence(self, session_id: str, delta: float):
        session = self.get_session(session_id)
        session["confidence"] = min(1.0, session["confidence"] + delta)
        session["updated_at"] = time.time()

    def activate_agent(self, session_id: str):
        session = self.get_session(session_id)
        session["agent_active"] = True
        session["updated_at"] = time.time()

    def increment_message_count(self, session_id: str):
        session = self.get_session(session_id)
        session["total_messages"] += 1
        session["updated_at"] = time.time()

    def add_intelligence(self, session_id: str, key: str, values: list):
        """
        key must be one of:
        bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords
        """
        session = self.get_session(session_id)
        existing = set(session["intelligence"].get(key, []))
        for v in values:
            if v not in existing:
                session["intelligence"][key].append(v)
        session["updated_at"] = time.time()

    def mark_callback_sent(self, session_id: str):
        session = self.get_session(session_id)
        session["callback_sent"] = True
        session["updated_at"] = time.time()
