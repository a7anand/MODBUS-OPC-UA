# Copyright (c) 2026 Aman Anand, M (T&I), Barauni
"""Detect mapping feedback loops (PDF §12)."""

from __future__ import annotations

from app.core.config_schema import GatewayDocument, MappingDefinition
from app.core.enums import MappingDirection


def find_feedback_cycles(doc: GatewayDocument) -> list[str]:
    """Return human-readable warnings for bidirectional loops on the same tag."""
    warnings: list[str] = []
    by_tag: dict[str, list[MappingDefinition]] = {}
    for m in doc.mappings:
        if not m.enabled:
            continue
        by_tag.setdefault(m.tag_name, []).append(m)
    for tag, maps in by_tag.items():
        dirs = {m.direction for m in maps}
        if MappingDirection.BIDIRECTIONAL in dirs or (
            MappingDirection.MB_TO_UA in dirs and MappingDirection.UA_TO_MB in dirs
        ):
            warnings.append(f"Tag '{tag}' has conflicting mapping directions (feedback risk)")
    # Simple 2-node cycle: tag A writes to B via mapping ids (future graph)
    return warnings


def validate_mappings(doc: GatewayDocument) -> list[str]:
    errors = list(find_feedback_cycles(doc))
    names = {t.name for t in doc.tags}
    for m in doc.mappings:
        if m.tag_name not in names:
            errors.append(f"Mapping {m.id} references unknown tag {m.tag_name}")
    return errors
