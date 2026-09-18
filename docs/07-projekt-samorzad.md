# Projekt: samorząd terytorialny w Grafie Państwa

Stan: projekt z 18.09.2026. Decyzje właściciela z tego samego dnia: samorząd wchodzi do Grafu Państwa, pilot to województwo łódzkie, radni widoczni z nazwiska od początku. **Etap 0 (rama krajowa) jest zbudowany** (`scripts/jst/build-frame.py`, `data/jst/`). **Etap 1 (łódzkie) jest zrobiony**: nakładka `data/jst/overlay/10.json` z 226 potwierdzonymi osobami w 25 jednostkach (województwo, 21 powiatów, 3 miasta na prawach powiatu): zarządy, prezydia rad, zastępcy prezydentów, skarbnicy i sekretarze, każda osoba z adresem strony, cytatem i datą; niezależna sprawdzarka `scripts/jst/verify-overlay.py`. Luka: zarząd i prezydium rady powiatu bełchatowskiego (BIP bez treści, protokoły jako skany; OCR je czyta, ale robots.txt BIP zabrania automatom pobierać załączniki; właściciel dopuścił 18.09 werdykt `confirmed-manual` z etykietą „sprawdzone ręcznie” i powodem, więc te osiem osób jest na kole). **Warszawa (18.09, wieczór):** nakładka `overlay/14.json`: miasto (prezydium Rady, 4 zastępców Prezydenta, skarbnik, sekretarz) i 18 dzielnic (burmistrzowie, 54 zastępców, prezydia rad), 145 osób, wszystkie potwierdzone po dodaniu do sprawdzarki ciasteczek sesji (BIP m.st. Warszawy, Liferay, oddaje pustą odpowiedź na pierwsze żądanie bez ciasteczka). Dzielnice są osobnymi jednostkami (`kind: dzielnica`, kody 1465xx z PKW, 420 radnych z pliku `kandydaci_rady_dzielnic`) z własnym szablonem na ustawie o ustroju m.st. Warszawy (10 cytatów). **Etap 3 działa od 18.09**: cotygodniowa ponowna weryfikacja nakładek i przebudowa ramy w `weekly-update.py` oraz strażnik wyborów w toku kadencji `scripts/jst/watch-pkw.py` (portale wyników PKW, stan bazowy 915 pozycji). Dokument odpowiada na dwa pytania właściciela: kto i jak uruchamia zadania, żeby dane były aktualne, oraz jak rozszerzyć graf o województwa, powiaty i gminy.

## 1. Kto i jak uruchamia zadania (stan obecny, działa)

Nikt nie musi niczego klikać. Zadania uruchamiają się same według harmonogramu, a człowiek dostaje tylko to, co wymaga decyzji.

| Co | Kto uruchamia | Kiedy | Co robi człowiek |
|---|---|---|---|
| Aktualizacja danych (`.github/workflows/weekly-update.yml`) | GitHub Actions, harmonogram cron | poniedziałek 04:00 UTC, dodatkowo ręcznie przyciskiem „Run workflow” | nic, jeśli przebieg jest zielony |
| Zapis zmian | bot w tym samym przebiegu, tylko po 100% potwierdzeń w drugim odczycie i po komplecie testów | od razu | nic |
| Lista do przejrzenia (akty z Monitora Polskiego, zmiany statusu podstaw prawnych) | ten sam przebieg, jako zgłoszenie (issue) z etykietą `aktualizacja` | gdy jest co przejrzeć | sprawdza akt, poprawia właściwą część danych, zamyka zgłoszenie |
| Niepowodzenie (źródło niedostępne, test czerwony) | ten sam przebieg, jako zgłoszenie z linkiem do logów | gdy się zdarzy | czyta powód; dane w repozytorium zostają nietknięte |
| Wdrożenie na stronę | cron na serwerze WWW pobiera nowy commit z publicznego repozytorium | co godzinę | nic; GitHub nie ma żadnego dostępu do serwera |

Powiadomienia o zgłoszeniach GitHub wysyła mailem właścicielowi repozytorium. Jedna pułapka platformy: GitHub wyłącza harmonogramy w publicznych repozytoriach po 60 dniach bez aktywności. Tu jej nie ma, bo cotygodniowy przebieg zawsze zostawia commit (daty sprawdzenia części parlamentarnej).

Ta sama zasada ma obowiązywać dla samorządu: **automat zmienia dane tylko z rejestrów maszynowych i po niezależnym potwierdzeniu, reszta idzie do człowieka z dowodem.**

## 2. Skala i dlaczego to inny problem niż szczebel centralny

