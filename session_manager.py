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

    def cleanup_stale(
        self,
        max_idle_seconds: float = 86400,
        exclude_session_id: str | None = None,
    ) -> list[str]:
        """
        Remove sessions not updated in max_idle_seconds.
        Optionally exclude a session (e.g. current request) from removal.
        Returns list of removed session ids (for syncing agent memory).
        """
        now = time.time()
        to_remove = [
            sid for sid, s in self.sessions.items()
            if sid != exclude_session_id
            and (now - s["updated_at"]) > max_idle_seconds
        ]
        for sid in to_remove:
            del self.sessions[sid]
        return to_remove
