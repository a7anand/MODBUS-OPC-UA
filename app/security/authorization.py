# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Role-based authorization."""

from __future__ import annotations

from app.core.config_schema import GatewayDocument
from app.core.enums import UserRole


class AuthorizationService:
    def __init__(self, doc: GatewayDocument) -> None:
        self._doc = doc

    def role_for(self, username: str) -> UserRole:
        for user in self._doc.security.users:
            if user.username == username:
                return user.role
        if not self._doc.security.require_auth:
            return UserRole.ADMINISTRATOR
        return UserRole.VIEWER

    def can_write(self, username: str) -> bool:
        role = self.role_for(username)
        return role in (
            UserRole.ADMINISTRATOR,
            UserRole.ENGINEER,
            UserRole.OPERATOR,
        )