| Szczebel | Jednostek | Organy i osoby |
|---|---|---|
| Województwo | 16 | sejmik (552 radnych, potwierdzone w pliku PKW), zarząd z marszałkiem, urząd marszałkowski |
| Powiat | ok. 314 oraz ok. 66 miast na prawach powiatu | rada powiatu, zarząd ze starostą, starostwo |
| Gmina | ok. 2,5 tys. | rada gminy albo miasta, wójt, burmistrz albo prezydent, urząd, jednostki pomocnicze |
| Razem | ok. 2,8 tys. jednostek | ok. 47 tys. radnych i ok. 2,5 tys. wójtów, burmistrzów i prezydentów |

Dokładne liczby ma podać TERYT przy budowie, nie ten dokument. Graf centralny ma 570 węzłów i był budowany część po części przez agentów z weryfikatorem. Przy 2,8 tys. jednostek ta metoda jest za droga i za wolna. Samorząd trzeba **generować z rejestrów**, a ręczną i półautomatyczną pracę zostawić tylko tam, gdzie rejestru nie ma.

Sprzyja temu prawo: ustrój każdej gminy, powiatu i województwa jest taki sam, bo wynika z trzech ustaw. Relacje nie wymagają więc researchu dla każdej jednostki osobno. Wystarczy jeden zweryfikowany szablon na szczebel.

## 3. Model: jeden mały graf na jednostkę, jak `/us` i `/sf` w oryginale

CivLab nie rysuje rządu federalnego i miasta na jednym kole. Ma osobne grafy o tym samym języku wizualnym. Tak samo tutaj: każda jednostka samorządu dostaje własne koło, a nie dodatkowy pierścień na kole państwa.

**Szablon gminy** (ustawa o samorządzie gminnym):
- suweren w środku: mieszkańcy gminy,
- sektor stanowiący: rada gminy, jej przewodniczący, komisje (rewizyjna oraz skarg, wniosków i petycji są obowiązkowe),
- sektor wykonawczy: wójt, burmistrz albo prezydent miasta, zastępcy, sekretarz, skarbnik, urząd, jednostki organizacyjne jako kropki,
- jednostki pomocnicze: sołectwa, dzielnice, osiedla,
- sektor nadzoru i kontroli: wojewoda (nadzór nad legalnością), regionalna izba obrachunkowa (finanse), samorządowe kolegium odwoławcze, NIK, Prezes Rady Ministrów.

**Szablon powiatu:** mieszkańcy wybierają radę, rada wybiera zarząd i starostę, starosta kieruje starostwem i jest zwierzchnikiem powiatowych służb, inspekcji i straży.

**Szablon województwa:** mieszkańcy wybierają sejmik, sejmik wybiera zarząd i marszałka, marszałek kieruje urzędem marszałkowskim. Wojewoda jest tu węzłem wspólnym z grafem centralnym: `pl-wojewoda-…` już istnieje i staje się przejściem między kołem państwa a kołem województwa.

**Miasto na prawach powiatu** to szablon gminy z zadaniami powiatu.

Typy relacji zostają te same co w grafie centralnym (`elects`, `appoints`, `nominates`, `oversees`, `office`, `administers`). Przykłady z szablonu, z przepisami do potwierdzenia w ELI tym samym trybem weryfikatora co dotąd: organy gminy (art. 11a ustawy o samorządzie gminnym), wójt jako organ wykonawczy (art. 26), urząd jako aparat wójta (art. 33), organy nadzoru (art. 86), organy powiatu (art. 8 ustawy o samorządzie powiatowym), wybór zarządu przez radę (art. 27), organy województwa (art. 15 ustawy o samorządzie województwa), wybór zarządu przez sejmik (art. 32). **Numery artykułów w tym akapicie pochodzą z pamięci i nie były dziś sprawdzane.**

Model osób przejmuje ustalenie z zaparkowanego projektu kontroli obywatelskiej: **osoba jest trwała, mandat jest rolą** z datą początku i końca. Identyfikator osoby bez numeru PESEL: kod TERYT, znormalizowane nazwisko i imiona, rok wyborów. Ta sama osoba w dwóch radach to miękkie powiązanie, nigdy twarde scalenie.

## 4. Źródła

