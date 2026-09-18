"""BioMCP command line interface.

The CLI is registry driven. Installation, launch, diagnostics and client
configuration consume the same machine readable server metadata.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from . import __version__
from .assess import assess_server
from .config import show as show_config, set_value
from .contracts import validate_server
from .doctor import diagnose
from .lifecycle import snapshot
from .mcp_client import call_tool, discover_tools, json_arguments
from .registry import get_server, installable_servers, load_registry
from .transport import resolve_transport_entry


def _client_paths(*, platform: str | None = None, os_name: str | None = None, home: Path | None = None, path_cls=Path) -> dict[str, Path]:
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


def _server_configs(names: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in names:
        entry = get_server(name)
        if not entry.get("installable"):
            raise SystemExit(f"{name} is not installable (status: {entry.get('status')})")
        transport = resolve_transport_entry(entry, client="default")
        key = f"biomcp_{name}"
        if transport == "stdio":
            result[key] = {"command": entry["command"], "args": list(entry.get("args", []))}
        elif transport == "streamable-http":
            endpoint = entry.get("endpoint")
            if not isinstance(endpoint, str) or not endpoint.strip():
                raise SystemExit(f"{name} declares streamable-http but has no HTTP endpoint")
            result[key] = {"url": endpoint.strip()}
        else:
            raise SystemExit(f"{name} declares unsupported client configuration transport: {transport}")
    return result


def _atomic_write_text(path: Path, content: str) -> None:
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


def _write_json(path: Path, servers: dict[str, dict[str, Any]]) -> None:
    data: dict[str, Any] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"Invalid JSON configuration: {path}")
    block = data.setdefault("mcpServers", {})
    if not isinstance(block, dict):
        raise RuntimeError(f"Invalid mcpServers object: {path}")
    block.update(servers)
    _atomic_write_text(path, json.dumps(data, indent=2) + "\n")


def _write_codex(path: Path, servers: dict[str, dict[str, Any]]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    for name, cfg in servers.items():
        if "url" in cfg:
            block = f'[mcp_servers.{name}]\nurl = {json.dumps(cfg["url"])}\n'
        else:
            args = "[" + ", ".join(json.dumps(x) for x in cfg.get("args", [])) + "]"
            block = f'[mcp_servers.{name}]\ncommand = {json.dumps(cfg["command"])}\nargs = {args}\n'
        pattern = re.compile(rf"(?ms)^\[mcp_servers\.{re.escape(name)}\]\n.*?(?=^\[|\Z)")
        if pattern.search(existing):
            existing = pattern.sub(block, existing, count=1)
        else:
            if existing and not existing.endswith("\n"):
                existing += "\n"
            existing += "\n" + block
    _atomic_write_text(path, existing.rstrip() + "\n")


def _configure_clients(targets: list[tuple[str, Path]], servers: dict[str, dict[str, Any]]) -> None:
    """Write all client configs as one transaction, restoring prior files on failure."""
    snapshots: dict[Path, tuple[bool, bytes, int]] = {}
    for _, path in targets:
        if path in snapshots:
            continue
        if path.exists():
            snapshots[path] = (True, path.read_bytes(), path.stat().st_mode & 0o777)
        else:
            snapshots[path] = (False, b"", 0)
    try:
        for client, path in targets:
            if client == "codex":
                _write_codex(path, servers)
            else:
                _write_json(path, servers)
            print(f"configured {path}")
    except BaseException:
        for path, (existed, content, mode) in snapshots.items():
            try:
                if existed:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    _atomic_write_text(path, content.decode("utf-8"))
                    os.chmod(path, mode)
                elif path.exists():
                    path.unlink()
            except OSError:
                pass
        raise


def _missing_dependencies(entry: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for module in entry.get("dependencies", []):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def _install_extra(entry: dict[str, Any]) -> bool:
    extra = entry.get("package_extra")
    missing = _missing_dependencies(entry)
    if not extra or not missing:
        return False
    distribution = entry.get("distribution", "biomcp")
    spec = f"{distribution}[{extra}]"
    print(f"Installing {spec} for missing dependencies: {', '.join(missing)}")
    subprocess.run([sys.executable, "-m", "pip", "install", spec], check=True)
    return True


def _install_selected(names: list[str], *, dry_run: bool = False) -> None:
    for name in names:
        entry = get_server(name)
        if dry_run:
            missing = _missing_dependencies(entry)
            extra = entry.get("package_extra")
            if extra and missing:
                print(f"would install biomcp[{extra}] for {name}: {', '.join(missing)}")
            continue
        _install_extra(entry)


def _verify_installed(names: list[str]) -> int:
    """Verify each installed server against prerequisites and live MCP discovery."""
    failures = 0
    for name in names:
        result = assess_server(name)
        print(json.dumps(result, indent=2, sort_keys=True))
        if result["status"] != "ready":
            failures += 1
    return failures


def _client_targets(clients: list[str]) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    paths = _client_paths()
    for client in clients:
        if client == "codex":
            path = Path.home() / ".codex" / "config.toml"
        else:
            path = paths.get(client)
        if path is None:
            raise SystemExit(f"Unsupported client: {client}")
        targets.append((client, path))
    return targets


def _server_targets(names: list[str]) -> list[str]:
    """Validate all requested servers before any dependency installation."""
    for name in names:
        try:
            entry = get_server(name)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        if not entry.get("installable"):
            raise SystemExit(f"{name} is not installable (status: {entry.get('status')})")
    return names


def _installation_plan(names: list[str], targets: list[tuple[str, Path]]) -> dict[str, Any]:
    """Build a deterministic, side-effect-free installer plan from registry truth."""
    servers: list[dict[str, Any]] = []
    for name in names:
        entry = get_server(name)
        servers.append({
            "name": name,
            "status": entry["status"],
            "package_extra": entry.get("package_extra"),
            "missing_dependencies": _missing_dependencies(entry),
            "command": entry["command"],
            "args": list(entry.get("args", [])),
        })
    return {
        "product": load_registry()["product"],
        "servers": servers,
        "clients": [{"name": client, "path": str(path)} for client, path in targets],
        "configuration": _server_configs(names),
    }


def cmd_list(_: argparse.Namespace) -> int:
    print(f"BioMCP {__version__}\n")
    print(f"{'server':16} {'status':12} {'transport':22} description")
    print("-" * 100)
    for entry in load_registry()["servers"]:
        status = "installable" if entry.get("installable") else entry.get("status", "unknown")
        transport = ",".join(entry.get("transport", [])) or "none"
        print(f"{entry['name']:16} {status:12} {transport:22} {entry['description']}")
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    tools = discover_tools(args.server)
    print(json.dumps(tools, indent=2, sort_keys=True))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate_server(args.server)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def cmd_assess(args: argparse.Namespace) -> int:
    if not args.all and not args.server:
        raise SystemExit("assess requires a server id or --all")
    names = [entry["name"] for entry in installable_servers()] if args.all else [args.server]
    if args.all and not names:
        raise SystemExit("No installable BioMCP servers available for assessment")
    results = [assess_server(name) for name in names]
    if args.all:
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(item["status"] == "ready" for item in results) else 1
    print(json.dumps(results[0], indent=2, sort_keys=True))
    return 0 if results[0]["status"] == "ready" else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    result = diagnose(args.server) if args.server else diagnose()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


def cmd_lifecycle(args: argparse.Namespace) -> int:
    try:
        result = snapshot(args.server)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    names = _server_targets([item.strip() for item in args.servers.split(",") if item.strip()])
    clients = [item.strip() for item in args.clients.split(",") if item.strip()]
    targets = _client_targets(clients)
    if args.plan:
        print(json.dumps(_installation_plan(names, targets), indent=2, sort_keys=True))
        return 0
    _install_selected(names, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(_installation_plan(names, targets), indent=2, sort_keys=True))
        return 0
    if clients and clients != ["none"]:
        _configure_clients(targets, _server_configs(names))
    if args.verify:
        return _verify_installed(names)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    arguments = json_arguments(args.arguments)
    result = call_tool(args.server, args.tool, arguments, transport=args.transport)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result.get("is_error") else 1


def cmd_discover(args: argparse.Namespace) -> int:
    tools = discover_tools(args.server, transport=args.transport)
    print(json.dumps(tools, indent=2, sort_keys=True))
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    if args.action == "show":
        print(json.dumps(show_config(), indent=2, sort_keys=True))
        return 0
    set_value(args.key, args.value)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="biomcp")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list")
    list_parser.set_defaults(func=cmd_list)

    tools_parser = sub.add_parser("tools")
    tools_parser.add_argument("server")
    tools_parser.set_defaults(func=cmd_tools)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("server")
    validate_parser.set_defaults(func=cmd_validate)

    assess_parser = sub.add_parser("assess")
    assess_parser.add_argument("server", nargs="?")
    assess_parser.add_argument("--all", action="store_true")
    assess_parser.set_defaults(func=cmd_assess)

    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("server", nargs="?")
    doctor_parser.set_defaults(func=cmd_doctor)

    lifecycle_parser = sub.add_parser("lifecycle")
    lifecycle_parser.add_argument("server", nargs="?")
    lifecycle_parser.set_defaults(func=cmd_lifecycle)

    install_parser = sub.add_parser("install")
    install_parser.add_argument("--servers", default="bioimage")
    install_parser.add_argument("--clients", default="none")
    install_parser.add_argument("--dry-run", action="store_true")
    install_parser.add_argument("--plan", action="store_true")
    install_parser.add_argument("--verify", action="store_true")
    install_parser.set_defaults(func=cmd_install, plan=False)

    run_parser = sub.add_parser("run")
    run_parser.add_argument("server")
    run_parser.add_argument("tool")
    run_parser.add_argument("--arguments", default="{}")
    run_parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    run_parser.set_defaults(func=cmd_run)

    discover_parser = sub.add_parser("discover")
    discover_parser.add_argument("server")
    discover_parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    discover_parser.set_defaults(func=cmd_discover)

    config_parser = sub.add_parser("config")
    config_parser.add_argument("action", choices=["show", "set"])
    config_parser.add_argument("key", nargs="?")
    config_parser.add_argument("value", nargs="?")
    config_parser.set_defaults(func=cmd_config)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
