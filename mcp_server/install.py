"""seo-audit-mcp-install — configures Claude Desktop, Claude Code, and shell function."""
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

PLUGIN_DATA = Path(__file__).parent / "plugin_data"
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

    _step(1, 3, "Cấu hình Claude Desktop MCP server...")
    _configure_desktop(binary)

    _step(2, 3, "Cấu hình Claude Code CLI...")
    _configure_claude_code(binary)

    _step(3, 3, "Cài đặt plugin files + shell function...")
    plugin_dir = _install_plugin_dir()
    _add_shell_function(plugin_dir)

    _restart_claude()

    print(f"\n{_BOLD}{_GREEN}{_DIV}{_RESET}")
    print(f"{_BOLD}{_GREEN}  Cài đặt hoàn tất!{_RESET}")
    print(f"{_BOLD}{_GREEN}{_DIV}{_RESET}")
    print(f"\n  MCP tools → hoạt động ngay trong Claude Desktop + Claude Code")
    print(f"  Claude Code terminal → gõ: /onpage  (sau khi mở terminal mới)")
    print(f"\n{_BOLD}  Để dùng /onpage trong Cowork (1 lần duy nhất):{_RESET}")
    print(f"  Cowork → Settings → Plugins → Upload → chọn file seo-audit.plugin")
    print(f"  (Tải file tại: https://github.com/minhdo01011990-glitch/seo-audit-plugin/releases/latest)")
    print(f"\n{_BOLD}{_GREEN}{_DIV}{_RESET}\n")