| Warstwa | Źródło | Stan sprawdzenia 18.09.2026 |
|---|---|---|
| Lista i hierarchia jednostek | rejestr TERYT GUS (TERC), kody 7-znakowe; usługa sieciowa opisana w zbiorze 747 na dane.gov.pl | zbiór istnieje (CC BY 4.0); usługa wymaga konta, pliki TERC do pobrania ze strony GUS: do sprawdzenia przy budowie |
| Wybrani radni sejmików, rad powiatów, rad gmin i dzielnic | PKW, arkusze wyborów samorządowych 2024: `kandydaci_sejmiki_wojewodztw`, `kandydaci_rady_powiatow`, `kandydaci_rady_gmin_do_20k`, `kandydaci_rady_gmin_powyzej_20k`, `kandydaci_rady_dzielnic` (CSV i XLSX) | **sprawdzone**: pliki się pobierają, mają kolumny `TERYT` i „Czy uzyskał mandat”; w pliku sejmików 552 mandaty |
| Wójtowie, burmistrzowie, prezydenci | PKW, `kandydaci_wbp` | **sprawdzone**: 6731 kandydatów, 1728 mandatów w pierwszej turze, kolumna o prawie do drugiej tury; wyniki ponownego głosowania trzeba dołączyć z osobnego pliku |
| Zmiany w trakcie kadencji | PKW: wybory uzupełniające i przedterminowe, wygaśnięcia mandatów | nie sprawdzone; to główne ryzyko aktualności |
| Starostowie, marszałkowie, zarządy, przewodniczący rad, zastępcy, skarbnicy, sekretarze | strony BIP jednostek; rejestr stron BIP na bip.gov.pl (ok. 2,8 tys. według wcześniejszego researchu) | brak rejestru maszynowego: tylko monitor stron i człowiek |
| Budżety jednostek | Ministerstwo Finansów, kwartalne sprawozdania budżetowe samorządów (Rb-27S, Rb-28S) w sekcji „Bazy danych” | potwierdzone we wcześniejszym researchu (`02-mapa-zrodel-i-ryzyk.md`) |
| Regionalne izby obrachunkowe | dane.gov.pl, zbiór 120 (CC0) | **sprawdzone**: istnieje, dane teleadresowe z 2019 r., więc tylko jako punkt startu |
| Podstawy prawne | trzy ustawy samorządowe przez ELI | tryb jak w grafie centralnym |

Pliki PKW zawierają też wiek, wykształcenie i miejsce zamieszkania kandydatów. **Tych pól nie przenosimy.** Publikujemy wyłącznie: imię i nazwisko, funkcję, jednostkę, komitet wyborczy, datę i źródło.

## 5. Architektura danych

Jednego pliku `graph.json` nie da się już utrzymać. Dane samorządowe są dzielone na małe pliki generowane skryptem.

```
data/jst/
  index.json                     wszystkie jednostki: TERYT, nazwa, typ, jednostka nadrzędna, liczniki, data sprawdzenia
  search/<kod województwa>.json  indeks wyszukiwarki: nazwy jednostek i osób pełniących funkcje
  units/<2 cyfry>/<TERYT>.json   mały graf jednostki: węzły, relacje, osoby, provenance (ten sam schemat co graph.json)
  budget/<2 cyfry>/<TERYT>.json  budżet jednostki (ten sam schemat co budget.json)
  state/                         stan zadań: skróty plików źródłowych, daty, liczniki
scripts/jst/
  build-frame.py                 TERYT + PKW + szablony → units/ i index.json (deterministyczny)
  templates/{gmina,powiat,wojewodztwo}.json   węzły i relacje szablonu z przepisami
  watch-pkw.py                   wybory uzupełniające, wygaśnięcia mandatów
  watch-bip.py                   monitor stron (skrót treści, odczyt przy zmianie, propozycja)
  build-budgets.py               sprawozdania MF → budget/
```

Zasady:
- **Pliki z repozytorium, bez bazy danych**, dopóki nie pojawi się potrzeba zapytań przekrojowych albo edycji przez wiele osób. Statyczne pliki są darmowe w hostingu, mają historię w gicie i działają z obecnym wdrożeniem. Baza (wcześniej rozważany Supabase) wchodzi dopiero z publicznym API do zapytań.
- **Stabilna kolejność i wcięcia w plikach**, żeby różnice w gicie były małe i czytelne. Surowe pliki źródłowe zostają poza repozytorium; w repozytorium są adresy i sumy kontrolne, jak przy budżecie.
- Widok ładuje tylko plik wybranej jednostki (kilkanaście do kilkudziesięciu kB), nie całość.
- Strony osób mają wyłączone indeksowanie. To ustalenie z projektu kontroli obywatelskiej (precedens TK K 2/23 dotyczy indeksowalnej publikacji danych osób publicznych).

## 6. Interfejs

