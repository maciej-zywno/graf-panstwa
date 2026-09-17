# Katalog zachowań oryginału: CivLab · US Gov Graph

Data obserwacji: **2026-09-17** · adres: https://graph.civlab.org/us · przeglądarka: Chrome (rozszerzenie Claude), okno 1468×836 CSS px, DPR 2.
Metoda: zwykłe oglądanie strony (najazd, klik, klawiatura), odczyt `location`, `document.title` i atrybutów DOM bez modyfikacji strony. Zrzuty: `tests/parity/shots/us-*.jpg`.

> Uwaga o motywie: przy pierwszym wejściu w tej sesji strona wystartowała w motywie **jasnym** (bez klucza `civlab-theme` w `localStorage`, system w trybie jasnym). Dokument `docs/01` i `intended-differences.md` pkt 9 mówią o starcie w ciemnym: dziś oryginał idzie za ustawieniem systemu.

## 0. Układ ekranu
- Lewa kolumna 582 px: pasek breadcrumb (`CivLab / US Gov ▾` + po wyborze `/ Executive`), pod nim karty. Cała strona przewija się jako dokument (scena jest przyklejona, przewija się tylko lewa kolumna).
- Scena: w lewym górnym rogu sceny ikona lupy, w prawym górnym przycisk motywu (księżyc/słońce) i para strzałek `‹ ›`, w lewym dolnym przycisk `Legend ▾`, w prawym dolnym przełącznik `Graph | Power map`. Brak przycisków zoomu.
- Stan spoczynku: widoczne etykiety pierścieni (`HIGHEST AUTHORITY`, `OVERSIGHT`, `ADMINISTRATION`, `CABINET`) i sektorów na łuku; żadnych linii relacji.

## 1. Najazd (hover)
| # | Wyzwalacz | Obserwowalny skutek | Zrzut |
|---|---|---|---|
| H1 | Najazd na glif organu (np. Department of Justice) | Glif wypełnia się pełnym kolorem sektora (fiolet), kółko szefa zostaje białe. Nad glifem pigułka z pełną nazwą: tło w kolorze sektora, biały tekst, bez strzałki. Żadnych linii, nic nie przygasa, panel i URL bez zmian. Kursor: rączka. | us-01 (stan po kliknięciu), opis z obserwacji zoom |
| H2 | Najazd na kółko szefa przy glifie | Wypełnia się tylko kółko; glif organu zostaje obrysem. Pigułka z nazwą STANOWISKA („Attorney General”), nie organu. | — |
| H3 | Najazd na kropkę podjednostki (sub-agency) | Pigułka z nazwą podjednostki ok. 25 px nad kropką; kropka podświetlona. | — |
| H4 | Najazd na rząd kwadracików (series) | Każdy kwadracik to osobny węzeł: wypełnia się tylko jeden kwadracik, pigułka z jego nazwą („U.S. Immigration and Customs Enforcement”). | — |
| H5 | Najazd na pojedynczą izbę w kapsule Kongresu | Wypełnia się tylko ta izba (czerwień), pigułka „United States House of Representatives”. | — |
| H6 | Najazd na kapsułę (przerwa między izbami / obrys) | Wypełnia się cała kapsuła, izby zostają białe; pigułka „Congress”; napis łukowy `CONGRESS` znika na czas najazdu. Najazd na sam napis `CONGRESS` nic nie robi. | — |
| H7 | Najazd na pieczęć suwerena | **Brak reakcji** (bez pigułki, bez wypełnienia). | — |
| H8 | Najazd na linię relacji (widoczną po wyborze węzła) | Na linii, w miejscu kursora, mała biała pigułka z czasownikiem małymi literami w kolorze linii: `appoints`, `confirms`. Linia się nie pogrubia, reszta nie przygasa. | — |
| H9 | Najazd na kartę w „Who's connected?” | Szare tło karty; brak widocznej zmiany na scenie. | — |

