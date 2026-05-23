#!/usr/bin/env bash
# druckpunkt — Parts-Guide Upstream-Sync
# Verwendung: bash sync-upstream.sh  (aus dem od3m/parts-guide Repo-Root)
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

UPSTREAM_URL="https://github.com/Kartzy-Studio/cfm-parts-guide.git"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GENERATOR="$SCRIPT_DIR/generate_parts_guide.py"

echo -e "${BOLD}druckpunkt — Parts-Guide Upstream-Sync${NC}"
echo "─────────────────────────────────────────"

# ── 1. upstream-Remote einrichten ────────────────────────────────────────
if ! git remote get-url upstream &>/dev/null; then
  git remote add upstream "$UPSTREAM_URL"
  echo -e "${GREEN}✓ upstream-Remote hinzugefügt${NC}"
else
  echo -e "  upstream bereits vorhanden"
fi

# ── 2. Upstream holen ────────────────────────────────────────────────────
echo -e "\n${CYAN}↓ Hole upstream …${NC}"
git fetch upstream --quiet

# ── 3. Neue Commits? ─────────────────────────────────────────────────────
NEW=$(git log HEAD..upstream/main --oneline 2>/dev/null || true)
if [ -z "$NEW" ]; then
  echo -e "${GREEN}✓ Kein Update nötig — Fork ist aktuell.${NC}"
  exit 0
fi

echo -e "${YELLOW}Neue Commits im Original:${NC}"
echo "$NEW" | sed 's/^/  /'
echo

# ── 4. Was hat sich geändert? ────────────────────────────────────────────
NEW_IMGS=$(git diff HEAD..upstream/main --name-only 2>/dev/null | grep '^images/' || true)
NEW_CODE=$(git diff HEAD..upstream/main --name-only 2>/dev/null | grep -E '\.(html|css|js|json)$' || true)

if [ -n "$NEW_IMGS" ]; then
  echo -e "${YELLOW}Geänderte Bilder:${NC}"
  echo "$NEW_IMGS" | sed 's/^/  /'
  echo
fi
if [ -n "$NEW_CODE" ]; then
  echo -e "${YELLOW}Geänderte Code-Dateien (werden NICHT automatisch übernommen):${NC}"
  echo "$NEW_CODE" | sed 's/^/  /'
  echo -e "  → Schau sie dir manuell an und übertrage nur was sinnvoll ist."
  echo
fi

# ── 5. Nur Bilder übernehmen (kein Merge, keine History-Konflikte) ────────
# Strategie: Wir ziehen gezielt den images/-Ordner vom Original rüber.
# Branding-Dateien (css, html, js, locales) bleiben unberührt.
echo -e "${CYAN}↓ Übernehme Bilder von upstream …${NC}"
git checkout upstream/main -- images/
echo -e "${GREEN}✓ images/ aktualisiert${NC}"

# ── 6. Committen & pushen ────────────────────────────────────────────────
git add images/
if git diff --cached --quiet; then
  echo -e "${GREEN}  Keine Änderungen in images/ — nichts zu committen.${NC}"
else
  git commit -m "sync: images from upstream $(date +%Y-%m-%d)"
  echo -e "\n${CYAN}↑ Push zu origin …${NC}"
  git push origin main
  echo -e "${GREEN}✓ Fork gepusht — GitHub Pages baut neu (~1 Min)${NC}"
fi

# ── 7. Neues Shopify-Liquid generieren ───────────────────────────────────
if [ -f "$GENERATOR" ]; then
  echo -e "\n${CYAN}⚙  Generiere Shopify-Liquid …${NC}"
  python3 "$GENERATOR"
  echo -e "${GREEN}✓ page.parts-guide.liquid aktualisiert${NC}"
else
  echo -e "${YELLOW}⚠  generate_parts_guide.py nicht gefunden${NC}"
fi

# ── 8. Abschluss-Checkliste ──────────────────────────────────────────────
echo
echo -e "${BOLD}Was jetzt noch zu tun ist:${NC}"
echo "  1. ~1 Min warten, dann Bilder prüfen:"
echo "     → https://od3m.github.io/parts-guide/images/hero.png"
echo "  2. Neues Liquid in Shopify einsetzen:"
echo "     → Theme-Editor → templates/page.part-guide.liquid → Inhalt ersetzen → Save"
if [ -n "$NEW_IMGS" ]; then
  echo "  3. Drift-Report oben prüfen — neue Teile brauchen ggf. ein deutsches Label"
  echo "     in generate_parts_guide.py unter LABELS ergänzen, dann nochmal:"
  echo "     python3 generate_parts_guide.py"
fi
echo
echo -e "${GREEN}Fertig.${NC}"