- Wejście z koła państwa: wojewoda prowadzi do koła województwa; wyszukiwarka rozumie nazwy miejscowości („Piaseczno”, „powiat piaseczyński”).
- Nawigacja w górę i w dół: województwo, powiat, gmina, z okruszkami w nagłówku.
- Koło jednostki ma trzy sektory: stanowiący, wykonawczy, nadzór i kontrola. Radni są jak członkowie komisji w Sejmie: liczba miejsc na kole, nazwiska w panelu z podziałem na komitety.
- Przełącznik „Graf | Budżet” działa tak samo, z danymi Ministerstwa Finansów dla tej jednostki.
- Adres: `#jst=<TERYT>` oraz `#jst=<TERYT>&node=<id>`.

## 7. Zadania i harmonogram dla samorządu

| Zadanie | Źródło | Częstość | Tryb | Rozmiar przebiegu |
|---|---|---|---|---|
| Rama jednostek | TERYT | raz w miesiącu i po 1 stycznia | automat, zmiana listy jednostek idzie do przeglądu | jedno pobranie |
| Skład rad i organy wykonawcze z wyborów | PKW, arkusze wyborów powszechnych | po wyborach (następne w 2029 r.) | automat z kontrolą sum: liczba mandatów w pliku równa się liczbie mandatów w okręgach | kilka plików CSV |
| Zmiany w kadencji | PKW: wybory uzupełniające, przedterminowe, wygaśnięcia | co tydzień | automat tam, gdzie PKW podaje dane w arkuszach; reszta do przeglądu | mały |
| Zarządy powiatów i województw, przewodniczący rad | BIP, ok. 400 stron | co tydzień, w 16 równoległych zadaniach po województwach | półautomat: skrót strony, przy zmianie odczyt nazwisk modelem, propozycja jako pull request z cytatem i linkiem | ok. 400 pobrań |
| Zastępcy, skarbnicy, sekretarze w gminach | BIP, ok. 2,5 tys. stron | etap późniejszy, rotacyjnie: każda strona raz na 4 tygodnie | jak wyżej | ok. 600 pobrań tygodniowo |
| Budżety | Ministerstwo Finansów | raz na kwartał | automat z kontrolą sum jak w budżecie państwa | kilka plików |
| Podstawy prawne szablonów | ELI | co tydzień (już działa dla grafu centralnego) | lista do przeglądu | jedno zadanie |
| Poprawki od ludzi | zgłoszenia na GitHubie z linkiem do źródła urzędowego | na bieżąco | człowiek | pojedyncze |

Wykonanie: GitHub Actions z macierzą po województwach, każde zadanie z własnym plikiem stanu i limitem czasu. Pobieranie grzeczne: odstępy między żądaniami, nagłówek z adresem projektu, poszanowanie robots.txt, żadnego obchodzenia zabezpieczeń. Strony, które blokują automaty, trafiają na listę ręczną. Dla publicznego repozytorium standardowe maszyny GitHuba są bezpłatne; koszt pojawia się tylko przy modelu czytającym zmienione strony i jest proporcjonalny do liczby zmian, nie do liczby stron.

Mierniki, które mają być widoczne na stronie: odsetek jednostek ze sprawdzonym organem wykonawczym w ostatnich 30 dniach, liczba stron na liście ręcznej, wiek najstarszego niesprawdzonego rekordu w każdym województwie.

## 8. Etapy

| Etap | Zakres | Warunek zaliczenia |
|---|---|---|
| 0. Rama krajowa | wszystkie jednostki z TERYT, organy z szablonów, wybrani z PKW 2024 (rady, wójtowie, burmistrzowie, prezydenci), wojewoda jako przejście z grafu centralnego | liczba jednostek zgodna z TERYT; liczba mandatów zgodna z PKW w każdej jednostce; przepisy szablonów potwierdzone w ELI |
| 1. Pilot jednego województwa | zarząd województwa, starostowie i zarządy powiatów, przewodniczący rad; koło jednostki w interfejsie | 100% jednostek pilotażu ma organ wykonawczy ze źródłem; pokaz trzem osobom spoza projektu |
| 2. Budżety | sprawozdania MF dla wszystkich jednostek, widok „Budżet” | sumy zgodne ze źródłem dla każdej jednostki |
| 3. Cała Polska, szczebel powiatowy i wojewódzki | monitor ok. 400 stron BIP | mierniki aktualności z pkt 7 na stronie |
| 4. Urzędy gmin | zastępcy, skarbnicy, sekretarze; ewentualnie jednostki organizacyjne z rejestrów (szkoły z RSPO) | decyzja po etapie 3 na podstawie kosztu utrzymania |

Etap 0 jest w całości deterministyczny i nie wymaga modelu ani ręcznej pracy poza weryfikacją szablonów.

## 9. Ryzyka

