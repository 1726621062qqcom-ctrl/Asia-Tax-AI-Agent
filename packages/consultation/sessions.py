"""Bounded in-memory local demo sessions; never persist prompts or credentials."""
from __future__ import annotations

from dataclasses import dataclass, field
import secrets
import threading
import time

from packages.consultation.schemas import Fact


@dataclass
class Session:
    token: str
    synthetic_acknowledged: bool
    touched: float
    messages: list[str] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    responses: dict = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)
    active: bool = True


class SessionStore:
    def __init__(self, *, ttl: int = 3600, capacity: int = 100, clock=time.monotonic):
        self.ttl, self.capacity, self.clock = ttl, capacity, clock
        self.sessions: dict[str,Session] = {}
        self.lock = threading.Lock()

    def create(self, synthetic_acknowledged: bool) -> Session:
        with self.lock:
            now = self.clock()
            for token,session in list(self.sessions.items()):
                if now-session.touched > self.ttl and not session.lock.locked():
                    session.active = False
                    del self.sessions[token]
            if len(self.sessions) >= self.capacity:
                raise OverflowError('session capacity reached')
            token = secrets.token_urlsafe(32)
            session = Session(token,synthetic_acknowledged,now)
            self.sessions[token] = session
            return session

    def get(self, token: str | None) -> Session:
        with self.lock:
            session = self.sessions.get(token or '')
            if session is None or not session.active:
                raise KeyError('session not found')
            if self.clock()-session.touched > self.ttl:
                session.active = False
                del self.sessions[session.token]
                raise KeyError('session expired')
            session.touched = self.clock()
            return session

    def delete(self, token: str | None):
        with self.lock:
            session = self.sessions.pop(token or '',None)
            if session:
                session.active = False
