# Graf Państwa Polskiego — cele i opis projektu

## Skąd ten projekt
Punktem wyjścia jest praca [CivLab](https://www.civlab.org/) (Civilization Lab, non-profit z San Francisco):
[SF Gov Graph](https://graph.civlab.org/sf) i [US Gov Graph](https://graph.civlab.org/us). Ich teza:
„We cannot govern systems we don't understand, so we built a complete data model of the United States federal
government: entities, positions, people, and the legal relationships between them."

**Zadanie pierwotne: skopiować grafy CivLab dla Polski.** Ten sam model danych, ten sam sposób pokazania, te same
funkcje, ale na polskim prawie i polskich źródłach.

## Czym jest produkt
Interaktywna mapa państwa polskiego na szczeblu centralnym. W centrum stoi Naród jako suweren, wokół niego pierścienie
władzy i cztery sektory: ustawodawcza, wykonawcza, sądownicza oraz organy niezależne i kontrolne. Każdy organ ma
podstawę prawną, stronę urzędu, stanowisko szefa i osobę, która je obsadza. Kliknięcie organu pokazuje, kto go powołuje,
kto zatwierdza, kto nadzoruje i gdzie zasiada z urzędu, z cytatem przepisu przy każdej relacji.

Pod spodem leży otwarty model danych: **organ ⟂ stanowisko ⟂ osoba ⟂ relacja prawna**.

## Cel nadrzędny
Polski odpowiednik Gov Graph, rozpoznawalny dla kogoś, kto zna oryginał. **Wierność CivLab jest kryterium decyzji
projektowych.** Przy każdym wyborze pytamy najpierw „jak robi to CivLab?”. Odstępstwo wymaga uzasadnienia
(polskie prawo, polskie źródła albo zmierzony problem czytelności).

## Cele i mierniki

| # | Cel | Miernik | Stan (2026-09-17) |
|---|---|---|---|
| C1 | **Kompletny model szczebla centralnego**: organy, stanowiska, osoby, relacje prawne | pokrycie list referencyjnych (19 ministerstw, 23 jednostki PRM, 34 urzędy centralne z katalogu gov.pl, 16 województw, organy konstytucyjne); 100% węzłów z podstawą prawną; ≥ 95% relacji z cytatem | 570 węzłów, 1111 relacji, 889 osób (w tym wnętrze parlamentu: komisje, prezydia, konwenty, kluby i koła); podstawa prawna 100%; źródła w `04-zrodla-danych.md` |
| C2 | **Widok jak w CivLab**: mapa radialna, strona organu, legenda, wyszukiwarka, relacje po wyborze | parytet funkcji z listą z `01-analiza-civlab` §3; test: osoba znająca oryginał rozpoznaje ten sam produkt | viewer v0.1 działa; skórka w stylu CivLab w budowie; przełącznik skórek gotowy |
| C3 | **Warstwa żywa z dokumentów urzędowych**: ostatnie zmiany (wakaty, p.o., 7/30/90 dni) z Monitora Polskiego i stron urzędów. Bez newsów i bez power map (decyzja właściciela z 17.09.2026, patrz „Czego nie robimy”) | zmiana w Radzie Ministrów wykryta ≤ 24 h (Monitor Polski przez ELI); zmiana w kierownictwie urzędu ≤ 7 dni | zaprojektowane (`03-projekt` §5), niezbudowane |
| C4 | **Wiarygodność**: każdy fakt ma źródło i datę weryfikacji | 0 nazwisk bez `sourceUrl`; ≥ 90% osób zweryfikowanych w ostatnich 30 dniach; spory ustrojowe oznaczone jako spór | 512 z 543 osób zweryfikowanych adwersarialnie; TK, KRS, CBA, IPN oznaczone |
| C5 | **Otwartość** (świadome odstępstwo: CivLab ma dane zamknięte) | zrzuty JSON/CSV na CC BY 4.0, publiczne API do odczytu, strona „O danych” | dane w repo; API i strona „O danych” przed nami |
| C6 | **Budżet i etaty jak w SF Gov Graph** | część budżetowa i liczba etatów dla ≥ 80% organów | seedy etatów w `seeds/employee-count/`; nieużyte |

## Parytet funkcji z CivLab

| Funkcja oryginału | Polska wersja |
|---|---|
| Mapa radialna: suweren, pierścienie, sektory, glify typów | jest (skórka D, jedyny widok projektu) |
| Relacje po wyborze węzła, z typami (elects, appoints, confirms, oversees…) | jest, plus polski typ „wnioskuje / wskazuje” |
| Strona organu: opis, Legal Source, Official Website, szef, „Who's connected?” | jest |
| Legenda encji i relacji, każda pozycja jako filtr (licznik ukrytych, „Show all”) | jest (skórka D; dodatkowo kluby i koła, klasy zbiorcze, wakat, p.o.) |
| Obrót grafu: wybrany węzeł staje na godz. 6 | jest (skórka D); napisy zostają czytelne po obrocie |
| Wachlarz podjednostek wybranego organu (mini-glify z kółkami szefów) | jest (skórka D); duże grona izb w kilku łukach grupami |
| Jasne wypełnienie węzłów łańcucha władzy, także pieczęci suwerena | jest (skórka D) |
| Wyszukiwarka po nazwie i aliasach | jest |
| Latest Changes: wakaty, acting officials, oś czasu | kafle są, brak danych o zmianach |
| Latest News ze streszczeniem i linkami do organów | świadomie pominięte (decyzja 17.09.2026) |
| Power map: kto jest w newsach (90 dni) | zastąpione **mapą władzy formalnej** (18.09.2026): ten sam układ dwudziestu osób z liniami powołań, ale liczony z relacji ustawowych grafu, bez mediów |
| Animacje sceny: obrót do godz. 6, rozsuwanie rzędu podjednostek, wzrost wybranego glifu | jest (zmierzone na oryginale klatka po klatce, testy `10-fan-animation`) |
| Rozmiar koła i układ boxu informacyjnego jak na stronie organu w oryginale | jest (testy `09-circle-size-and-panel`) |
| Widok „Budżet” jak w wersji SF: pierścień wydatków, zakładka w panelu | jest: budżet państwa według części, wykonanie 2025 i plan 2026 (testy `12-budget`); koło celowo się nie obraca |
| Cotygodniowa aktualizacja danych bez udziału człowieka | jest dla parlamentu; akty z Monitora Polskiego jako lista do przejrzenia (`.github/workflows/weekly-update.yml`) |
| Topics | częściowo: działy administracji przy ministrach |
| Budget, employee counts (SF) | brak, są seedy |
| Request access / API | brak; u nas ma być otwarte |

## Dla kogo
Dziennikarze i organizacje strażnicze. Urzędnicy i legislatorzy, którzy muszą wiedzieć, kto za co odpowiada.
Studenci i nauczyciele prawa oraz WOS. Obywatel, który chce sprawdzić, „kto to powołuje i kto tym kieruje”.

## Czego nie robimy (na teraz)
- Samorząd terytorialny: na razie poza zakresem. Projekt rozszerzenia jest w `07-projekt-samorzad.md` i czeka na decyzję właściciela; oświadczenia majątkowe zostają w osobnym, zaparkowanym projekcie.
- Oświadczenia majątkowe, powiązania biznesowe, dane prywatne.
- Oceny i werdykty. Pokazujemy dane z cytatem, także w sporach ustrojowych.
- **Newsy i media w jakiejkolwiek postaci** (decyzja właściciela z 17.09.2026): żadnej zakładki z aktualnościami, żadnego poboru RSS mediów ani Google News, żadnych streszczeń artykułów. Powód: projekt ma pokazywać ustrój z dokumentów urzędowych, a nie powielać przekaz mediów, zwłaszcza sensacyjnych i niskiej jakości.
- **Power map z oryginału w wersji newsowej**, bo jej jedynym sygnałem są wzmianki w mediach. Zbudowana jest za to wersja formalna: zasięg władzy z relacji ustawowych grafu (powołuje, wybiera, wnioskuje, zatwierdza, nadzoruje), opisana w README.
- Rankingi osób.
- Monetyzacja, konta użytkowników, aplikacja mobilna.

## Zasady
1. **Kopiujemy wiernie.** Decyzją właściciela z 17.09.2026 projekt ma jeden widok: skórkę D w stylu CivLab. Robocze pomysły (zwinięte koło, widok resortu, sunburst, pierwszy prototyp) leżą w `archive/skorki/` i nie są rozwijane.
2. **Dane, nie werdykt.**
3. **Każdy fakt ma źródło** i przeszedł weryfikację przez osobnego agenta.
4. **Tylko oficjalne API i serwisy dopuszczające roboty** (ELI, Sejm API, gov.pl, dane.gov.pl).
5. **Widok oddzielony od danych.** Widok czyta `window.GRAPH_DATA` albo `./graph.json`, wybór siedzi w `#node=<id>`, motyw w `gp-theme`. Dzięki temu ta sama skórka działa w prototypie (artefakt) i na stronie publicznej.

## Etapy
- **v0.1 (jest):** seed danych, widok w stylu CivLab, strona publiczna https://grafpanstwa.pl bez indeksowania (wdrożenie: `05-wdrozenie-grafpanstwa-pl.md`).
- **v0.2:** domknięcie luk seedu z plików `*.verdicts.json`, zgoda CivLab i włączenie indeksowania, repozytorium.
- **v1:** oś zmian z Monitora Polskiego, otwarte API, strona „O danych”, automatyczne odświeżanie.
- **v2:** budżet i etaty, tematy, uczelnie i instytuty (RAD-on), spółki Skarbu Państwa, sądy per jednostka.

## Kryterium sukcesu
Osoba, która zna graph.civlab.org/us, otwiera polską wersję i rozpoznaje ten sam produkt. Osoba, która go nie zna,
w 30 sekund odpowiada na pytanie „kto powołuje Prezesa NIK i kto nim dziś jest”.
