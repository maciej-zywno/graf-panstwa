# Budżet państwa według części: źródła i metoda

Stan na 2026-09-18. Ten dokument opisuje plik `data/pl/budget.json` (dane do widoku „Budżet”) i skrypt
`scripts/build-budget.py`, który go odtwarza. Uzupełnia `04-zrodla-danych.md` (źródła grafu) i `02-mapa-zrodel-i-ryzyk.md`
(przegląd źródeł). Obowiązuje ta sama zasada co w całym projekcie: **wyłącznie źródła urzędowe**, każda liczba ma wskazane
źródło, nic nie jest zgadywane.

Jednostka wszędzie: **tys. zł**, z dokładnością źródła, bez przeliczeń.

## 1. W skrócie

| | |
|---|---|
| Rok bieżący (`currentYear`) | 2025, wykonanie budżetu |
| Rok planu (`planYear`) | 2026, ustawa budżetowa |
| Historia | wykonanie, plan i plan po zmianach za lata 2021–2024 z tego samego zbioru |
| Wpisy | 162: **85 części** i **77 podczęści** (15/01–15/12, 85/02–85/32, 86/01–86/97) |
| Z `nodeId` | 97 wpisów: 80 z 85 części, 17 z 77 podczęści |
| Grupy | 11: 6 funkcjonalnych i 5 technicznych |

| Rok | Plan wg ustawy | Plan po zmianach | Wykonanie (`actual`) | Wydatki niewygasające | Razem, kwota nagłówkowa MF (`actualWithCarriedOver`) |
|---|---:|---:|---:|---:|---:|
| 2021 | 523 492 865 | 523 492 865 | 513 595 573,60 | 7 621 243,18 | 521 216 816,78 |
| 2022 | 521 836 950 | 521 836 950 | 517 398 906,98 | 0 | 517 398 906,98 |
| 2023 | 693 378 366 | 693 378 366 | 659 586 490,98 | 0 | 659 586 490,98 |
| 2024 | 866 375 747 | 866 375 747 | 834 242 509,64 | 0 | 834 242 509,64 |
| **2025** | **921 618 215** | **921 618 215** | **870 143 503,93** | 47 108,28 | **870 190 612,21** |
| 2026 | 918 940 000 | | | | |

Uwaga do środka pierścienia: oficjalna łączna kwota wydatków w „Zestawieniu ogólnym” sprawozdania to wykonanie **razem**
z wydatkami niewygasającymi (2025: 870 190 612,21). Suma pól `actual` wszystkich części daje 870 143 503,93. Obie liczby są
w `meta.totals`; trzeba świadomie wybrać, którą pokazać, i ją podpisać.

## 2. Źródła i licencje

