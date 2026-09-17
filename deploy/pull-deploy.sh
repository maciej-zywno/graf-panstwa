#!/usr/bin/env bash
# Wdrożenie „na żądanie serwera”: uruchamiane z crona na serwerze WWW. Sprawdza, czy w publicznym repozytorium jest nowy commit
# na gałęzi main, buduje z niego stronę statyczną i podmienia pliki. Nie wymaga żadnych haseł ani kluczy: GitHub nie ma dostępu do serwera.
# Instalacja (raz):  install -m 755 pull-deploy.sh ~/bin/grafpanstwa-pull-deploy.sh ; wpis w crontab:  17 * * * * ~/bin/grafpanstwa-pull-deploy.sh
# Indeksowanie w wyszukiwarkach włącza plik ~/.cache/grafpanstwa/index.on (touch), wyłącza jego usunięcie.
set -euo pipefail
REPO="${GP_REPO:-maciej-zywno/graf-panstwa}"; WWW="${GP_WWW:-/var/www/grafpanstwa.pl}"; STATE="$HOME/.cache/grafpanstwa"; LOG="$STATE/deploy.log"
mkdir -p "$STATE"; exec 9>"$STATE/lock"; flock -n 9 || exit 0
SHA=$(curl -fsS -m 30 -H 'Accept: application/vnd.github.sha' -A 'grafpanstwa-pull-deploy' "https://api.github.com/repos/$REPO/commits/main")
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "$(date -Is) zła odpowiedź GitHuba" >> "$LOG"; exit 1; }
[ "$SHA" = "$(cat "$STATE/deployed.sha" 2>/dev/null || true)" ] && exit 0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL -m 180 -A 'grafpanstwa-pull-deploy' "https://codeload.github.com/$REPO/tar.gz/$SHA" | tar -xz -C "$TMP" --strip-components=1
cd "$TMP"; if [ -f "$STATE/index.on" ]; then python3 scripts/build-site.py --index >/dev/null; else python3 scripts/build-site.py >/dev/null; fi
# kontrola przed podmianą: dane się czytają i nie skurczyły się podejrzanie, a strona zawiera widok
python3 - <<'PY'
import json, sys
g = json.load(open('dist/site/graph.json', encoding='utf-8')); h = open('dist/site/index.html', encoding='utf-8').read()
ok = len(g['nodes']) >= 500 and len(g['edges']) >= 900 and '__GP_TEST' in h and len(h) > 100000
sys.exit(0 if ok else 1)
PY
rsync -a --delete dist/site/ "$WWW/"
echo "$SHA" > "$STATE/deployed.sha"; echo "$(date -Is) wdrożono $SHA ($(tr '\n' ' ' < dist/site/BUILD.txt))" >> "$LOG"
