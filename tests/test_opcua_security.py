# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
from __future__ import annotations

from pathlib import Path

from app.core.enums import OpcUaSecurityMode
from app.opcua.cert_generator import generate_self_signed, rotate_self_signed
from app.opcua.security_setup import SECURITY_POLICY_MATRIX, policy_types_for_mode


def test_security_policy_matrix_not_empty():
    assert len(SECURITY_POLICY_MATRIX) >= 3


def test_policy_types_for_sign_and_encrypt():
    types = policy_types_for_mode(OpcUaSecurityMode.SIGN_AND_ENCRYPT)
    assert any("SignAndEncrypt" in t.name for t in types)


def test_cert_rotate_archives(tmp_path: Path):
    own = tmp_path / "own"
    generate_self_signed(own)
    assert (own / "gateway_cert.pem").exists()
    result = rotate_self_signed(own)
    assert Path(result["certificate"]).exists()
    assert result["archived"]
