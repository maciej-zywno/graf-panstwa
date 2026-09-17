#!/usr/bin/env bash
# Wdrożenie grafpanstwa.pl. Kroki nginx, dns i cert zmieniają serwer i DNS: uruchamiać świadomie.
#   scripts/deploy-site.sh files   # tylko pliki strony (bezpieczne po pierwszym wdrożeniu)
#   scripts/deploy-site.sh nginx   # vhost nginx (pierwszy raz)
#   scripts/deploy-site.sh dns     # rekordy A u rejestratora (wywołanie idzie przez serwer, bo klucz API ma białą listę adresów)
#   scripts/deploy-site.sh cert    # certyfikat Let's Encrypt (po propagacji DNS)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; DOMAIN=grafpanstwa.pl; WWW=/var/www/$DOMAIN; AM=https://json.aftermarket.pl
[ -f "$ROOT/deploy/local.env" ] || { echo "brak deploy/local.env (wzór: deploy/local.env.example)"; exit 1; }
. "$ROOT/deploy/local.env"; HOST="$DEPLOY_HOST"; IP="$DEPLOY_IP"; ENVF="$REGISTRAR_ENV"
am() { local P S; P=$(grep -E '^AFTERMARKET_API_PUBLIC=' "$ENVF" | cut -d= -f2- | tr -d "\"' \r"); S=$(grep -E '^AFTERMARKET_API_SECRET=' "$ENVF" | cut -d= -f2- | tr -d "\"' \r")
  printf 'user = "%s:%s"\n' "$P" "$S" | ssh -o BatchMode=yes "$HOST" "curl -sS -m 25 -A 'Mozilla/5.0' -K - $*"; }
case "${1:-}" in
  files) python3 "$ROOT/scripts/build-site.py" ${INDEX:+--index}
         ssh "$HOST" "sudo mkdir -p $WWW && sudo chown \$(id -un): $WWW"
         rsync -az --delete "$ROOT/dist/site/" "$HOST:$WWW/"; ssh "$HOST" "cat $WWW/BUILD.txt" ;;
  nginx) scp "$ROOT/deploy/nginx-$DOMAIN.conf" "$HOST:/tmp/$DOMAIN.conf"
         ssh "$HOST" "sudo install -m 644 /tmp/$DOMAIN.conf /etc/nginx/sites-available/$DOMAIN && sudo ln -sfn /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN && if sudo nginx -t; then sudo systemctl reload nginx && echo 'nginx: przeładowany'; else sudo rm -f /etc/nginx/sites-enabled/$DOMAIN; echo 'nginx -t nie przeszedł: vhost wyłączony, reszta serwera nietknięta'; exit 1; fi" ;;
  dns)   echo "przed:"; am "$AM/domain/dns/list --data-urlencode name=$DOMAIN"; echo
         am "$AM/domain/dns/add --data-urlencode name=$DOMAIN --data-urlencode type=A --data-urlencode host=@ --data-urlencode value=$IP"; echo
         am "$AM/domain/dns/add --data-urlencode name=$DOMAIN --data-urlencode type=A --data-urlencode host=www --data-urlencode value=$IP"; echo
         echo "po:"; am "$AM/domain/dns/list --data-urlencode name=$DOMAIN"; echo ;;
  cert)  ssh "$HOST" "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --redirect --non-interactive --agree-tos -m $DEPLOY_EMAIL" ;;
  *) sed -n 2,7p "$0"; exit 1 ;;
esac
