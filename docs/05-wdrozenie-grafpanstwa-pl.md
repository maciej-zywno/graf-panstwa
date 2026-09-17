# Wdrożenie strony grafpanstwa.pl

Strona publiczna to dwa pliki statyczne: `index.html` (widok) i `graph.json` (dane). Nie ma serwera aplikacji ani bazy danych.

## Budowa
```bash
python3 scripts/build-site.py            # dist/site/, bez indeksowania w wyszukiwarkach (domyślnie)
python3 scripts/build-site.py --index    # z indeksowaniem
```
Dane mają wersję w adresie (`graph.json?v=<skrót treści>`), więc plik może mieć długi cache bez ryzyka podania starych danych.

## Serwer
Dowolny serwer plików statycznych z HTTPS. Przykładowa konfiguracja nginx: `deploy/nginx-grafpanstwa.pl.conf` (przekierowania HTTP i `www` na adres kanoniczny, nagłówki bezpieczeństwa, gzip dla JSON, długi cache danych).

Skrypt `scripts/deploy-site.sh` wgrywa pliki przez `rsync` i obsługuje pierwszy raz (vhost, rekordy DNS, certyfikat Let's Encrypt). Adres serwera i ścieżkę do kluczy API czyta z pliku `deploy/local.env`, którego nie ma w repozytorium. Wzór: `deploy/local.env.example`.

## Indeksowanie
Do czasu uzgodnień z zespołem CivLab, na którego projekcie wzorowany jest widok, strona ma wyłączone indeksowanie (meta `robots`, `robots.txt`, nagłówek `X-Robots-Tag`).

## Lekcja z pierwszego wdrożenia: DNS
Rejestrator domeny podaje rekordy z czasem życia 6 godzin, także dla adresu parkingowego zwracanego przez pustą strefę. Kto zapyta o nową domenę przed dodaniem rekordów, zamraża parking w pamięci swojego resolvera na 6 godzin, a parking podaje niezaufany certyfikat. Kolejność ma znaczenie: najpierw rekordy, potem pierwsze zapytanie i pierwsze otwarcie w przeglądarce. Przy zmianie hostingu stary serwer powinien działać jeszcze 6 godzin.