## 2. Klik
| # | Wyzwalacz | Obserwowalny skutek | Zrzut |
|---|---|---|---|
| K1 | Klik glifu organu (DOJ) | (a) cały graf **obraca się** ok. 1–2 s tak, by wybrany węzeł stanął na godz. 6; (b) glif wypełniony pełnym kolorem i lekko powiększony; (c) rysuje się **łańcuch władzy**: People → President (`elects`, pomarańcz, podwójny grot), President → Attorney General (`appoints`, fiolet, pełny grot), People → Senate (`elects`), Senate → Attorney General (`confirms`, czerwień, pusty grot); węzły łańcucha dostają jasne wypełnienie (także pieczęć suwerena i izba Senatu); (d) kropki podjednostek **rozwijają się w wachlarz mini-glifów** pod węzłem, połączonych przerywanymi liniami; (e) etykiety pierścieni znikają; (f) na dole sceny, pod węzłem, podpis z nazwą w kolorze sektora na białym tle; (g) reszta węzłów **nie przygasa**; (h) brak zoomu. Panel: tytuł, opis, linki `Legal Source` / `Official Website`, karta szefa (zdjęcie, „Appointed 2026”), zakładki `News` / `Who's connected?`. Breadcrumb: `CivLab / US Gov / Executive`. URL: `/us/departments/us-department-of-justice` (nowy wpis historii), `document.title` = „CivLab · Department of Justice”. | us-01-klik-doj.jpg |
| K2 | Klik drugiego węzła przy wybranym | Bezpośrednie przełączenie wyboru (bez stanu pośredniego), nowy obrót, nowy URL i wpis historii. Aktywna zakładka panelu (`Who's connected?`) zostaje zapamiętana między węzłami. | us-02-klik-hud-zakladka-connected.jpg |
| K3 | Klik węzła-huba (President) | Pęk linii `appoints` w pełnym, nasyconym fiolecie do wszystkich celów, cele z jasnym wypełnieniem; węzły niepowiązane zostają zwykłym obrysem. Panel: `Elected by` (People…), `Appoints — Appoints 881 seats`, karty z „1 of 1 seats”. | us-03-klik-prezydent-hub.jpg |
| K4 | Klik kapsuły Kongresu | Obrót o ok. 180° (kapsuła na godz. 6, napisy sektorów do góry nogami), kapsuła wypełniona, obie izby jasne; linie `appoints` do agencji legislatywy. Panel: „535 members · From the United States Senate (100) and the United States House of Representatives (435)”. | us-08-klik-kongres-obrot.jpg |
| K5 | Klik pojedynczej izby | Izba wypełniona mocno, kapsuła jasno; linia `elects` People → izba; Senat: pęk czerwonych linii `confirms`. Panel: `Part of: Congress`, `Members — 435 seats` z kartami osób. | — |
| K6 | Klik kółka szefa / wejście na `/us/dept-heads/us-attorney-general` | Wypełnione kółko, glif organu jasny; łańcuch do People; dodatkowo krótkie linie `appoints` do szefów podjednostek w wachlarzu i kropkowane `ex officio`. Panel: `Appoints 6 seats`, `Appointed by`, `Confirmed by`. | — |
| K7 | Klik pozycji listy „Who's connected?” (FBI) | Wybór tego węzła: URL `/us/departments/us-federal-bureau-of-investigation`, panel z kartą `Part of: Department of Justice`, na scenie wypełniony mini-glif w wachlarzu rodzica, rodzic jasny. Graf się nie obraca ponownie. | — |
| K8 | Klik w pustą część płyty | Odznaczenie: URL wraca do `/us` (nowy wpis historii), panel wraca do strony głównej (Latest News / Latest Changes), linie znikają, wracają etykiety pierścieni, po chwili graf obraca się do pozycji wyjściowej. | — |
| K9 | Klik w beżowe tło poza płytą | **Nic** (wybór zostaje). | — |
| K10 | Klik w linię relacji | **Nic** (wybór, panel i URL bez zmian). | — |
| K11 | Klik pieczęci suwerena | **Nic**: pieczęć nie jest klikalna (nie wybiera, nie odznacza). | — |
| K12 | Przeciągnięcie po scenie | Traktowane jak klik w pustą płytę (odznacza); brak przesuwania. | — |
| K13 | Kółko myszy nad sceną | Przewija stronę (lewą kolumnę); **brak zoomu** (`viewBox` stały `0 -25 800 840`). | — |
| K14 | Podwójny klik | Brak zoomu; działa jak dwa kliki. | — |

