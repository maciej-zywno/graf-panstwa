# Rejestr źródeł danych — Graf Państwa Polskiego

Stan na 2026-09-17. Ten dokument mówi, **skąd pochodzi każdy rodzaj danych w `data/pl/graph.json`**, jak został pobrany
i na jakich warunkach wolno go używać. Uzupełnia `02-mapa-zrodel-i-ryzyk.md` (tam: przegląd wszystkich możliwych źródeł
i ryzyk prawnych) i `03-projekt-graf-panstwa.md` (tam: model danych).

Zasady, które obowiązują przy każdym źródle:
1. **Tylko źródła urzędowe.** Wikipedia i Wikidata służyły wyłącznie jako wskazówka, nigdy jako źródło wpisu.
2. **Każdy fakt niesie swoje źródło w danych**: `provenance.sources[]` na węźle i relacji, `sourceUrl` przy każdej osobie,
   `startedAtSource` przy każdej dacie objęcia funkcji, `legalSource.url` i `citeUrl` przy przepisach.
3. **Przepisy tylko z ELI.** Permalink `https://eli.gov.pl/eli/{DU|MP}/{rok}/{poz}/ogl` aktu bazowego, numer artykułu w osobnym
   polu. Tytuł aktu sprawdzany w API ELI, treść artykułu czytana z PDF (`pdftotext`).
4. **Tylko API i serwisy, które dopuszczają roboty.** `www.sejm.gov.pl`, `orka.sejm.gov.pl` i `monitorpolski.gov.pl` mają
   `Disallow: /`, więc nie są scrapowane; zamiast nich API Sejmu i ELI. `senat.gov.pl` dopuszcza strony, wyklucza `/gfx/`
   (dlatego nie ma zdjęć senatorów). `gov.pl` ma `Allow: /`.

## 1. Źródła według warstwy danych

| Warstwa | Źródło | Adres | Format | Warunki użycia | Jak pobierane |
|---|---|---|---|---|---|
| Podstawy prawne i cytaty przepisów | ELI API Kancelarii Sejmu (Dziennik Ustaw, Monitor Polski) | `https://api.sejm.gov.pl/eli/acts/{DU|MP}/{rok}/{poz}` + `/text.pdf`; permalinki `eli.gov.pl` | JSON + PDF | akty normatywne nie są przedmiotem prawa autorskiego (art. 4 pr. aut.); API bez klucza i bez regulaminu | agenci (budowa) + skrypty (weryfikacja tytułów) |
| Sejm: posłowie, komisje, kluby, funkcje, zdjęcia | API Sejmu | `https://api.sejm.gov.pl/sejm/term10/{MP,committees,clubs,clubs/<id>/members}` | JSON | warunki Systemu Informacyjnego Sejmu: bezpłatnie, z podaniem źródła | **skrypt** `scripts/build-parliament-chunk.py` |
| Senat: komisje, składy, kluby i koła, prezydium | serwis Senatu | `https://www.senat.gov.pl/prace/komisje-senackie/`, `…/sklad,<id>,….html`, `/sklad/kluby-i-kola/`, `/sklad/senatorowie/prezydium.html` | HTML | informacja publiczna; robots dopuszcza strony, wyklucza `/gfx/` | **skrypt** (parser HTML) + agent (prezydium) |
| Rada Ministrów, ministrowie, wiceministrowie, dyrektorzy generalni | serwis gov.pl (KPRM i resorty) | `https://www.gov.pl/web/premier/sklad-rady-ministrow`, strony „Kierownictwo” resortów | HTML | teksty CC BY-SA 4.0, zdjęcia CC BY-NC-ND 4.0 | agenci |
| Daty powołań członków RM, wyboru marszałków, sędziów TK, członków KRS, RPO | Monitor Polski przez ELI | postanowienia Prezydenta RP „o zmianie w składzie Rady Ministrów”, uchwały Sejmu i Senatu | PDF | jak akty urzędowe | agenci (`pdftotext`) |
| Organy podległe i nadzorowane przez ministrów | rozporządzenia PRM o zakresie działania ministrów (Dz.U. 2025 poz. 993–1005 i starsze), obwieszczenia ministrów o wykazach jednostek (M.P.) | ELI | PDF | jak wyżej | agenci |
| Jednostki nadzorowane przez Prezesa RM | KPRM + ustawa o działach art. 33a | `https://www.gov.pl/web/premier/jednostki-i-organy-nadzorowane-przez-prezesa-rady-ministrow` | HTML | CC BY-SA 4.0 | agenci |
| Ciała doradcze RM i PRM, komisje wspólne | rejestry BIP KPRM + akty w M.P. | `https://www.gov.pl/web/premier/organy-pomocnicze-rady-ministrow2` i pokrewne | HTML + PDF | CC BY-SA 4.0 | agenci |
| Prezydent, Kancelaria Prezydenta, BBN, rady przy Prezydencie | prezydent.pl | `https://www.prezydent.pl/kancelaria/kierownictwo-kancelarii` i pokrewne | HTML | teksty do ponownego użycia z podaniem źródła; zdjęcia tylko ilustracyjnie | agenci |
| Sądy i trybunały, KRS, prokuratura | sn.pl, nsa.gov.pl, trybunal.gov.pl, krs.pl, BIP-y 16 WSA, gov.pl/web/prokuratura-krajowa | strony „organizacja”, „sędziowie”, „skład” | HTML | informacja publiczna | agenci |
| Organy niezależne i kontrolne | nik.gov.pl, bip.brpo.gov.pl, gov.pl/web/krrit, pkw.gov.pl, uodo.gov.pl, ipn.gov.pl, pip.gov.pl, uke.gov.pl, pkdp.gov.pl | strony „kierownictwo”, „skład” | HTML | informacja publiczna | agenci |
| NBP (Prezes, Zarząd, RPP) | Monitor Polski przez ELI | uchwały Sejmu i Senatu, postanowienia Prezydenta | PDF | jak akty urzędowe | agenci; `nbp.pl` blokuje automaty, więc pewność „średnia” |
| Wojewodowie, wicewojewodowie, urzędy wojewódzkie | gov.pl/web/mswia/urzedy-wojewodzkie + strony 16 urzędów | HTML | CC BY-SA 4.0 | agenci |
| Części budżetowe (`budgetPart`) | rozporządzenie MF o klasyfikacji części budżetowych (Dz.U. 2025 poz. 1185) | ELI | PDF | jak akty | agenci (tylko część węzłów) |
| Etaty (jeszcze nieużyte w grafie) | wystąpienia pokontrolne NIK P/26/001, arkusze sprawozdania z wykonania budżetu (dane.gov.pl, zbiór 163, CC0), arkusze Fundacji Sprawne Państwo | `seeds/employee-count/` | CSV | CC0 / informacja publiczna / licencja nieokreślona (Sprawne Państwo) | skrypty w rundzie badawczej |

