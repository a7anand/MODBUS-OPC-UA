# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Generate self-signed OPC UA lab certificate (PDF §29)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate_self_signed(
    dest_dir: Path,
    common_name: str = "ModbusOPCUAGateway",
    days_valid: int = 365,
) -> Path:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    dest_dir.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=days_valid))
        .sign(key, hashes.SHA256())
    )
    key_path = dest_dir / "gateway_key.pem"
    cert_path = dest_dir / "gateway_cert.pem"
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return cert_path


def rotate_self_signed(dest_dir: Path, common_name: str = "ModbusOPCUAGateway") -> dict[str, str]:
    """Archive current own cert/key and generate a new pair (PDF §29 rotation UX)."""
    from datetime import datetime, timezone

    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archived: list[str] = []
    for name in ("gateway_cert.pem", "gateway_key.pem"):
        src = dest_dir / name
        if src.exists():
            dst = archive / f"{stamp}_{name}"
            dst.write_bytes(src.read_bytes())
            src.unlink()
            archived.append(str(dst))
    new_cert = generate_self_signed(dest_dir, common_name=common_name)
    return {"certificate": str(new_cert), "archived": archived}
