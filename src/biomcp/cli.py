"""BioMCP CLI: registry-driven install, run, diagnostics and client setup."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import __version__
from .config import show as show_config, set_value
from .registry import get_server, installable_servers, load_registry


def _client_paths() -> dict[str, Path]:
    home = Path.home()
    return {
        "generic": home / ".config" / "biomcp" / "mcp.json",
        "claude-desktop": home / ".config" / "Claude" / "claude_desktop_config.json",
    }


def _server_configs(names: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for name in names:
        entry = get_server(name)
        if not entry.get("installable"):
            raise SystemExit(f"{name} is not installable (status: {entry.get('status')})")
        result[f"biomcp_{name}"] = {"command": entry["command"], "args": []}
    return result


def _write_json(path: Path, servers: dict[str, dict]) -> None:
    data: dict = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"Invalid JSON configuration: {path}")
    block = data.setdefault("mcpServers", {})
    if not isinstance(block, dict):
        raise RuntimeError(f"Invalid mcpServers object: {path}")
    block.update(servers)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_codex(path: Path, servers: dict[str, dict]) -> None:
    """Upsert BioMCP-managed Codex MCP blocks without duplicating them."""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    for name, cfg in servers.items():
        block = f'[mcp_servers.{name}]\ncommand = {json.dumps(cfg["command"])}\nargs = []\n'
        pattern = re.compile(
            rf"(?ms)^\[mcp_servers\.{re.escape(name)}\]\n.*?(?=^\[|\Z)"
        )
        if pattern.search(existing):
            existing = pattern.sub(block, existing, count=1)
        else:
            if existing and not existing.endswith("\n"):
                existing += "\n"
            existing += "\n" + block
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing.rstrip() + "\n", encoding="utf-8")


def cmd_list(_: argparse.Namespace) -> int:
    print(f"BioMCP {__version__}\n")
    for entry in load_registry()["servers"]:
        status = "installable" if entry.get("installable") else entry.get("status", "unknown")
        print(f"{entry['name']:16} {status:12} {entry['description']}")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    names = [s.strip() for s in args.servers.split(",")] if args.servers else [e["name"] for e in installable_servers()]
    servers = _server_configs(names)
    clients = [c.strip() for c in args.clients.split(",")]
    for client in clients:
        if client == "codex":
            path = Path.home() / ".codex" / "config.toml"
        else:
            path = _client_paths().get(client)
        if path is None:
            raise SystemExit(f"Unsupported client: {client}")
        if args.dry_run:
            print(json.dumps({"client": client, "path": str(path), "mcpServers": servers}, indent=2))
        elif client == "codex":
            _write_codex(path, servers)
            print(f"configured {path}")
        else:
            _write_json(path, servers)
            print(f"configured {path}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    entries = installable_servers()
    if args.server:
        entries = [get_server(args.server)]
    failures = 0
    for entry in entries:
        command = str(entry["command"])
        ok = shutil.which(command) is not None
        print(f"{entry['name']:16} {'OK' if ok else 'MISSING':8} {command}")
        failures += int(not ok)
    return 1 if failures else 0


def cmd_run(args: argparse.Namespace) -> int:
    entry = get_server(args.server)
    if not entry.get("installable"):
        raise SystemExit(f"{args.server} is not installable (status: {entry.get('status')})")
    command = str(entry["command"])
    if shutil.which(command) is None:
        raise SystemExit(f"Command not found: {command}. Run `biomcp doctor`.")
    return subprocess.run([command, *args.extra], check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="biomcp", description="Open-source MCP platform for biology and bioimaging")
    parser.add_argument("--version", action="version", version=f"BioMCP {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list", help="list all registered servers")
    p.set_defaults(func=cmd_list)
    p = sub.add_parser("install", help="configure selected servers for MCP clients")
    p.add_argument("--servers", help="comma-separated server ids; default is all installable servers")
    p.add_argument("--clients", default="generic", help="generic, claude-desktop, codex")
    p.add_argument("--dry-run", action="store_true", help="print changes without writing")
    p.set_defaults(func=cmd_install)
    p = sub.add_parser("doctor", help="check registered server executables")
    p.add_argument("--server")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("run", help="launch a registered MCP server over stdio")
    p.add_argument("server")
    p.add_argument("extra", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("config", help="inspect or edit persistent BioMCP configuration")
    cfg = p.add_subparsers(dest="config_command", required=True)
    q = cfg.add_parser("show")
    q.set_defaults(func=lambda _: print(show_config()) or 0)
    q = cfg.add_parser("set")
    q.add_argument("section_key")
    q.add_argument("value")
    def _set(args: argparse.Namespace) -> int:
        section, key = args.section_key.split(".", 1)
        set_value(section, key, args.value)
        return 0
    q.set_defaults(func=_set)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