## 2. Źródła według chunku (policzone z danych)

Liczby w kolumnie „Najczęstsze hosty” to liczba odwołań w `provenance.sources` i `sourceUrl`.

| Chunk | Węzły | Relacje | Osoby | Akty prawne | Najczęstsze hosty | Sposób budowy |
|---|---|---|---|---|---|---|
| `konstytucyjne` | 24 | 50 | 42 | 7 | eli.gov.pl 42, gov.pl 25, prezydent.pl 19, senat.gov.pl 10, sejm.gov.pl 8 | agent + agent-weryfikator |
| `ministerstwa-G1` (MON, MSZ, MC) | 39 | 72 | 31 | 17 | eli.gov.pl 85, gov.pl 43, wojsko-polskie.pl 10 | agent + weryfikator |
| `ministerstwa-G2` (MSWiA, MS) | 37 | 70 | 57 | 16 | gov.pl 85, eli.gov.pl 43, policja, straż graniczna, sw.gov.pl | agent + weryfikator |
| `ministerstwa-G3` (MF, MRiT, MAP, MFiPR, MI, ME) | 72 | 122 | 28 | 37 | eli.gov.pl 110, gov.pl 68 | agent + weryfikator |
| `ministerstwa-G4` (MZ, MRPiPS, MEN, MNiSW, MKiDN) | 80 | 127 | 62 | 37 | eli.gov.pl 105, gov.pl 72, zus.pl, nfz.gov.pl | agent + weryfikator |
| `ministerstwa-G5` (MRiRW, MKiŚ, MSiT) | 51 | 92 | 21 | 26 | eli.gov.pl 69, gov.pl 57 | agent + weryfikator |
| `urzedy-prm` | 48 | 85 | 37 | 23 | eli.gov.pl 51, gov.pl 37, knf.gov.pl 17 | agent + weryfikator |
| `ciala-doradcze` | 33 | 100 | 8 | 26 | eli.gov.pl 40, gov.pl 39, prezydent.pl 9 | agent + weryfikator |
| `sadownictwo` | 43 | 81 | 86 | 6 | eli.gov.pl 91, krs.pl 28, nsa.gov.pl 27, sn.pl 15, trybunal.gov.pl 12 | agent + weryfikator |
| `niezalezne` | 31 | 81 | 93 | 13 | eli.gov.pl 106, nik.gov.pl 23, ipn.gov.pl 17, pkw.gov.pl 15 | agent + weryfikator |
| `wojewodowie` | 33 | 128 | 63 | 1 | gov.pl 137, eli.gov.pl 65, strony urzędów wojewódzkich | agent + weryfikator |
| **`parlament`** | **81** | **82** | **346** | **4** | **api.sejm.gov.pl 320, senat.gov.pl 133** | **skrypt deterministyczny + drugi przebieg pobrań** |

Po scaleniu (`scripts/merge-chunks.py`, z usunięciem duplikatów): 570 węzłów, 1111 relacji, 889 osób.

## 3. Chunk „parlament” szczegółowo (dodany 2026-09-17)

**Zakres:** Prezydium Sejmu i Senatu, Konwent Seniorów Sejmu i Senatu, 40 komisji sejmowych X kadencji (31 stałych,
6 nadzwyczajnych, 3 śledcze), 20 komisji stałych Senatu XI kadencji, 11 klubów i kół poselskich, 6 klubów i kół w Senacie.