- **Aktualność w trakcie kadencji.** Wybory dają stan na dzień wyborów. Wygaśnięcia mandatów, wybory uzupełniające, odwołania starostów i zarządów nie mają jednego rejestru. Bez etapu 3 dane powiatowe i wojewódzkie będą się starzeć.
- **Różnorodność stron BIP.** Wcześniejszy research wskazał, że wąskim gardłem jest odnalezienie właściwej podstrony, a nie odczyt. Większość stron pochodzi od kilku dostawców, więc wzorce adresów dla nich pokryją większość jednostek.
- **Osoby o tym samym nazwisku.** Bez numeru PESEL nie ma pewnej tożsamości między jednostkami. Dlatego tylko miękkie powiązania.
- **Prywatność.** Tylko funkcje publiczne i tylko z urzędowych źródeł; bez wieku, wykształcenia, adresu; strony osób bez indeksowania. Oświadczenia majątkowe to osobny, zaparkowany projekt i nie wchodzą do grafu.
- **Rozmiar repozytorium.** Kilka tysięcy plików zmienianych co tydzień. Pomaga stabilny zapis, zmiana tylko plików z faktyczną różnicą i trzymanie migawek w wydaniach (releases), nie w historii.

## 9a. Wnioski z pilota łódzkiego (18.09.2026)

- **Wynik:** 25 jednostek, 226 osób, wszystkie potwierdzone dwoma niezależnymi przebiegami sprawdzarki (`scripts/jst/verify-overlay.py`: każdy adres pobrany od nowa, nazwisko obok słowa funkcji w oknie 600 znaków). 141 osób ze stron BIP, 85 z oficjalnych stron urzędów tam, gdzie BIP nie ma składu albo jest nieczytelny. Data objęcia stanowiska tylko dla 20 osób (BIP podaje uchwałę z datą).
- **Czas:** ok. 26 minut zegarowych na 25 jednostek w czterech równoległych wątkach; powiat z czytelnym BIP 1–2 minuty, z BIP jako aplikacją JS albo bez strony składu 5–10 minut; weryfikacja 226 osób ok. 2,5 minuty przy limicie jednego żądania na sekundę na host.
- **Główna przeszkoda to odnalezienie właściwej podstrony, nie odczyt.** Nie ma maszynowego rejestru adresów BIP (wyszukiwarka gov.pl/bip to aplikacja JS bez otwartego API), zgadywane adresy `bip.<domena>` nie istniały w połowie przypadków; właściwy adres trzeba brać z odnośnika na stronie urzędu. Ta sama informacja bywa w BIP, na stronie urzędu, w tabeli kadencji dwa poziomy niżej albo w skanie PDF.
- **Dostawcy BIP:** bip.net.pl (Next.js: treść artykułu tylko w ładunku `self.__next_f.push`, nie w DOM nawet po Playwright; sprawdzarka go dekoduje), biuletyn.net, nv.pl, finn.pl, SSDIP na gov.pl, 4bip. Kilku dostawców pokrywa większość stron, więc przy skalowaniu na 380 powiatów i miast opłaca się adapter na dostawcę.
- **Blokady i awarie:** `powiat-pabianice.bip.info.pl` zabrania automatom w robots.txt (użyto oficjalnej strony, bez obchodzenia); `bip.piotrkow.pl` dał raz HTTP 500 (przebieg tygodniowy potrzebuje ponowienia); `www.powiatkutno.eu` nie odpowiada; `www.powiat.wielun.pl` ma certyfikat tylko na domenę bez `www`.
- **Luka:** powiat bełchatowski: BIP (SSDIP) ma puste kategorie „Starosta” i „Zarząd Powiatu”, oficjalna strona podaje tylko komisje, protokoły sesji to skany bez warstwy tekstu. Takie przypadki wymagają OCR albo człowieka.
- **Granica sprawdzarki:** potwierdza współwystępowanie nazwiska i słowa funkcji na stronie; nie wykryje strony niezaktualizowanej po zmianie na stanowisku. Stąd cotygodniowe ponowne sprawdzanie i obserwacja uchwał rad (etap 3).

## 10. Decyzje do podjęcia przez właściciela

1. Czy samorząd wchodzi do Grafu Państwa, czy zostaje osobnym projektem korzystającym z tego samego widoku. Dotąd był wymieniony w „Czego nie robimy”.
2. Które województwo na pilota.
3. Czy radni mają być widoczni z nazwiska od etapu 0 (ok. 47 tys. osób), czy na początek tylko organy wykonawcze i liczba mandatów.
4. Klucz do modelu czytającego zmienione strony BIP (potrzebny od etapu 1) jako sekret repozytorium.