## 3. Legenda
- Otwarcie: przycisk `Legend ▾` → popover nad przyciskiem (strzałka obraca się w górę). Sekcje `ENTITIES` (Elected offices, Agencies & departments, Department heads, Commissions, Advisory bodies, Courts, Corporations, Quasi-official, Sub-agencies) i `RELATIONSHIPS` (Elects, Appoints, Confirms, Oversees, Administers, Advises, Heads, Offices, Ex officio). Zrzut: us-04-legenda-otwarta.jpg.
- **Pozycje legendy są przełącznikami-filtrami**: klik „Courts” wyszarza pozycję i ukrywa sądy na scenie; klik „Appoints” ukrywa linie tego typu. Na dole pojawia się `SHOW ALL`, a na zamkniętym przycisku licznik „Legend · 1 hidden”. Filtr przeżywa zmianę wyboru węzła.
- `Esc` **nie zamyka** legendy. Klik poza legendą (tło, płyta) **nie zamyka** legendy; zamyka ją tylko jej przycisk.
- Klik w pustą płytę przy otwartej legendzie: odznacza węzeł, legenda zostaje otwarta. Klik węzła przy otwartej legendzie: wybiera węzeł, legenda zostaje.

## 4. Wyszukiwarka
- Klik lupy: ikona rozwija się w pole na całą szerokość sceny (placeholder „Search”), po prawej `×`; przyciski motywu i strzałek znikają pod polem.
- Wpisanie „justice”: spinner po prawej, po odpowiedzi serwera panel wyników pod polem, nagłówek `Entities`, 8 wierszy z kwadracikiem w kolorze sektora (Department of Justice, State Justice Institute, Bureau of Justice Assistance…); reszta strony rozmyta i przygaszona. Zrzut: us-05-szukaj-justice.jpg. (W tej sesji wyniki pojawiały się dopiero po prawdziwym zdarzeniu klawisza; przy wklejeniu tekstu spinner kręcił się bez końca.)
- Klawiatura: strzałki ↑/↓ **nic nie robią**, `Enter` w polu **nic nie robi**; `Tab` przechodzi na `×`, potem na kolejne wyniki (to linki `<a>`, widoczny pierścień fokusu), `Enter` na linku wybiera węzeł. `Esc` zamyka wyszukiwarkę i czyści pole.
- Klik wyniku: wybór węzła (URL, panel, obrót), wyszukiwarka się zwija.

## 5. Nawigacja i adresy
- Każdy wybór i każde odznaczenie to osobny wpis historii. Przeglądarkowe Wstecz/Dalej odtwarzają wybór, panel i tytuł karty (sprawdzone: HUD → President → `/us` → President).
- Wejście z linku (`/us/commissions/us-federal-communications-commission`): od razu wybrany węzeł, obrócony graf, łańcuch linii, breadcrumb `/ Independent`. Zrzut: us-06-link-fcc-jasny.jpg.
- Strzałki `‹ ›` w prawym górnym rogu to **poprzedni / następny węzeł w kolejności grafu** (President → `‹` Senate, `›` Vice President), nie historia przeglądania.
- Breadcrumb: `CivLab / US Gov ▾ / <sektor>`; człon sektora pojawia się tylko przy wybranym węźle.

## 6. Motyw
- Przycisk księżyc/słońce: natychmiastowa zmiana, `html[data-theme="dark"]`, zapis w `localStorage["civlab-theme"]`. Wybór węzła i linie zostają. W ciemnym płyty sektorów są ciemnofioletowe/oliwkowe/bordowe, linie i pigułki jaśnieją. Zrzut: us-07-fcc-ciemny.jpg.

## 6a. Stany szczególne zaobserwowane z linku
- **Pełniący obowiązki** (`/us/departments/us-government-accountability-office`): etykieta karty szefa zmienia się na „Acting Comptroller General of the United States”, pod nazwiskiem „Acting since 2025” (zamiast „Appointed <rok>”). Graf obrócony o ok. 180°, łańcuch People → President (`elects`) → szef GAO (`appoints`) oraz People → Senate. Zrzut: us-09-gao-acting.jpg.
- **Nieistniejący adres węzła** (`/us/departments/us-supreme-court-of-the-united-states`): strona „404: Page not found · Go back to the homepage or contact us”, tytuł karty „CivLab · 404”. (Usterka oryginału: w tle 404 rysuje się graf SF, breadcrumb „SF Gov / 404”.)

## 7. Pozostałe
- Przełącznik `Graph | Power map` istnieje (Power map: siatka awatarów z liczbą artykułów i liniami powołań). Nie testowano dalej.
- Okno 390 px: **pominięto**. `resize_window` rozszerzenia nie zmienia szerokości widoku w tej sesji (`innerWidth` zostaje 1468).
- Konsola: brak błędów w trakcie sesji.

