"""BioMCP command-line interface."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from . import __version__
from .registry import get_server, installable_servers, load_registry


def _paths() -> dict[str, Path]:
    home = Path.home()
    return {
        "generic": home / ".config" / "biomcp" / "mcp.json",
        "claude-desktop": home / ".config" / "Claude" / "claude_desktop_config.json",
        "codex": home / ".codex" / "config.toml",
    }


def _write_json(path: Path, servers: dict) -> None:
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"Invalid JSON config: {path}")
    target = data.setdefault("mcpServers", {})
    if not isinstance(target, dict):
        raise RuntimeError(f"Invalid mcpServers object: {path}")
    target.update(servers)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _config_servers(names: list[str]) -> dict:
    result = {}
    for name in names:
        entry = get_server(name)
        if not entry.get("installable"):
            raise SystemExit(f"{name} is not installable (status: {entry.get('status')}).")
        result[f"biomcp_{name}"] = {"command": entry["command"], "args": []}
    return result


def cmd_list(_: argparse.Namespace) -> int:
    print(f"BioMCP {__version__}\n")
    for entry in load_registry()["servers"]:
        flag = "installable" if entry.get("installable") else entry.get("status", "unknown")
        print(f"{entry['name']:16} {flag:12} {entry['description']}")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    names = args.servers.split(",") if args.servers else [e["name"] for e in installable_servers()]
    servers = _config_servers(names)
    clients = args.clients.split(",")
    paths = _paths()
    for client in clients:
        if client not in paths:
            raise SystemExit(f"Unsupported client: {client}")
        path = paths[client]
        if args.dry_run:
            print(json.dumps({"path": str(path), "mcpServers": servers}, indent=2))
        elif path.suffix == ".json":
            _write_json(path, servers)
            print(f"configured {path}")
        else:
            print(f"Codex TOML configuration is not auto-written yet: {path}")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    print(f"BioMCP {__version__} doctor\n")
    for entry in installable_servers():
        command = str(entry["command"])
        found = shutil.which(command)
        print(f"{entry['name']:16} {'OK' if found else 'MISSING':8} {command}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    entry = get_server(args.server)
    if not entry.get("installable"):
        raise SystemExit(f"{args.server} is not installable (status: {entry.get('status')}).")
    return subprocess.run([entry["command"], *args.extra], check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="biomcp", description="Open-source MCP platform for biology and bioimaging")
    parser.add_argument("--version", action="version", version=f"BioMCP {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list", help="show the BioMCP server registry")
    p.set_defaults(func=cmd_list)
    p = sub.add_parser("install", help="configure installable BioMCP servers")
    p.add_argument("--servers", help="comma-separated server ids")
    p.add_argument("--clients", default="generic", help="comma-separated clients")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_install)
    p = sub.add_parser("doctor", help="diagnose local MCP server availability")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("run", help="run a registered MCP server over stdio")
    p.add_argument("server")
    p.add_argument("extra", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_run)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
