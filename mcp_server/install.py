"""seo-audit-mcp-install — configures Claude Desktop, Claude Code, and Cowork plugin."""
import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_DATA = Path(__file__).parent / "plugin_data"
PLUGIN_ID = "plugin_seo_audit_mcp"
REPORT_DIR = Path.home() / "Documents" / "SEO Audit Reports"

_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_DIV = "━" * 53


def _ok(msg: str) -> None:
    print(f"  {_BOLD}{_GREEN}✅ {msg}{_RESET}")


def _warn(msg: str) -> None:
    print(f"  {_YELLOW}⚠️  {msg}{_RESET}")


def _step(n: int, total: int, msg: str) -> None:
    print(f"\n{_BOLD}{n}/{total} {msg}{_RESET}")


def _get_desktop_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude/claude_desktop_config.json"
    return Path.home() / ".config/Claude/claude_desktop_config.json"


def _get_binary() -> str:
    return shutil.which("seo-audit-mcp") or "seo-audit-mcp"


def _configure_desktop(binary: str) -> None:
    config_path = _get_desktop_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except Exception:
            pass

    config.setdefault("mcpServers", {})["seo-audit"] = {
        "command": binary,
        "env": {
            "PAGESPEED_API_KEY": "",
            "REPORT_OUTPUT_DIR": str(REPORT_DIR),
        },
    }
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    _ok(f"claude_desktop_config.json")


def _configure_claude_code(binary: str) -> None:
    settings_path = Path.home() / ".claude/settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    settings: dict = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except Exception:
            pass

    settings.setdefault("mcpServers", {})["seo-audit"] = {"command": binary}
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    _ok("~/.claude/settings.json")


def _install_plugin_dir() -> Path:
    """Extract plugin files to ~/.local/share/seo-audit-mcp/plugin/ with correct names."""
    dest = Path.home() / ".local/share/seo-audit-mcp/plugin"
    dest.mkdir(parents=True, exist_ok=True)

    shutil.copytree(PLUGIN_DATA / "claude_plugin", dest / ".claude-plugin", dirs_exist_ok=True)
    shutil.copy(PLUGIN_DATA / "mcp.json", dest / ".mcp.json")
    shutil.copytree(PLUGIN_DATA / "skills", dest / "skills", dirs_exist_ok=True)

    _ok(f"Plugin files → {dest}")
    return dest


def _add_shell_function(plugin_dir: Path) -> None:
    """Wrap `claude` CLI to always load the plugin via --plugin-dir."""
    shell = Path(os.environ.get("SHELL", "")).name
    rc_file = Path.home() / (".zshrc" if shell == "zsh" else ".bashrc")
    marker = "seo-audit-mcp: /onpage skill"

    func = (
        f"\n# {marker}\n"
        f'function claude() {{ command claude --plugin-dir "{plugin_dir}" "$@"; }}\n'
    )

    text = rc_file.read_text() if rc_file.exists() else ""
    if marker not in text:
        with rc_file.open("a") as f:
            f.write(func)
        _ok(f"Shell function → {rc_file.name} (claude --plugin-dir auto-loaded)")
    else:
        _ok(f"Shell function đã có trong {rc_file.name}")


def _inject_cowork_plugin(plugin_dir: Path) -> bool:
    """Copy plugin into Claude Desktop Cowork rpm directory and update manifest."""
    claude_data = Path.home() / "Library/Application Support/Claude/local-agent-mode-sessions"
    if not claude_data.exists():
        return False

    manifests = list(claude_data.glob("*/*/rpm/manifest.json"))
    if not manifests:
        return False

    for manifest_path in manifests:
        rpm_dir = manifest_path.parent
        target = rpm_dir / PLUGIN_ID

        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plugin_dir / ".claude-plugin", target / ".claude-plugin", dirs_exist_ok=True)
        shutil.copy(plugin_dir / ".mcp.json", target / ".mcp.json")
        shutil.copytree(plugin_dir / "skills", target / "skills", dirs_exist_ok=True)

        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}

        manifest.setdefault("plugins", [])
        manifest["plugins"] = [p for p in manifest["plugins"] if p.get("id") != PLUGIN_ID]
        manifest["plugins"].append({
            "id": PLUGIN_ID,
            "name": "seo-audit",
            "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000Z"),
            "marketplaceId": "local_install",
            "marketplaceName": "Local Install",
            "installedBy": "user",
            "installationPreference": "available",
        })
        manifest["lastUpdated"] = int(datetime.now().timestamp() * 1000)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

        _ok(f"Cowork rpm → {rpm_dir.name}/...")

    return True


def _restart_claude() -> None:
    if platform.system() != "Darwin":
        _warn("Restart Claude Desktop thủ công để áp dụng thay đổi")
        return
    subprocess.run(["osascript", "-e", "tell application \"Claude\" to quit"],
                   capture_output=True)
    time.sleep(3)
    subprocess.run(["open", "-a", "Claude"], capture_output=True)
    _ok("Claude Desktop đã restart")


def main() -> None:
    print(f"\n{_BOLD}{_DIV}{_RESET}")
    print(f"{_BOLD}  SEO Audit MCP Plugin — Install{_RESET}")
    print(f"{_BOLD}{_DIV}{_RESET}")

    binary = _get_binary()
    print(f"\n  Binary: {binary}")

    _step(1, 4, "Cấu hình Claude Desktop MCP server...")
    _configure_desktop(binary)

    _step(2, 4, "Cấu hình Claude Code CLI...")
    _configure_claude_code(binary)

    _step(3, 4, "Cài đặt plugin files + shell function...")
    plugin_dir = _install_plugin_dir()
    _add_shell_function(plugin_dir)

    _step(4, 4, "Cài đặt Cowork plugin + restart...")
    cowork_ok = _inject_cowork_plugin(plugin_dir)
    if not cowork_ok:
        _warn("Không tìm thấy Cowork rpm directory")
        _warn("Mở Claude Desktop một lần rồi chạy lại: seo-audit-mcp-install")
    _restart_claude()

    print(f"\n{_BOLD}{_GREEN}{_DIV}{_RESET}")
    print(f"{_BOLD}{_GREEN}  Cài đặt hoàn tất!{_RESET}")
    print(f"{_BOLD}{_GREEN}{_DIV}{_RESET}")
    print(f"\n  Claude Desktop → Cowork → gõ: /onpage")
    print(f"  Claude Code terminal → gõ:    /onpage")
    print(f"\n{_BOLD}{_GREEN}{_DIV}{_RESET}\n")