## 8. Czego NIE udało się zaobserwować (braki tego katalogu)
> Uzupełnienie z drugiego przebiegu (2026-09-17, §9): Supreme Court, ciało doradcze, wakat, korporacja, kolejność `Tab`, klik wiersza listy i pamięć zakładki zostały zaobserwowane, ale wyłącznie w układzie 500 px. Nadal brak: te same węzły w układzie desktopowym, okno 390 px.
- W połowie sesji okno Chrome z kartą testową przeszło w stan `visibilityState = "hidden"` (`outerWidth/outerHeight = 0`). Od tej chwili do strony docierał tylko ruch myszy; **kliknięcia i klawisze nie były dostarczane** (sprawdzone nasłuchem zdarzeń na lokalnej kopii PL). Wszystko w sekcjach 1–6 zebrano PRZED tą zmianą, prawdziwą myszą i klawiaturą; sekcję 6a zebrano po niej, samą nawigacją po adresach.
- Nie zaobserwowano: Supreme Court, ciało doradcze, wakat („Seats vacant”), korporacja rządowa (Amtrak/USPS), zachowanie `Esc` przy samym wybranym węźle bez legendy (przy otwartej legendzie `Esc` nie zmienił ani legendy, ani wyboru), fokus `Tab` po scenie, okno 390 px.
- Kółko myszy: narzędzie nie zmieniło ani `scrollY`, ani `viewBox`; wniosek „brak zoomu” opiera się na stałym `viewBox`, braku przycisków zoomu i braku reakcji na podwójny klik i przeciąganie.
- Jedno kliknięcie kapsuły Kongresu zaraz po załadowaniu strony nie zadziałało (drugie zadziałało); to samo zdarzyło się po stronie PL, więc traktuję to jako artefakt narzędzia, nie zachowanie strony.

## 9. Uzupełnienie z drugiego przebiegu (2026-09-17, układ 500 px)
Warunki: Chrome (rozszerzenie Claude), widok **500×757 CSS px**, `visibilityState="hidden"` (okno odziedziczone po pierwszym przebiegu; rozmiaru nie zmieniano). Kliknięcia, najazd i klawisze docierały jako zdarzenia zaufane; `wheel` nie docierał. Animacja obrotu jest sterowana klatkami (`requestAnimationFrame`): w ukrytym oknie posuwa się tylko przy wymuszonej klatce (zrzut ekranu), linie rysują się od razu w układzie docelowym, a glify dochodzą dopiero po kilku klatkach. Zrzuty: `shots/v2-us-*.jpg`.

### 9.1 Układ wąski (500 px)
- `viewBox="0 125 500 550"`: scena pokazuje dolną połowę płyty, pieczęć suwerena u góry; po wyborze graf obraca się tak samo (węzeł na godz. 6) i to obrót sprowadza węzeł do widocznej części.
- U góry pasek `CivLab / US Gov ▾ / <sektor>`, przycisk motywu i lupa; pod sceną `Legend ▾`, `Graph ▾` (lista rozwijana zamiast przełącznika `Graph | Power map`) i `‹ ›`; niżej treść panelu. Cała strona przewija się jako dokument; klik zakładki `Who's connected?` przewija stronę do listy (scrollY ≈ 360–650), klik pozycji listy wraca na górę (scrollY = 0).
- Pigułki długich nazw są ucinane przez krawędzie ekranu („…States Court of Appeals for the Federal Circuit”, „…ostal Service Board of Contract Appeal…”). Po przejściu między węzłami w lewym górnym rogu zostaje osierocony dymek `appoints` (usterka oryginału).