**Podstawy prawne (tytuły sprawdzone w ELI, artykuły odczytane z tekstu):**
- Konstytucja RP (Dz.U. 1997 nr 78 poz. 483): art. 110 ust. 1 (wybór Marszałka i wicemarszałków), art. 110 ust. 3 (komisje stałe
  i nadzwyczajne), art. 111 (komisja śledcza), art. 124 (odpowiednie stosowanie do Senatu).
- Regulamin Sejmu (M.P. 1992 nr 26 poz. 185; t.j. M.P. 2026 poz. 573): art. 8 (kluby co najmniej 15 posłów, koła co najmniej 3),
  art. 9 (organy Sejmu), art. 11–13 (Prezydium), art. 14–16 (Konwent Seniorów), art. 17–20 (komisje).
- Regulamin Senatu (M.P. 1991 nr 2 poz. 11; t.j. M.P. 2025 poz. 1251): art. 4 (organy Senatu), art. 5 i 9 (Prezydium), art. 13 i 15
  (komisje), art. 16 (Konwent Seniorów), art. 21 (kluby co najmniej 7 senatorów, koła co najmniej 3).
- Ustawa z 9.05.1996 r. o wykonywaniu mandatu posła i senatora (Dz.U. 1996 nr 73 poz. 350), art. 17 (kluby, koła, zespoły).
- Ustawa z 21.01.1999 r. o sejmowej komisji śledczej (Dz.U. 1999 nr 35 poz. 321).

**Co bierzemy z którego pola:**
- `committees`: `code` (skrót, np. FPB), `name`, `type` (STANDING / EXTRAORDINARY / INVESTIGATIVE), `appointmentDate`, `scope`,
  `members[]` z `function`; liczba członków to `seatsCount`, osoby z funkcją to `people[]`.
- `clubs` + `clubs/<id>/members`: `membersCount`, `functions[]` z `functionType` (chairman, vice_chairman), `appointmentDate`
  i `dismissalDate`. **To jedyne miejsce, gdzie data objęcia funkcji jest polem danych**, więc `startedAt` przewodniczących klubów jest pewne.
- `MP`: pełne imiona i nazwiska, zdjęcia (`/MP/{id}/photo`).
- Senat: lista komisji, strona składu (nazwisko, „Od:”, opis funkcji pisany swobodnie, np. „od 4 grudnia 2024 r. - przewodniczący”),
  strona klubów (liczebność, członkowie z funkcją i okresem członkostwa).

**Decyzje modelowe:**
- Komisje to `type: commission`, `subtype: committee`; prezydia i konwenty to `commission / council`.
- Kluby i koła to **nowy typ `political_group`** (podtypy `parliamentary_club`, `parliamentary_circle`), bo są strukturą polityczną,
  a nie organem państwa. W Sejmie klub od 15 posłów, w Senacie klub według nazwy urzędowej (kluby parlamentarne wspólne z posłami
  mogą mieć w Senacie mniej niż 7 osób).
- Relacja klub → Konwent Seniorów (`ex_officio`) tylko tam, gdzie wynika to wprost z regulaminu: kluby poselskie oraz kluby w Senacie
  z co najmniej 7 senatorami. Koła nie mają tej relacji, bo ich udział zależy od warunków, których dane nie rozstrzygają.
- Nazwy komisji mają dopisek „(Sejm)” albo „(Senat)”, bo obie izby mają komisje o tych samych nazwach; nazwa urzędowa jest w `aliases`.

**Czego nie ma i dlaczego:** pełnych składów komisji (tylko liczba i prezydium komisji), podkomisji, zespołów parlamentarnych,
posłów i senatorów niezrzeszonych, imiennego składu konwentów (niepublikowany), dat objęcia funkcji w komisjach sejmowych
(API podaje tylko datę wejścia do komisji), zdjęć senatorów (robots Senatu). Komisja Obrony Narodowej Senatu nie ma
wskazanego przewodniczącego na stronie składu; zapisane jako nota, nie jako błąd.

**Weryfikacja:** `python3 scripts/build-parliament-chunk.py --verify` pobiera źródła drugi raz i sprawdza każde nazwisko
przy funkcji (dla aktów M.P. czyta treść PDF, bo nazwiska są tam odmienione). Wynik z 2026-09-17: 346 z 346 potwierdzonych.

**Odświeżanie:** to samo polecenie bez `--verify`, potem `python3 scripts/merge-chunks.py`. Składy komisji i władze klubów
zmieniają się w trakcie kadencji, więc chunk warto przebudowywać co tydzień.

## 4. Czego świadomie nie używamy
- Wikipedia i Wikidata jako źródło wpisu (Wikidata bywa nieaktualna: Marszałek Senatu, część ministrów).
- Serwisy komercyjne i agregatory (Rejestr.io, MGBI).
- Pełne teksty prasy (prawo pokrewne wydawców); dla przyszłej warstwy newsów tylko tytuł, link, data i źródło.
- Dane CivLab nie są źródłem żadnego wpisu w polskim grafie. Publiczna strona ich projektu posłużyła wyłącznie do analizy modelu danych i wyglądu.
