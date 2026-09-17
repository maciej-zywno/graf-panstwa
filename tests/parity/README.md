# Testy zgodności z oryginałem (CivLab US Gov Graph ↔ Graf Państwa Polskiego)

Cel: wyłapać błędy i braki po polskiej stronie przez porównanie ZACHOWAŃ z oryginałem https://graph.civlab.org/us.
Porównujemy zachowania, nie piksele, bo dane po obu stronach są inne.

## Dwie warstwy
1. **Warstwa skryptowa** (`tests/e2e/`, Playwright): wszystko, co nie wymaga oceny. Uruchamiana przy każdym buildzie:
   `npm test` (serwer lokalny startuje sam). Raport: `tests/e2e/report/`.
2. **Przebieg porównawczy** (agenci + przeglądarka): katalog zachowań oryginału → pary scenariuszy → werdykt → weryfikacja
   adwersarialna. Raport: `tests/parity/report-RRRR-MM-DD.md`.

## Co jest testowane
- Samodzielny plik skórki domyślnej: `viewer/variants/D-styl-civlab/index.html` z danymi `data/pl/graph.json` (localhost).
- Przełącznik skórek: `dist/graf-panstwa.local.html` (tylko warstwa skryptowa; Playwright widzi ramki `srcdoc`).
- Opublikowany artefakt NIE jest testowany automatycznie (domena zablokowana dla rozszerzenia, wymaga logowania).

## Przebieg porównawczy krok po kroku
1. **Katalog zachowań oryginału** → `behaviors-civlab.md`. Agent przechodzi stronę US i dla każdej interakcji zapisuje:
   wyzwalacz, obserwowalny skutek, zrzut. Zakres: najazd na węzeł / kropkę / kółko szefa / linię; klik węzła, pustej sceny,
   linii; legenda (otwarcie, klik poza, Esc); wyszukiwarka; zoom i przeciąganie; link do węzła; wstecz; motyw; breadcrumb;
   zakładki panelu; wąski ekran.
2. **Pary scenariuszy** → `scenarios.json`: to samo zachowanie na odpowiadających sobie węzłach US i PL.
3. **Wykonanie**: te same kroki po obu stronach. Po stronie PL agent czyta stan przez uchwyty (niżej), po stronie US obserwuje.
4. **Werdykt** per zachowanie: `zgodne` / `różnica zamierzona` (lista w `intended-differences.md`) / `błąd` / `brak funkcji`.
   Waga: `krytyczny` (blokuje użycie), `wysoki` (myli użytkownika), `średni` (razi przy porównaniu), `niski` (kosmetyka).
5. **Weryfikacja adwersarialna**: drugi agent odtwarza każdy `błąd`; niepowtarzalne trafiają do „niepotwierdzone".

## Uchwyty testowe po stronie PL (`window.__GP_TEST`, tylko odczyt)
- `state()` → `{selected, relFilter, legendOpen, edgesDrawn, ownEdgesDrawn, blockedEdges, hoverPill, selPill, bottomPill,
  edgeTip, hotEdge, theme, k, panelTitle, relRows}`
- od rundy 4 `state()` zwraca także `{fan, hidden, rot, rotTarget, rotating}`: id rodzica rozwiniętego wachlarza, klucze ukryte w legendzie (np. `entity:court`, `rel:appoints`), kąt obrotu grafu i czy animacja trwa
- `screenPos(id)` → `{x, y, kind, ring}` we współrzędnych okna (do najazdu i kliknięcia); uwzględnia obrót grafu i wachlarz (`kind: 'mini'`)
- `glyphs()` → `[{id, kind, x, y, r, headOf, parent}]` (kontrola nakładania)
- `edges()` → narysowane relacje `[{id, type, from, to, chain}]`; `edgePoints(eid, n)` → punkty linii w oknie
- `node(id)`, `ids()`, `stageRect()`
Kontrakt skórki (każda): dane z `window.GRAPH_DATA` | `./graph.json` | `?data=`, wybór przez `#node=<id>`, motyw w `gp-theme`.

## Ograniczenia środowiska
- Najazd myszą działa tylko w widocznej karcie: agenci z rozszerzeniem Chrome pracują po kolei, okno Chrome zostaje w spokoju.
- Strony za `about:srcdoc` są niedostępne dla rozszerzenia; przełącznik testuje wyłącznie Playwright.
- CivLab zmienia stronę bez ostrzeżenia: katalog zachowań ma datę i trzeba go odświeżać.
