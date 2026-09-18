"""Command-line validation for the packaged BioMCP registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .registry import load_registry


def validate_registries() -> dict[str, object]:
    """Validate repository and packaged registries and return a deterministic summary."""
    repository_path = Path(__file__).resolve().parents[2] / "biomcp" / "registry.json"
    packaged_path = Path(__file__).with_name("registry.json")
    repository = load_registry(repository_path)
    packaged = load_registry(packaged_path)
    if repository != packaged:
        raise ValueError("repository and packaged BioMCP registries differ")

    servers = repository["servers"]
    installable = [entry["name"] for entry in servers if entry.get("installable") is True]
    return {
        "product": repository["product"],
        "schema_version": repository["schema_version"],
        "server_count": len(servers),
        "installable_servers": installable,
        "registry_consistent": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="biomcp-registry", description="Validate BioMCP registry truth")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate lifecycle metadata and repository/package registry consistency")
    args = parser.parse_args(argv)
    if args.command == "validate":
        print(json.dumps(validate_registries(), indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
