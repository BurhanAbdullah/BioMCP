import json

import pytest

from biomcp.evidence import evidence_digest


def test_evidence_digest_is_order_independent():
    left = {"doctor": {"ok": True, "name": "bioimage"}, "contract": {"ok": True}}
    right = {"contract": {"ok": True}, "doctor": {"name": "bioimage", "ok": True}}
    assert evidence_digest(left) == evidence_digest(right)


def test_evidence_digest_matches_canonical_sha256():
    evidence = {"b": 2, "a": 1}
    expected = __import__("hashlib").sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert evidence_digest(evidence) == expected


def test_evidence_digest_rejects_non_json_values():
    with pytest.raises(TypeError, match="JSON-serializable"):
        evidence_digest({"bad": object()})
