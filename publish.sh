#!/usr/bin/env bash
# publish.sh — Build + publish lên PyPI + tạo GitHub Release
# Dùng: bash publish.sh [patch|minor|major]
set -euo pipefail

BUMP="${1:-patch}"  # patch | minor | major

BOLD="\033[1m"; GREEN="\033[32m"; YELLOW="\033[33m"; RESET="\033[0m"
info() { echo -e "${BOLD}${GREEN}✅ $*${RESET}"; }
step() { echo -e "\n${BOLD}$*${RESET}"; }

# ── Lấy version hiện tại ──────────────────────────────────────────────────────
CURRENT=$(python3 -c "
import re
content = open('pyproject.toml').read()
m = re.search(r'version\s*=\s*\"([^\"]+)\"', content)
print(m.group(1))
")

IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
    major) NEW_VER="$((MAJOR+1)).0.0" ;;
    minor) NEW_VER="${MAJOR}.$((MINOR+1)).0" ;;
    *)     NEW_VER="${MAJOR}.${MINOR}.$((PATCH+1))" ;;
esac

step "Bump version: $CURRENT → $NEW_VER"
sed -i '' "s/^version = \"$CURRENT\"/version = \"$NEW_VER\"/" pyproject.toml
info "pyproject.toml updated"

# ── Đóng gói plugin ───────────────────────────────────────────────────────────
step "Đóng gói Cowork plugin..."
bash package-plugin.sh
info "seo-audit.plugin đã tạo"

# ── Build Python package ──────────────────────────────────────────────────────
step "Build Python package..."
rm -rf dist/ build/ mcp_server.egg-info/
python3 -m build
info "Package đã build: $(ls dist/)"

# ── Kiểm tra package ──────────────────────────────────────────────────────────
step "Kiểm tra package với twine..."
python3 -m twine check dist/*
info "Package hợp lệ"

# ── Upload lên PyPI ───────────────────────────────────────────────────────────
step "Upload lên PyPI..."
python3 -m twine upload dist/*
info "Published: seo-audit-mcp v$NEW_VER"

# ── Git tag + GitHub Release ──────────────────────────────────────────────────
step "Tạo git tag v$NEW_VER..."
git add pyproject.toml
git commit -m "chore: bump version to v$NEW_VER"
git tag "v$NEW_VER"
git push origin main --tags
info "Tag v$NEW_VER đã push"

if command -v gh &>/dev/null; then
    step "Tạo GitHub Release..."
    gh release create "v$NEW_VER" seo-audit.plugin \
        --title "v$NEW_VER" \
        --generate-notes
    info "GitHub Release v$NEW_VER đã tạo với seo-audit.plugin"
else
    echo -e "${YELLOW}⚠️  gh CLI chưa cài — tạo release thủ công:${RESET}"
    echo "   gh release create v$NEW_VER seo-audit.plugin --title 'v$NEW_VER' --generate-notes"
    echo "   (cài gh: brew install gh)"
fi

echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Published seo-audit-mcp v$NEW_VER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