### 9.2 Pary zaobserwowane
| Węzeł | Adres | Scena po kliknięciu | Panel |
|---|---|---|---|
| Supreme Court of the United States | `/us/departments/us-the-supreme-court-of-the-united-states` (segment `departments`, nie `courts`) | Pięciokąt wypełniony ciemnym złotem, kółko szefa jasne; łańcuch People → President (`elects`) → Supreme Court (`appoints`), People → Senate (`elects`) → Supreme Court (`confirms`, pusty grot); trzy złote łuki `oversees` do sądów apelacyjnych; kropki podjednostek rozwinięte w wachlarz; podpis na dole w kolorze sektora; breadcrumb `/ Judicial` | Karta szefa „Chief Justice of the United States · John G. Roberts, Jr. · Appointed 2005”; `Who's connected?`: `Appointed by — 9 seats` (President, „9 of 9 seats”), `Oversees` ×3, `Confirmed by` (Senate) |
| Council of Economic Advisers (ciało doradcze) | `/us/advisories/us-council-of-economic-advisers` | Wypełniony kwadracik w wachlarzu podjednostek Executive Office of the President (rodzic jasny, przerywane linie wachlarza); łańcuch przez President i Senate | „3 members”, `Part of: Executive Office of the President`; `Who's connected?`: `Appointed by — 3 seats`, `Advises` (President), `Confirmed by` (Senate); `News`: „No recent news” |
| Director of the Women's Bureau (wakat, z wpisu `DEPARTURE · Sep 16 · IN: Seat now vacant` w Latest Changes) | `/us/dept-heads/us-director-of-the-womens-bureau` | Mała wypełniona kropka szefa przy kwadraciku w wachlarzu Department of Labor; łańcuch People → President (`appoints`) i People → Senate (`confirms`) | **Pusta karta z samą nazwą stanowiska**: bez zdjęcia, nazwiska i bez słowa „Vacant”; `Appointed by — 1 seat`, `Confirmed by`. Kafel `SEATS VACANT 6` na stronie głównej nie jest klikalny (brak listy wakatów) |
| United States Postal Service (korporacja) | `/us/departments/us-united-states-postal-service` | Zwykły glif z kółkiem szefa; krótka pętla `appoints` od glifu do własnego kółka szefa (organ powołuje swojego szefa); jedna podjednostka w wachlarzu; łańcuch przez President i Senate; breadcrumb `/ Executive` | Karta „Postmaster General · David Steiner · Appointed 2025” |

### 9.3 Linie
- Każda linia ma niewidoczne pole trafienia: drugi `path` o szerokości 10 px i przezroczystym obrysie nad widoczną linią 1 px. Najazd pokazuje biały dymek z czasownikiem (`appoints`, `oversees`); klik w linię nic nie robi (potwierdzone na `oversees` przy Supreme Court).
- **Dwie relacje tej samej pary leżą dokładnie na sobie** (Council of Economic Advisers ↔ President: `appoints` w dół i `advises` w górę, ta sama prosta, 426 jednostek). Najazd w każdym punkcie daje `appoints`; relacji `advises` nie da się odczytać ze sceny (usterka oryginału).

### 9.4 Lista powiązań i zakładki
- Klik pozycji `Who's connected?` („United States Courts of Appeals” przy Supreme Court) wybiera ten węzeł: nowy adres, tytuł karty i wpis historii; fokus spada na `BODY`.
- Aktywna zakładka (`Who's connected?`) zostaje po przejściu między węzłami w ramach sesji; po pełnym przeładowaniu strony wraca `News`.
- Klik w pustą płytę: odznaczenie, adres `/us`, nowy wpis historii, graf wraca do pozycji wyjściowej (potwierdzone w 500 px).

### 9.5 Klawiatura: kolejność `Tab` (prawdziwa klawiatura, strona główna)
- Scena jest **niedostępna z klawiatury**: w `svg.gov-graph` nie ma ani jednego elementu z `tabindex`, SVG nie ma `role` ani `aria-label`.
- 33 przystanki w kolejności DOM: linki w „Latest News” (encje i artykuły) → `Show more` → `Who's in the news / Power map` → `7D`, `30D`, `90D` → pozycje „Latest Changes” (`div[role=link]` + link daty) → `Show all 20 changes` → stopka (CivLab, Email, Twitter, Substack) → logo CivLab → `Switch government graph` → `Switch to dark mode` → lupa (bez etykiety) → `Graph` (combobox) → `‹`, `›` (bez etykiet). Potem pętla od początku.
- Fokus jest widoczny jako domyślny obrys przeglądarki (`outline: auto 1px`, przy linkach artykułów 3 px); bez obrysu (`outline-style: none`) są trzy przyciski: `Who's in the news / Power map`, `Switch government graph` i `Graph`.

### 9.6 Wyszukiwarka (uzupełnienie)
- Wyniki mają znacznik typu: fioletowy kwadracik dla urzędów i stanowisk, różowy sześciokąt albo kółko dla ciał doradczych i quasi-sądowych. Zapytanie z apostrofem („women's bureau”) kręciło spinnerem ponad 5 s bez wyników; „womens” zwróciło 4 wyniki (Women's Bureau, Domestic Policy Council, FDA Office of Women's Health, Director of the Women's Bureau). Wyniki pojawiają się dopiero po prawdziwym zdarzeniu klawisza (potwierdzenie obserwacji z §4).