| Co | Wydawca i adres | Format | Warunki użycia |
|---|---|---|---|
| Wykonanie budżetu 2021–2025 | Ministerstwo Finansów, dane.gov.pl, zbiór 163 „Część tabelaryczna sprawozdań z wykonania budżetu państwa”, <https://dane.gov.pl/pl/dataset/163>, API: `https://api.dane.gov.pl/1.4/datasets/163/resources` | ZIP na rok, w nim ZIP Tomu I i Tomu II z plikami XLS/XLSX (dla 2025 r. także PDF obu tomów) | **CC0 1.0** (pole `license_name` w API zbioru, sprawdzone 2026-09-18) |
| Nazwy części, część dysponentów | Rozporządzenie Ministra Finansów z 4.12.2009 r. w sprawie klasyfikacji części budżetowych oraz określenia ich dysponentów, t.j. [Dz.U. 2025 poz. 1185](https://eli.gov.pl/eli/DU/2025/1185/ogl) | PDF z API ELI Sejmu | materiał urzędowy, poza prawem autorskim (art. 4 pkt 1 i 2 ustawy o prawie autorskim) |
| Który minister dysponuje którą częścią | 18 rozporządzeń Prezesa RM w sprawie szczegółowego zakresu działania ministrów (lista w pkt 5) | PDF z API ELI Sejmu | jak wyżej |
| Plan 2026 | Ustawa budżetowa na rok 2026 z 9.01.2026 r., [Dz.U. 2026 poz. 62](https://eli.gov.pl/eli/DU/2026/62/ogl), załącznik nr 2 | PDF (867 stron) z API ELI Sejmu | jak wyżej |
| Definicja dysponenta, rezerwy | Ustawa o finansach publicznych, t.j. [Dz.U. 2025 poz. 1483](https://eli.gov.pl/eli/DU/2025/1483/ogl): art. 2 pkt 8, art. 114, art. 154, art. 155 | PDF | jak wyżej; tylko cytowana, skrypt jej nie pobiera |
| Zmiana nazwy części 84 od 2027 r. | [Dz.U. 2026 poz. 1026](https://eli.gov.pl/eli/DU/2026/1026/ogl) | PDF | jak wyżej; tylko cytowana |

Adresy sprawdzone na żywo 2026-09-18. `eli.gov.pl/robots.txt` niczego nie zabrania; `api.dane.gov.pl` i `api.sejm.gov.pl`
nie mają pliku robots.txt (404), a są to publiczne API przeznaczone do odczytu maszynowego. Pobieranie: jedno żądanie na
plik, z nagłówkiem User-Agent, z pamięcią podręczną. Strony `www.gov.pl/web/finanse/ustawa-2026` skrypt nie odpytuje:
ten sam akt jest w ELI.

### Pliki i sumy kontrolne

Pliki źródłowe leżą w `data/pl/budget-src/` (katalog jest w `.gitignore`, razem ok. 134 MB). W repozytorium zostają adresy
i sumy SHA-256: w skrypcie (tabele `YEARS` i `ACTS`) oraz w `budget.json` (`meta.sources[]`, a dla aktów o ministrach
`meta.verification.ministerActs[]`). Skrypt porównuje sumę każdego pobranego pliku z zapisaną i przerywa pracę, gdy się różnią.

| Plik | Adres | SHA-256 |
|---|---|---|
| `wyk2025.zip` | `https://api.dane.gov.pl/resources/2054935,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2025-r/file` | `ea4e38df86da7b41b12f2fd00dc80c94b260ee0e0687222e97995862a183e7d7` |
| `wyk2024.zip` | `https://api.dane.gov.pl/resources/72399,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2024-r/file` | `22bbb6c47434c48da5b28d539262b425b5fe1eaacf57e4b4604bd5830ac1e3cb` |
| `wyk2023.zip` | `https://api.dane.gov.pl/resources/58249,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2023-r/file` | `08b05037c6163d9ed3572b69190b08e13420f98ba90c3d28d40611055782ca74` |
| `wyk2022.zip` | `https://api.dane.gov.pl/resources/48622,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2022-r/file` | `df384cb1d09e2c06e652a85044d6c9f04dcbb48f7626a7a60e4b823f1ab1ddf5` |
| `wyk2021.zip` | `https://api.dane.gov.pl/resources/38967,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2021-r/file` | `db463035dbe382a405d84625af7528db4cbdc8096fd4389dea8f80634f285f14` |
| `D20251185.pdf` | `https://api.sejm.gov.pl/eli/acts/DU/2025/1185/text/O/D20251185.pdf` | `bd8949d3b053ec96abb8c00ec811ecdc7dfca88d8128923beaac73b5593f1dd7` |
| `D20260062.pdf` | `https://api.sejm.gov.pl/eli/acts/DU/2026/62/text/O/D20260062.pdf` | `a2486ce997442850401d19c763c767afbfda3a7b187985d343c3d3f10dc960da` |
| `D20251483.pdf` (tylko cytowany) | `https://api.sejm.gov.pl/eli/acts/DU/2025/1483/text/O/D20251483.pdf` | `e8222871a2b10844ba3b38625c0bffaaec5bccf348b3a1ed4868230762900a0f` |
| `D20261026.pdf` (tylko cytowany) | `https://api.sejm.gov.pl/eli/acts/DU/2026/1026/text/O/D20261026.pdf` | `544c7250030a39e249f7bad10871750aaa244d7ec3a477ef894176e432304c1e` |

### Które arkusze

Wbrew temu, co sugeruje nazwa, arkusz „012-WYDATKI BP WG CZĘŚCI” **nie zawiera wszystkich części ani wiersza „ogółem”**.
Pełny obraz składa się z siedmiu plików (układ identyczny w latach 2021–2025, zmieniają się tylko nazwy i rozszerzenia):

| Identyfikator w `meta.sources` | Tom | Plik (2025) | Arkusz | Co zawiera |
|---|---|---|---|---|
| `wyk2025-005` | I | `005 - ZESTAWIENIE OGÓLNE Z WYKONANIA BUDŻETU PAŃSTWA.xlsx` | ZESTAWIENIE OGÓLNE BP | wiersz „2. WYDATKI BUDŻETU PAŃSTWA”: oficjalna kwota łączna (kontrola krzyżowa) |
| `wyk2025-011` | I | `011 - WYDATKI BP WG DZIAŁÓW_2025.xls` | Wydatki wg działów | wiersz **OGÓŁEM** i sumy według działów (punkt odniesienia walidacji) |
| `wyk2025-012` | I | `012-WYDATKI BP WG CZĘŚCI_2025.xls` | WYDATKI WG.CZĘŚCI(STR2.5-2.90) | części 01–84 z podczęściami 15/01–15/12 (bez 81, 83) |
| `wyk2025-013` | I | `013- WYDATKI BP CZ 81 I CZ 83.xlsx` | Arkusz1 | rezerwy: części 81 i 83 (inny układ wierszy, patrz pkt 3) |
| `wyk2025-014` | I | `014 - BUDZETY WOJEWODÓW ZBIORCZO WYDATKI_2025.xlsx` | CZ. 85 | część 85 zbiorczo |
| `wyk2025-015` | I | `015- WYDATKI CZ 86-91_2025.xlsx` | WYDATKI WG.CZĘŚCI(STR2.5-2.90) | część 86 z podczęściami 86/01–86/97, części 88–91 |
| `wyk2025-t2-07` | II | `07 - BUDŻETY WOJEWODÓW - WYDATKI WG WOJEWODZTW_2025.xlsx` | WYDATKI WG.CZĘŚCI(STR2.5-2.90) | podczęści 85/02–85/32 |

Plik za 2025 r. jest w starym formacie `.xls` (czyta go `xlrd`), pozostałe w `.xlsx` (`openpyxl`). Nazwy plików w starszych
ZIP-ach są zakodowane w CP852 bez flagi UTF-8; skrypt je przekodowuje.

## 3. Co znaczą kolumny

Każda pozycja w arkuszu (część, dział, rozdział) to blok wierszy oznaczonych literą. W `budget.json`:

| Pole | Wiersz w sprawozdaniu | Znaczenie |
|---|---|---|
| `plan` | a, „Budżet wg ustawy budżetowej” | limit wydatków z ustawy budżetowej (po ewentualnej nowelizacji ustawy, jak w 2023 r.). Dla roku 2026: kwota z załącznika nr 2 do ustawy. |
| `planAfterChanges` | b, „Budżet po zmianach” | plan na koniec roku, po przeniesieniach między częściami, działami i rozdziałami oraz po rozdysponowaniu rezerw. Suma po wszystkich częściach jest równa sumie planu: przeniesienia nie zmieniają łącznego limitu. |
| `actual` | c, „Wykonanie” | wydatki faktycznie zrealizowane w roku budżetowym |
| `carriedOver` | d, „Wydatki niewygasające” | wydatki, które nie wygasły z końcem roku (realizacja w roku następnym). Pole występuje tylko, gdy kwota jest większa od zera. **Nie jest wliczone w `actual`.** Oficjalna kwota łączna w „Zestawieniu ogólnym” sprawozdania (plik 005) to c + d: sprawdzone co do grosza dla wszystkich pięciu lat (2021: 513 595 573,60 + 7 621 243,18 = 521 216 816,78). |

Dokładność: `plan` to pełne tys. zł; pozostałe kwoty mają w arkuszach do pięciu miejsc po przecinku (grosze). Skrypt
zaokrągla do pięciu miejsc wyłącznie po to, żeby usunąć szum zapisu zmiennoprzecinkowego (np. `292467.27314999996`).

**Rezerwy (części 81 i 83)** mają inny układ: a (ustawa), f (rezerwa po zmianach), g (wykorzystanie w drodze przeniesień),
b (budżet po zmianach, czyli *pozostałość* rezerwy). Wiersza „wykonanie” nie ma: rezerw się nie wydaje, tylko przenosi
do innych części i tam widać je w wykonaniu. Dlatego w `budget.json` rezerwy mają `actual: 0`, `planAfterChanges` równe
pozostałości, a dodatkowo `reserveAfterChanges` (f) i `reserveTransferred` (g). Tylko przy takim odczycie suma „planu po
zmianach” wszystkich części zgadza się z wierszem OGÓŁEM, co potwierdza walidacja.

## 4. Kształt `budget.json`

Zgodny z ustalonym szkicem, z kilkoma polami dodatkowymi (żadne nie zmienia znaczenia pól uzgodnionych):

- `meta`: `unit`, `currentYear`, `currentKind`, `planYear`, `planNote` (powód, gdyby planu nie przyjęto), `generatedAt`,
  `historyYears`, `columns`, `precision`, `totals` (na rok: `plan`, `planAfterChanges`, `actual`, ewentualnie `carriedOver`),
  `sources[]`, `verification` (pełny zapis wyników walidacji z ostatniego przebiegu).
- `meta.sources[]`: jeden wpis na **plik w ZIP-ie** (nie na ZIP), bo dane pochodzą z siedmiu plików na rok (razem 37 wpisów). Identyfikatory
  `wyk<rok>-<plik>`, np. `wyk2025-012`; pola `url`, `zip`, `sha256` (ZIP), `innerZip`, `file`, `sheet`, `fileSha256`
  (sam arkusz), `license`, `retrievedAt`. Do tego `klasyfikacja` i `ub2026`.
- `groups[]`: `code`, `name`, `kind` (`functional` albo `technical`), `parts` (tylko części najwyższego poziomu, więc suma
  grup = OGÓŁEM bez podwójnego liczenia), `totals`.
- `parts{}`: klucz to kod („29”, „85/02”). Pola: `code`, `name` (urzędowa, z rozporządzenia), `nameInSource` (wersalikami,
  z arkusza), `level` (`part` / `subpart`), `parent`, `children` (tylko części macierzyste: 15, 85, 86), `dysponent`,
  `dysponentNodeId`, `dysponentVerified`, `dysponentBasis`, `nodeId`, `group`, `groupBasis`, `years`, `breakdown`,
  `sourceRef`, `note`.
- `years`: dla 2021–2025 `plan`, `planAfterChanges`, `actual` (+ `carriedOver`, pola rezerw, `nameInSource`, gdy część
  nosiła wtedy inną nazwę); dla 2026 tylko `plan`.
- `breakdown`: działy klasyfikacji budżetowej w tej części w 2025 r. (`dzial`, `name`, `plan`, `planAfterChanges`, `actual`),
  w kolejności źródła. Suma każdej z trzech kolumn = kwota części (walidowane).
- `sourceRef`: identyfikator źródła i zakres wierszy arkusza (numeracja Excela) dla danych 2025.

**Podczęści** są osobnymi wpisami, a część macierzysta ma kwotę **ze źródła** (własny wiersz w arkuszu), nie wyliczoną.
Skrypt sprawdza, że suma podczęści jest jej równa. Rysując pierścień, należy brać albo część macierzystą, albo jej
podczęści, nigdy obie.

## 5. `nodeId` i dysponent: reguły

Rozporządzenie o klasyfikacji części wskazuje dysponentów wprost tylko dla kilku części (§ 2 ust. 2: 15/00, 77, 79, 80,
82, 84, 87, 97, 98). Dla reszty odsyła do art. 2 pkt 8 ustawy o finansach publicznych: dysponentami są „kierownicy jednostek
oraz organy wymienione w art. 139 ust. 2, właściwi ministrowie, kierownicy urzędów centralnych, wojewodowie oraz kierownicy
państwowych jednostek organizacyjnych (…) dysponujący częściami budżetu państwa”. Dlatego przypisania mają cztery podstawy,
w tej kolejności:

1. **Akt wskazuje ministra.** Każde rozporządzenie Prezesa RM o szczegółowym zakresie działania ministra zawiera zdanie
   „Minister jest dysponentem części … budżetu państwa”. Skrypt pobiera 18 aktów i **sprawdza, że lista części w akcie jest
   identyczna z tabelą w skrypcie** (inaczej się wywraca). `nodeId` to urząd obsługujący ministra, `dysponentNodeId` to
   stanowisko ministra, `dysponentVerified: true`.
2. **Rozporządzenie o klasyfikacji wskazuje „ministra właściwego do spraw …”** (79, 82, 84: budżet i finanse publiczne;
   80: administracja publiczna). Konkretny minister wynika z aktów z pkt 1. `dysponentVerified: true`.
3. **Część nosi nazwę instytucji, która ma węzeł w grafie** (np. 07 NIK, 58 GUS, 73 ZUS). `nodeId` to ten węzeł. Skrypt
   sprawdza zgodność nazw: rdzenie słów z urzędowej nazwy części muszą występować w nazwie, skrócie albo aliasach węzła
   (celowo błędne przypisanie 07 → GUS albo 85/02 → Lubelski UW jest wykrywane). Dysponentem jest kierownik jednostki;
   nazwę stanowiska skrypt bierze z pola `head` węzła i **oznacza jako niezweryfikowaną w akcie szczegółowym**
   (`dysponentVerified: false`). Dotyczy 38 części.
4. **Wojewodowie.** Podczęść 85/xx → urząd wojewódzki (`nodeId`) i wojewoda (`dysponentNodeId`); województwo wynika z nazwy
   podczęści, a to, że dysponentem jest wojewoda, z art. 2 pkt 8 u.f.p. `dysponentVerified: true`.

Gdy żadna podstawa nie zachodzi, `nodeId` zostaje `null`, a powód jest w `note`.

| Minister | Części | Akt |
|---|---|---|
| Minister Obrony Narodowej | 29 | [Dz.U. 2023 poz. 2707](https://eli.gov.pl/eli/DU/2023/2707/ogl) |
| Minister Funduszy i Polityki Regionalnej | 34 | [Dz.U. 2023 poz. 2711](https://eli.gov.pl/eli/DU/2023/2711/ogl) |
| Minister Rodziny, Pracy i Polityki Społecznej | 31, 44, 63 | [Dz.U. 2023 poz. 2715](https://eli.gov.pl/eli/DU/2023/2715/ogl) |
| Minister Edukacji | 30 | [Dz.U. 2023 poz. 2717](https://eli.gov.pl/eli/DU/2023/2717/ogl) |
| Minister Cyfryzacji | 27 | [Dz.U. 2023 poz. 2720](https://eli.gov.pl/eli/DU/2023/2720/ogl) |
| Minister Infrastruktury | 21, 22, 39, 69 | [Dz.U. 2023 poz. 2725](https://eli.gov.pl/eli/DU/2023/2725/ogl) |
| Minister Nauki i Szkolnictwa Wyższego | 28, 67, 90 | [Dz.U. 2025 poz. 68](https://eli.gov.pl/eli/DU/2025/68/ogl) |
| Minister Spraw Zagranicznych | 23, 45 | [Dz.U. 2025 poz. 993](https://eli.gov.pl/eli/DU/2025/993/ogl) |
| Minister Aktywów Państwowych | 26, 55 | [Dz.U. 2025 poz. 994](https://eli.gov.pl/eli/DU/2025/994/ogl) |
| Minister Klimatu i Środowiska | 41, 51 | [Dz.U. 2025 poz. 995](https://eli.gov.pl/eli/DU/2025/995/ogl) |
| Minister Kultury i Dziedzictwa Narodowego | 24 | [Dz.U. 2025 poz. 996](https://eli.gov.pl/eli/DU/2025/996/ogl) |
| Minister Finansów i Gospodarki | 18, 19, 20 | [Dz.U. 2025 poz. 997](https://eli.gov.pl/eli/DU/2025/997/ogl) |
| Minister Spraw Wewnętrznych i Administracji | 17, 42, 43 | [Dz.U. 2025 poz. 999](https://eli.gov.pl/eli/DU/2025/999/ogl) |
| Minister Rolnictwa i Rozwoju Wsi | 32, 33, 35, 62 | [Dz.U. 2025 poz. 1000](https://eli.gov.pl/eli/DU/2025/1000/ogl) |
| Minister Sportu i Turystyki | 25, 40 | [Dz.U. 2025 poz. 1002](https://eli.gov.pl/eli/DU/2025/1002/ogl) |
| Minister Zdrowia | 46 | [Dz.U. 2025 poz. 1004](https://eli.gov.pl/eli/DU/2025/1004/ogl) |
| Minister Sprawiedliwości | 15, 37 | [Dz.U. 2025 poz. 1005](https://eli.gov.pl/eli/DU/2025/1005/ogl) |
| Minister Energii | 47, 48 | [Dz.U. 2025 poz. 1206](https://eli.gov.pl/eli/DU/2025/1206/ogl) (t.j.) |

Rozstrzygnięcia warte zapamiętania:

- **Części 18, 19 i 20** ma jeden dysponent, Minister Finansów i Gospodarki, ale § 1 ust. 4 jego rozporządzenia mówi, że
  w działach budownictwo i gospodarka obsługuje go Ministerstwo Rozwoju i Technologii, a w działach budżet, finanse publiczne
  i instytucje finansowe Ministerstwo Finansów. Stąd 18 i 20 → `pl-ministerstwo-rozwoju-i-technologii`, 19 → `pl-ministerstwo-finansow`.
- **Część 15 „Sądy powszechne”** → węzeł zbiorczy `pl-sady-powszechne` (zgodny z nazwą części); dysponent: Minister
  Sprawiedliwości. **15/01** nosi nazwę „Ministerstwo Sprawiedliwości” → `pl-ministerstwo-sprawiedliwosci`.
- **Część 67 „Polska Akademia Nauk”** → węzeł PAN (nazwa części), ale dysponentem jest Minister Nauki i Szkolnictwa Wyższego
  (akt). **Część 90 „Akademia Kopernikańska”** i **80 „Regionalne izby obrachunkowe”** nie mają własnych węzłów, więc `nodeId`
  wskazuje urząd dysponenta wskazanego w akcie (MNiSW, MSWiA); jest to opisane w `note`.
- **Części 79, 82, 84** (dług, subwencje, składka do UE) → `pl-ministerstwo-finansow`, bo dysponenta wskazuje rozporządzenie
  o klasyfikacji. Nie udają wydatków urzędu: należą do grup technicznych (`groups[].kind = "technical"`).
- Przypisania odzwierciedlają **obecny** podział kompetencji (akty z lat 2023–2025, stan grafu z 2026-09-17), a kwoty dotyczą
  lat 2021–2025, kiedy część tych części miała innych dysponentów (np. do lipca 2025 r. częściami 18 i 20 dysponował
  Minister Rozwoju i Technologii: Dz.U. 2023 poz. 2721 i Dz.U. 2024 poz. 739). Historii dysponentów nie odtwarzano.

### Części i podczęści bez węzła

| Kod | Nazwa | Wykonanie 2025 | Powód |
|---|---|---:|---|
| 81 | Rezerwa ogólna | 0 | część techniczna; rezerwą dysponuje Rada Ministrów (art. 155 ust. 1 u.f.p.), co jest zapisane w `dysponentNodeId` |
| 83 | Rezerwy celowe | 0 | część techniczna; podziału dokonuje Minister Finansów (art. 154 ust. 1 u.f.p.) |
| 85 | Województwa (zbiorczo) | 58 570 330,26 | suma 16 budżetów wojewodów; węzły mają podczęści 85/02–85/32, w grafie nie ma węzła zbiorczego |
| 86 i 86/01–86/97 | Samorządowe kolegia odwoławcze (49) | 214 585,56 | brak węzłów SKO w grafie; dysponenta nie ustalono w sprawdzonych aktach |
| 91 | Biuro Rady Fiskalnej | 1 411,70 | brak węzła Rady Fiskalnej; dysponenta nie ustalono |
| 15/02–15/12 | 11 obszarów apelacji | 16 968 224,39 | w grafie nie ma węzłów poszczególnych sądów apelacyjnych; podczęść obejmuje wszystkie sądy z obszaru apelacji. Część macierzysta 15 ma węzeł. |

Udział wykonania 2025 z przypisanym węzłem zależy od tego, jak liczyć, więc podajemy trzy miary (wszystkie w
`meta.verification.nodeCoverage`):

| Miara | Wynik |
|---|---:|
| część ma węzeł albo mają go jej podczęści (najbliższe temu, co zobaczy użytkownik) | **99,98%** |
| tylko liście (podczęści tam, gdzie są, inaczej część) | 98,03% |
| tylko części najwyższego poziomu (bez zaglądania do podczęści; traci całą część 85) | 93,24% |

### Porównanie z polem `budgetPart` w grafie

68 węzłów grafu ma podpowiedź `budgetPart`. Skrypt sprawdza każdą: **sprzeczności 0**. Podpowiedzi są jednak niepełne.
Części, które mają `nodeId` w `budget.json`, a nie mają podpowiedzi w grafie: 15/01, 17, 43, 49, 54, 60, 61, 64, 66, 68,
72, 73, 79, 80, 82, 84. W szczególności MSWiA ma w grafie tylko „42”, a akt wymienia 17, 42 i 43; Ministerstwo
Sprawiedliwości ma „37”, a akt wymienia 15 i 37. Grafu nie zmieniano (to zadanie było czysto danowe).

## 6. Grupy (wewnętrzny pierścień)

**Reguła.** Część należy do grupy tego działu klasyfikacji budżetowej, który ma w niej największe **wykonanie w 2025 r.**
Gdy wykonanie całej części jest zerowe (rezerwy), decyduje największy **plan**. Dział 758 „Różne rozliczenia” jest workiem
technicznym (mieszczą się w nim rezerwy, subwencje, składka do UE, programy regionalne, Fundusz Kościelny), więc w nim
rozstrzyga **rozdział** o największej kwocie. Podczęści dziedziczą grupę części macierzystej. Tabele są jawne w skrypcie
(`DZIAL_TO_GROUP`, `ROZDZIAL_758_TO_GROUP`); nieznany dział albo rozdział wywraca skrypt, zamiast trafić „gdzieś”.
Podstawę decyzji dla każdej części zapisuje `groupBasis` (dział, jego udział, ewentualnie rozdział).

Grup jest 11 (górna granica ustalonego przedziału 8–11). Pięć pozycji technicznych musiało dostać własne, uczciwie nazwane
grupy, więc na grupy funkcjonalne zostało sześć miejsc. Stąd dwa świadome połączenia: wymiar sprawiedliwości (755) z władzą
i administracją (750, 751; dział 751 i tak obejmuje sądy i trybunały) oraz rolnictwo i środowisko z gospodarką.

### Tabela „dział → grupa”

| Grupa (`code`) | Nazwa | Działy |
|---|---|---|
| `obrona` | Obrona narodowa i bezpieczeństwo | 752 Obrona narodowa · 754 Bezpieczeństwo publiczne i ochrona przeciwpożarowa |
| `administracja` | Władza państwowa, administracja i wymiar sprawiedliwości | 720 Informatyka · 750 Administracja publiczna · 751 Urzędy naczelnych organów władzy państwowej, kontroli i ochrony prawa oraz sądownictwa · 755 Wymiar sprawiedliwości · 756 Dochody od osób prawnych, od osób fizycznych (…) oraz wydatki związane z ich poborem |
| `zdrowie` | Ochrona zdrowia | 851 Ochrona zdrowia |
| `nauka-kultura` | Nauka, oświata, kultura i sport | 730 Szkolnictwo wyższe i nauka · 801 Oświata i wychowanie · 854 Edukacyjna opieka wychowawcza · 921 Kultura i ochrona dziedzictwa narodowego · 926 Kultura fizyczna |
| `spoleczne` | Rodzina i polityka społeczna | 852 Pomoc społeczna · 853 Pozostałe zadania w zakresie polityki społecznej · 855 Rodzina |
| `gospodarka` | Gospodarka, infrastruktura, rolnictwo i środowisko | 010 Rolnictwo i łowiectwo · 020 Leśnictwo · 050 Rybołówstwo i rybactwo · 100 Górnictwo i kopalnictwo · 150 Przetwórstwo przemysłowe · 400 Wytwarzanie i zaopatrywanie w energię elektryczną, gaz i wodę · 500 Handel · 550 Hotele i restauracje · 600 Transport i łączność · 630 Turystyka · 700 Gospodarka mieszkaniowa · 710 Działalność usługowa · 900 Gospodarka komunalna i ochrona środowiska · 925 Ogrody botaniczne i zoologiczne oraz naturalne obszary i obiekty chronionej przyrody |
| `ubezpieczenia` (techniczna) | Ubezpieczenia społeczne (ZUS i KRUS) | 753 Obowiązkowe ubezpieczenia społeczne |
| `dlug` (techniczna) | Obsługa długu publicznego | 757 Obsługa długu publicznego |
| `samorzady`, `ue`, `rezerwy` (techniczne) | patrz niżej | 758 Różne rozliczenia, według rozdziału |

Dział 758 według rozdziału:

| Rozdziały | Grupa |
|---|---|
| 75817 Ogólna rezerwa budżetowa Rady Ministrów · 75818 Rezerwy ogólne i celowe | `rezerwy` „Rezerwy budżetowe” |
| 75801–75807, 75809, 75833–75835 (części i uzupełnienia subwencji ogólnej, subwencja ogólna dla JST, rezerwa na uzupełnienie dochodów JST) | `samorzady` „Subwencje ogólne dla samorządów” |
| 75850 Rozliczenia z budżetem ogólnym Unii Europejskiej z tytułu środków własnych | `ue` „Składka do budżetu Unii Europejskiej” |
| 75863–75866, 75868 (programy regionalne współfinansowane z UE) | `gospodarka` |
| 75814 Różne rozliczenia finansowe · 75822 Fundusz Kościelny · 75823 Partie polityczne i komitety wyborcze | `administracja` (brak lepszej grupy funkcjonalnej; to decyzja redakcyjna, nie fakt ze źródła) |

W 2025 r. rozdział rozstrzygał w sześciu częściach: 34 (75866), 43 (75822), 81 (75817), 82 (75834), 83 (75818), 84 (75850).

### Wynik (2025)

| Grupa | Rodzaj | Części | Wykonanie 2025, mld zł | Udział | Plan 2026, mld zł | Kody części |
|---|---|---:|---:|---:|---:|---|
| `obrona` | funkcjonalna | 5 | 168,5 | 19,4% | 169,0 | 29, 42, 56, 57, 59 |
| `administracja` | funkcjonalna | 44 | 84,8 | 9,7% | 64,2 | 01–17, 19, 23, 27, 37, 43, 45, 47, 49, 50, 52, 53, 55, 58, 60, 61, 64, 65, 66, 68, 71, 74, 75, 80, 86, 88, 89, 91 |
| `zdrowie` | funkcjonalna | 1 | 46,1 | 5,3% | 45,0 | 46 |
| `nauka-kultura` | funkcjonalna | 6 | 46,2 | 5,3% | 44,2 | 24, 25, 28, 30, 67, 90 |
| `spoleczne` | funkcjonalna | 5 | 63,2 | 7,3% | 49,7 | 31, 44, 54, 63, 85 |
| `gospodarka` | funkcjonalna | 16 | 55,0 | 6,3% | 49,9 | 18, 21, 22, 26, 32, 33, 34, 35, 39, 40, 41, 48, 51, 62, 69, 76 |
| `ubezpieczenia` | techniczna | 2 | 210,5 | 24,2% | 238,8 | 72, 73 |
| `dlug` | techniczna | 2 | 109,8 | 12,6% | 91,8 | 20, 79 |
| `samorzady` | techniczna | 1 | 50,8 | 5,8% | 52,7 | 82 |
| `ue` | techniczna | 1 | 35,3 | 4,1% | 39,6 | 84 |
| `rezerwy` | techniczna | 2 | 0,0 | 0,0% | 74,1 | 81, 83 |

### Skutki reguły, o których trzeba wiedzieć

Reguła jest mechaniczna i zgodna z zamówieniem, ale w kilku miejscach daje wynik nieoczywisty. Wszystkie są w `note` albo
w `groupBasis`:

- **Część 20 „Gospodarka” trafia do „Obsługi długu publicznego”.** 94% jej wykonania w 2025 r. to dział 757, rozdział 75704
  „Rozliczenia z tytułu poręczeń i gwarancji udzielonych przez Skarb Państwa” (34 662 332 tys. zł). Ministerstwo Rozwoju
  i Technologii dostaje więc w pierścieniu segment „długu”. Jeśli w widoku ma to wyglądać inaczej, trzeba zmienić regułę,
  a nie dane.
- **Część 73 ZUS** jest w „Ubezpieczeniach społecznych”, choć dział 753 to tylko 53% jej wykonania; reszta to głównie dział
  855 „Rodzina” (świadczenia wypłacane przez ZUS).
- **Część 85 Województwa** jest w „Rodzinie i polityce społecznej” przy udziale największego działu (855) zaledwie 33%.
  Budżety wojewodów obejmują 29 działów. Podczęści dziedziczą tę grupę.
- **Części 19 i 45** są w „administracji”, bo Krajowa Administracja Skarbowa i placówki zagraniczne księgowane są w dziale 750.
- **Rezerwy mają wykonanie 0 z definicji**, więc w widoku wykonania ich segment znika, a w widoku planu ma 87,6 mld zł (2025).
  Różnica między planem a wykonaniem innych części to w dużej mierze właśnie rozdysponowane rezerwy (np. część 19: plan
  16,1 mld zł, wykonanie 38,4 mld zł).
- Części, w których największy dział ma mniej niż 70% wykonania (grupa jest tam najmniej oczywista): 06, 21, 24, 32, 34,
  37, 41, 42, 51, 63, 68, 69, 73, 85.

## 7. Historia 2021–2024

Układ arkuszy jest ten sam od 2021 r., więc wszystkie lata czyta ten sam kod i przechodzą tę samą walidację. Numeracja
części w latach 2021–2025 się nie zmieniła; **części nie łączono ani nie przenumerowywano**. Różnice:

- **48**: w latach 2021–2024 „Gospodarka złożami kopalin”, od 2025 r. „Gospodarka surowcami energetycznymi” (Dz.U. 2024
  poz. 1195, stosowane od budżetu 2025). Szereg jest pod jednym numerem, a dawna nazwa jest w `years[rok].nameInSource`
  i w `note`. Zakres mógł się różnić; nie korygowano.
- **89**: do 2023 r. „Państwowa Komisja do spraw wyjaśniania przypadków czynności skierowanych przeciwko wolności seksualnej
  i obyczajności wobec małoletniego poniżej lat 15”, od 2024 r. obecna nazwa. Tak samo oznaczone.
- **90** Akademia Kopernikańska: brak w 2021 r. **91** Biuro Rady Fiskalnej: tylko 2025 (część dodana 15.02.2025 r., Dz.U.
  2025 poz. 189; plan z ustawy = 0, środki dopiero w planie po zmianach).
- **Części 78**, wymienianej w założeniach zadania, nie ma w żadnym z pięciu lat: pozycje 36, 38, 70 i 78 są w rozporządzeniu
  uchylone, a obsługa długu Skarbu Państwa to część 79.
- Części 77, 87, 97 i 98 istnieją w klasyfikacji, ale dotyczą dochodów oraz przychodów i rozchodów, więc nie mają wydatków.
- 13 i 19 różnią się między latami tylko typografią (myślnik, spacja po przecinku); skrypt to normalizuje.

**Porównywalność w czasie jest ograniczona.** Kwoty są nominalne (bez korekty o inflację i bez odniesienia do PKB). Między
latami mógł się też zmieniać zakres tego, co jest finansowane z budżetu państwa, a co z funduszy poza nim; z samego zbioru
tego nie widać i **w ramach tego zadania nie było to weryfikowane w źródłach urzędowych**. Przed pokazaniem wykresu historii
(wzrost z 517 mld zł w 2022 r. do 870 mld zł w 2025 r.) warto to sprawdzić w uzasadnieniach do ustaw budżetowych.

**Znana niespójność w arkuszu MF.** W arkuszu rezerw za 2023 r. (rok nowelizacji ustawy budżetowej) w kolumnie „a” drugi
blok działu 758 (rezerwy dodane w trakcie roku, 16 163 834 tys. zł) nie wchodzi do kwoty części 83 (65 444 572 tys. zł), choć
w kolumnach f, g i b wchodzi. Kwota części zgadza się z wierszem OGÓŁEM i z plikiem 011; niespójny jest tylko podział planu
części 83 na działy w 2023 r., którego `budget.json` nie zawiera. Skrypt nie wycisza tej walidacji, tylko sprawdza, że
rozbieżność wynosi dokładnie tyle (`KNOWN_SOURCE_ISSUES`); gdy MF poprawi plik, skrypt się wywróci i wpis trzeba będzie usunąć.

## 8. Plan 2026

Załączniki do ustawy budżetowej są tylko w PDF. Skrypt wyciąga tekst przez `pdftotext -layout` (poppler) i czyta załącznik
nr 2: wiersze części (kod, nazwa wersalikami, Poz. = 1, kwota planu) oraz wiersze działów (do walidacji). Nazwy zawinięte
do dwóch linii (13, 18, 89, 86/21, 86/59) są obsłużone; numery stron wplecione w kolumny kwot są usuwane przed odczytem.

Plan przyjmowany jest tylko wtedy, gdy przejdzie **wszystkie** sprawdzenia. W przeciwnym razie `planYear = null`, a powód
trafia do `meta.planNote`. Wynik ostatniego przebiegu:

| Sprawdzenie | Wynik |
|---|---|
| kwota z art. 1 ust. 2 ustawy = wiersz „Ogółem” załącznika | 918 940 000 = 918 940 000 |
| suma 84 części = „Ogółem” (bez tolerancji, liczby całkowite) | 918 940 000 = 918 940 000 |
| suma podczęści 15/xx, 85/xx, 86/xx = część macierzysta | 18 780 934 · 47 538 725 · 205 112, wszystkie zgodne |
| części, w których suma działów ≠ plan części | 0 ze 161 |
| działy niezgodne z zestawieniem zbiorczym według działów (początek załącznika) | 0 z 31 |

Części 91 w ustawie na 2026 r. nie ma (jest rezerwa celowa „na realizację zadań wynikających z ustawy o Radzie Fiskalnej”),
więc wpis 91 nie ma klucza `2026`.

## 9. Weryfikacja (przebieg z 2026-09-18)

Wszystkie poniższe sprawdzenia są w skrypcie i **każde niepowodzenie kończy go kodem ≠ 0**. Pełny zapis jest w `meta.verification`.

1. **Sumy części = wiersz OGÓŁEM** (plik 011), bez podwójnego liczenia podczęści, tolerancja 0,001 tys. zł (1 zł). Różnica
   w każdym roku i każdej kolumnie (plan, plan po zmianach, wykonanie, niewygasające): **0**. Kwoty w tabeli w pkt 1.
   Dodatkowo OGÓŁEM z pliku 011 = wiersz „2. WYDATKI BUDŻETU PAŃSTWA” z „Zestawienia ogólnego” (plik 005): plan równy planowi,
   a wykonanie + niewygasające równe kwocie wykonania z zestawienia, we wszystkich pięciu latach.
2. **Suma podczęści = część macierzysta** (15, 85, 86) we wszystkich latach i kolumnach: zgodne.
3. **Suma `breakdown` = kwota części** dla wszystkich 162 wpisów, w trzech kolumnach: zgodne. Dodatkowo suma rozdziałów =
   dział, a suma działów po częściach = wiersz działu w pliku 011, we wszystkich latach (jeden znany wyjątek, pkt 7).
4. **Drugi, niezależny odczyt.** Te same kwoty odczytane z **PDF sprawozdania** (Tom I i II w tym samym ZIP-ie za 2025 r.):
   inny plik, inny format, inny parser (`pdftotext` i wyrażenia regularne zamiast `xlrd`/`openpyxl`). PDF podaje pełne tys. zł,
   więc porównanie jest po zaokrągleniu, z tolerancją 1 tys. zł. Próba: 10 największych części (73, 29, 79, 85, 82, 42, 46,
   19, 20, 84) i 15 losowych wpisów (ziarno 2025: 01, 12, 15/02, 15/07, 15/11, 37, 55, 85/28, 85/30, 85/32, 86/07, 86/47,
   86/73, 86/87, 86/93). **Zgodnych 25 z 25, różnic 0.** Jednorazowo, poza skryptem, to samo porównanie puszczono na
   wszystkich 162 wpisach (484 kwoty): **różnic 0**.
   W trakcie prac drugi odczyt wykazał jedną rozbieżność (część 82, brak „planu po zmianach” w odczycie z PDF). Przyczyną był
   parser PDF, nie dane: w PDF wiersz „b” stoi w tej samej linii co dalszy ciąg zawiniętej nazwy części. Po poprawce kwota
   z PDF (50 770 513) zgadza się z arkuszem (50 770 513,02).
5. **Każde `nodeId` i `dysponentNodeId` istnieje w `graph.json`**: tak (w przeciwnym razie skrypt się wywraca). Udział
   wykonania z węzłem: 99,98% / 98,03% / 93,24% zależnie od miary (pkt 5).
6. **Akty o ministrach**: 18 z 18 zgodnych z tabelą w skrypcie. **Nazwy części**: 162 z 162 zgodne z rozporządzeniem
   (po normalizacji wielkości liter i myślników). **Podpowiedzi `budgetPart` w grafie**: sprzeczności 0.
7. **Testy negatywne** (ręczne): zmiana kwoty jednej części o 1, o 0,01 i zmiana kwoty podczęści są wykrywane; podmieniona
   suma SHA-256 pliku źródłowego jest wykrywana; `--offline` bez pliku w pamięci podręcznej kończy się błędem.
8. **Powtarzalność**: dwa przebiegi z tą samą `--date` dają identyczny plik (SHA-256 zgodne), także po ponownym pobraniu
   plików z sieci.

Czego weryfikacja **nie** obejmuje: drugi odczyt z PDF dotyczy tylko 2025 r. (starsze ZIP-y nie zawierają PDF). Lata
2021–2024 są sprawdzone sumami kontrolnymi z pkt 1–3, ale nie drugim nośnikiem.

## 10. Znane ograniczenia

- **Budżet państwa to nie cały sektor finansów publicznych.** Poza nim są m.in.: budżet środków europejskich (osobny załącznik
  i osobne arkusze sprawozdania), państwowe fundusze celowe (FUS, Fundusz Pracy, FGŚP i inne; w budżecie widać tylko dotacje
  do nich, np. w części 73), NFZ, agencje wykonawcze, instytucje gospodarki budżetowej, państwowe osoby prawne, fundusze
  w BGK i PFR oraz samorządy (w budżecie tylko subwencje i dotacje dla nich). Suma pierścienia to „wydatki budżetu państwa”,
  nie „wydatki państwa”.
- **Część to nie urząd.** Część odpowiadająca działowi administracji (np. 46 „Zdrowie”) obejmuje dotacje, świadczenia
  i jednostki podległe, a nie koszt ministerstwa. Koszt samego urzędu widać dopiero na poziomie rozdziału (np. 75001
  „Urzędy naczelnych i centralnych organów administracji rządowej”), którego `budget.json` nie zawiera (parser go czyta,
  więc łatwo dodać).
- **Dysponent a urząd.** Jeden minister może mieć kilka części, a jedną część mogą obsługiwać różne urzędy w różnych latach.
  Przypisania są według stanu obecnego (pkt 5).
- **Dysponent 38 części jest niezweryfikowany w akcie szczegółowym** (`dysponentVerified: false`): to kierownik instytucji
  wzięty z grafu. W szczególności nie sprawdzono w ustawach ustrojowych, kto formalnie dysponuje częściami 16 (KPRM) i 88
  (prokuratura). Dla 15/02–15/12, 85 (zbiorczo), 86 i 91 dysponent jest `null`.
- **Grupy są uproszczeniem.** Część trafia do grupy w całości, według jednego działu (pkt 6). Dokładniejszy obraz funkcjonalny
  daje `breakdown`.
- **Porównywalność lat** jest ograniczona (pkt 7). Nie przeliczano na ceny stałe ani na % PKB.
- **Plan 2026 to ustawa, nie plan po zmianach.** Wykonanie za 2026 r. MF opublikuje w połowie 2027 r.
- `meta.sources[].retrievedAt` to data pobrania pliku do pamięci podręcznej (z `_manifest.json`, a gdy go brak, z daty pliku).

## 11. Jak odświeżyć dane za rok

Według dat zasobów w API sprawozdanie za rok N trafia do zbioru 163 zwykle w czerwcu roku N+1 (za 2021: 3.06.2022, za 2022:
21.06.2023, za 2023: 4.06.2024, za 2025: 11.06.2026), ale za 2024 r. dopiero 18.08.2025. Ustawę budżetową na 2026 r. ogłoszono
20.01.2026.

1. `python3 scripts/build-budget.py --list-resources` wypisze zasoby zbioru 163. Dodaj nowy rok do tabeli `YEARS` (adres, nazwa
   pliku w pamięci podręcznej). Przy pierwszym pobraniu wpisz `'sha256': None`: skrypt wypisze wtedy policzoną sumę, którą
   trzeba wkleić do tabeli.
2. Ustaw `CURRENT_YEAR` i `PLAN_YEAR`. Dodaj nową ustawę budżetową do `ACTS` (klucz `ub2026` jest użyty w kodzie z nazwy:
   przy zmianie roku zmień klucz i odwołania do niego) i zaktualizuj adres ELI.
3. Sprawdź w ELI, czy zmieniło się rozporządzenie o klasyfikacji części (nowy tekst jednolity albo nowelizacja; od budżetu
   2027 część 84 nazywa się „Zasoby własne Unii Europejskiej”) i czy wydano nowe rozporządzenia o zakresie działania
   ministrów (po każdej rekonstrukcji rządu). Zaktualizuj `ACTS` i `MINISTER_ACTS`; skrypt sam wykryje, że lista części w akcie
   nie zgadza się z tabelą.
4. Uruchom `python3 scripts/build-budget.py`. Typowe powody zatrzymania i co wtedy zrobić:
   - *nieznany dział albo rozdział 758*: dopisz go do `DZIAL_TO_GROUP` / `ROZDZIAL_758_TO_GROUP` i do tabeli w pkt 6;
   - *nowa część bez przypisania i bez powodu*: dodaj ją do właściwej tabeli w sekcji 2 skryptu albo do `NO_NODE_REASON`;
   - *przypisanie po nazwie bez pokrycia w nazwie węzła*: popraw węzeł albo dodaj uzasadniony wyjątek do `NAME_MATCH_EXCEPTIONS`;
   - *wzorzec pliku nie pasuje*: MF zmieniło nazwy plików w ZIP-ie, popraw wzorce w `FILES`;
   - *drugi odczyt wykazał różnice*: najpierw sprawdź ręcznie wiersz w PDF (numer linii jest w komunikacie), bo winny bywa
     parser PDF, nie dane.
5. Przejrzyj `meta.verification` i zaktualizuj liczby w tym dokumencie (pkt 1, 5, 6, 8, 9).

Zależności: `python3 -m pip install --user xlrd openpyxl` oraz `pdftotext` z pakietu poppler (`brew install poppler`).
Bez `pdftotext` skrypt zadziała, ale ustawi `planYear = null`, weźmie nazwy części z arkusza (wersalikami) i pominie drugi
odczyt, o czym głośno poinformuje.
