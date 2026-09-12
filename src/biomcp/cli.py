"""BioMCP CLI: registry-driven install, run, diagnostics and client setup."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import __version__
from .config import show as show_config, set_value
from .registry import get_server, installable_servers, load_registry


def _client_paths(*, platform: str | None = None, os_name: str | None = None, home: Path | None = None, path_cls=Path) -> dict[str, Path]:
    """Return platform-appropriate configuration paths for supported clients."""
    platform = sys.platform if platform is None else platform
    os_name = os.name if os_name is None else os_name
    home = Path.home() if home is None else home
    if platform == "darwin":
        claude = home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif os_name == "nt":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is required to configure Claude Desktop on Windows")
        claude = path_cls(appdata) / "Claude" / "claude_desktop_config.json"
    else:
        claude = home / ".config" / "Claude" / "claude_desktop_config.json"

    config_root = os.environ.get("XDG_CONFIG_HOME")
    generic_root = path_cls(config_root) if config_root else home / ".config"
    return {
        "generic": generic_root / "biomcp" / "mcp.json",
        "claude-desktop": claude,
    }


def _server_configs(names: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for name in names:
        entry = get_server(name)
        if not entry.get("installable"):
            raise SystemExit(f"{name} is not installable (status: {entry.get('status')})")
        result[f"biomcp_{name}"] = {"command": entry["command"], "args": []}
    return result


def _atomic_write_text(path: Path, content: str) -> None:
    """Replace a client config atomically while preserving existing permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = (path.stat().st_mode & 0o777) if path.exists() else 0o600
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


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
    _atomic_write_text(path, json.dumps(data, indent=2) + "\n")


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
    _atomic_write_text(path, existing.rstrip() + "\n")


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
