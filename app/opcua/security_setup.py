# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""OPC UA security policy matrix and server/client configuration (PDF §8–9)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from asyncua import ua
from asyncua.crypto.permission_rules import User, UserRole
from asyncua.server.user_managers import UserManager

from app.core.enums import OpcUaSecurityMode

if TYPE_CHECKING:
    from asyncua import Client, Server

logger = logging.getLogger(__name__)

# Documented matrix for operators / Web UI (URI → mode label).
SECURITY_POLICY_MATRIX: list[dict[str, str]] = [
    {
        "id": "none",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#None",
        "mode": "None",
        "description": "Lab only — no signing or encryption",
    },
    {
        "id": "basic256sha256_sign",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
        "mode": "Sign",
        "description": "Sign messages (requires server cert + key)",
    },
    {
        "id": "basic256sha256_sign_encrypt",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
        "mode": "SignAndEncrypt",
        "description": "Sign and encrypt (recommended production baseline)",
    },
    {
        "id": "aes128_sign",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
        "mode": "Sign",
        "description": "AES128-SHA256-RSA-OAEP sign",
    },
    {
        "id": "aes128_sign_encrypt",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
        "mode": "SignAndEncrypt",
        "description": "AES128-SHA256-RSA-OAEP sign and encrypt",
    },
    {
        "id": "aes256_sign",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss",
        "mode": "Sign",
        "description": "AES256-SHA256-RSA-PSS sign",
    },
    {
        "id": "aes256_sign_encrypt",
        "policy_uri": "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss",
        "mode": "SignAndEncrypt",
        "description": "AES256-SHA256-RSA-PSS sign and encrypt",
    },
]


def policy_types_for_mode(mode: OpcUaSecurityMode) -> list[ua.SecurityPolicyType]:
    """Map gateway security_mode to asyncua endpoint policy list."""
    if mode == OpcUaSecurityMode.NONE:
        return [ua.SecurityPolicyType.NoSecurity]
    if mode == OpcUaSecurityMode.SIGN:
        return [
            ua.SecurityPolicyType.Basic256Sha256_Sign,
            ua.SecurityPolicyType.Aes128Sha256RsaOaep_Sign,
            ua.SecurityPolicyType.Aes256Sha256RsaPss_Sign,
        ]
    return [
        ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ua.SecurityPolicyType.Aes128Sha256RsaOaep_SignAndEncrypt,
        ua.SecurityPolicyType.Aes256Sha256RsaPss_SignAndEncrypt,
    ]


def default_cert_paths(cert_base: Path) -> tuple[Path, Path]:
    own = cert_base / "own"
    cert = own / "gateway_cert.pem"
    key = own / "gateway_key.pem"
    return cert, key


async def apply_server_security(
    server: Server,
    mode: OpcUaSecurityMode,
    cert_path: Path | None,
    key_path: Path | None,
    cert_base: Path,
) -> dict[str, Any]:
    """Configure asyncua server policies and load cert/key when required."""
    policies = policy_types_for_mode(mode)
    server.set_security_policy(policies)
    cert, key = cert_path or default_cert_paths(cert_base)[0], key_path or default_cert_paths(cert_base)[1]
    loaded = False
    if mode != OpcUaSecurityMode.NONE:
        if cert.exists() and key.exists():
            await server.load_certificate(str(cert))
            await server.load_private_key(str(key))
            loaded = True
        else:
            logger.warning(
                "OPC UA %s requested but cert/key missing at %s / %s",
                mode.value,
                cert,
                key,
            )
    return {
        "security_mode": mode.value,
        "policies": [p.name for p in policies],
        "certificate_loaded": loaded,
        "certificate_path": str(cert) if cert.exists() else None,
    }


class PasswordUserManager(UserManager):
    """Username/password authentication for OPC UA clients (PDF §9)."""

    def __init__(self, users: dict[str, tuple[str, UserRole]]) -> None:
        self._users = users

    def get_user(
        self,
        iserver: Any,
        username: str | None = None,
        password: str | None = None,
        certificate: Any = None,
    ) -> User | None:
        if not self._users:
            return User(role=UserRole.User)
        if not username or password is None:
            return None
        entry = self._users.get(username)
        if not entry:
            return None
        expected, role = entry
        if password != expected:
            return None
        return User(role=role, name=username)


def build_password_user_manager(
    users: list[tuple[str, str, str]],
) -> PasswordUserManager | None:
    """users: (username, password, role_name) where role_name is Admin or User."""
    if not users:
        return None
    mapping: dict[str, tuple[str, UserRole]] = {}
    for username, password, role_name in users:
        role = UserRole.Admin if role_name.lower() == "admin" else UserRole.User
        mapping[username] = (password, role)
    return PasswordUserManager(mapping)


async def apply_client_security(
    client: Client,
    mode: OpcUaSecurityMode,
    cert_base: Path,
    server_cert_path: Path | None = None,
) -> None:
    """Best-effort client security for outbound OPC UA connections."""
    if mode == OpcUaSecurityMode.NONE:
        return
    cert, key = default_cert_paths(cert_base)
    if not cert.exists() or not key.exists():
        logger.warning("OPC UA client security %s skipped — no own cert/key", mode.value)
        return
    sec_mode = "SignAndEncrypt" if mode == OpcUaSecurityMode.SIGN_AND_ENCRYPT else "Sign"
    server_cert = str(server_cert_path or cert)
    await client.set_security_string(
        f"Basic256Sha256,{sec_mode},{cert},{key},{server_cert}"
    )
