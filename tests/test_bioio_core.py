from __future__ import annotations

import hashlib
import json

import pytest

from bioio import ExecutionProvenance, ScientificArtifact, sha256_file


def test_sha256_file_streams_and_returns_size(tmp_path):
    path = tmp_path / "sample.bin"
    payload = b"bioio-contract" * 1000
    path.write_bytes(payload)
    digest, size = sha256_file(path, chunk_size=17)
    assert digest == hashlib.sha256(payload).hexdigest()
    assert size == len(payload)


def test_artifact_from_file_and_serialization(tmp_path):
    path = tmp_path / "image.tif"
    path.write_bytes(b"fixture")
    artifact = ScientificArtifact.from_file(
        "image-001", path, "image/tiff",
        metadata={"axes": "YX", "pixel_size_um": 0.25},
    )
    decoded = json.loads(json.dumps(artifact.to_dict(), sort_keys=True))
    assert decoded["artifact_id"] == "image-001"
    assert decoded["size_bytes"] == 7
    assert decoded["metadata"]["axes"] == "YX"
    assert decoded["uri"].startswith("file://")


@pytest.mark.parametrize("kwargs", [
    {"artifact_id": "../bad"},
    {"media_type": "not-a-media-type"},
    {"sha256": "ABC"},
    {"size_bytes": -1},
    {"metadata": {"not_finite": float("nan")}},
    {"uri": "javascript:alert(1)"},
])
def test_artifact_rejects_invalid_fields(kwargs):
    values = {
        "artifact_id": "artifact-1", "media_type": "image/tiff",
        "uri": "file:///tmp/image.tif", "sha256": "a" * 64,
        "size_bytes": 1, "metadata": {},
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        ScientificArtifact(**values)


def test_provenance_serializes_artifact_lineage():
    record = ExecutionProvenance(
        execution_id="run-001", server="bioimage", tool="threshold_image",
        software_version="0.2.0", started_at="2026-11-27T10:00:00Z",
        finished_at="2026-11-27T10:00:02+00:00", status="succeeded",
        input_artifacts=("input-001",), output_artifacts=("mask-001",),
        parameters={"method": "otsu", "channel": 0}, random_seed=42,
    )
    result = record.to_dict()
    assert result["input_artifacts"] == ["input-001"]
    assert result["output_artifacts"] == ["mask-001"]
    assert result["parameters"]["method"] == "otsu"
    assert result["random_seed"] == 42


@pytest.mark.parametrize("overrides", [
    {"status": "success"},
    {"started_at": "2026-11-27T10:00:00"},
    {"finished_at": "2026-11-27T09:59:59Z"},
    {"random_seed": -1},
    {"parameters": {"bad": object()}},
])
def test_provenance_rejects_invalid_records(overrides):
    values = {
        "execution_id": "run-001", "server": "bioimage", "tool": "inspect_image",
        "software_version": "0.2.0", "started_at": "2026-11-27T10:00:00Z",
        "finished_at": "2026-11-27T10:00:01Z", "status": "succeeded",
    }
    values.update(overrides)
    with pytest.raises(ValueError):
        ExecutionProvenance(**values)
