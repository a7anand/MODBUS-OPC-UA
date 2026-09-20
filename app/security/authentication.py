# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Session authentication."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.core.config_schema import GatewayDocument
from app.security.password_manager import verify_password


@dataclass
class Session:
    token: str
    username: str


class AuthService:
    def __init__(self, doc: GatewayDocument) -> None:
        self._doc = doc
        self._sessions: dict[str, Session] = {}

    def login(self, username: str, password: str) -> Session | None:
        if not self._doc.security.require_auth:
            token = secrets.token_hex(16)
            sess = Session(token=token, username=username or "anonymous")
            self._sessions[token] = sess
            return sess
        for user in self._doc.security.users:
            if user.username == username and user.enabled:
                if verify_password(password, user.password_hash) or not user.password_hash:
                    token = secrets.token_hex(16)
                    sess = Session(token=token, username=username)
                    self._sessions[token] = sess
                    return sess
        return None

    def validate(self, token: str | None) -> Session | None:
        if not self._doc.security.require_auth:
            return Session(token="", username="anonymous")
        if token and token in self._sessions:
            return self._sessions[token]
        return None
