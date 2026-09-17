# Graf Państwa Polskiego — projekt (v0.1, 2026-09-17)

Polski odpowiednik [CivLab · US Gov Graph](https://graph.civlab.org/us). Dokumenty towarzyszące:
`01-analiza-civlab-us-gov-graph.md` (co dokładnie kopiujemy), `02-mapa-zrodel-i-ryzyk.md` (282 zweryfikowane
ustalenia o polskich źródłach, prawie i ryzykach — referencja), ten plik = synteza i decyzje.

## 1. Cel i teza

**Produkt:** kompletny, otwarty model danych polskiego państwa na szczeblu centralnym — *organ ⟂ stanowisko ⟂ osoba*
+ typowane relacje prawne (*powołuje / zatwierdza / wybiera / wnioskuje / nadzoruje / zasiada z urzędu*), każdy węzeł
z podstawą prawną (ELI), każda krawędź z cytatem przepisu — plus warstwy dynamiczne: oś czasu zmian personalnych
(z Monitora Polskiego).

> **Decyzja właściciela z 17.09.2026: bez newsów.** Projekt nie pobiera, nie przechowuje i nie pokazuje treści mediów (RSS redakcji, Google News, streszczenia artykułów), a power map z oryginału, liczona ze wzmianek w mediach, wypada z zakresu. Warstwa dynamiczna opiera się wyłącznie na dokumentach urzędowych: Monitor Polski i Dziennik Ustaw przez ELI, API Sejmu, strony „kierownictwo” urzędów. Fragmenty tego dokumentu o newsach (tabela źródeł, punkt 3 potoku, decyzja prawna nr 5) zostają jako zapis analizy i są **wycofane z planu**.

**Teza:** w Polsce nikt tego nie ma. Werdykt prior art (doc 02): ani NGO (Stowarzyszenie 61, ePaństwo, Watchdog,
Batory, KJ, ISP), ani administracja, ani nauka nie utrzymują otwartego, maszynowego grafu organ→stanowisko→osoba→relacja
dla szczebla centralnego. Państwo ma tylko fragmenty (BIP dump 13 306 podmiotów z dziurawą hierarchią, HTML-owe katalogi
gov.pl, obwieszczenia w M.P., Sejm API). Wikidata ma stanowiska (333) i piastunów (120 aktualnych), ale nie relacje.

**Dlaczego wykonalne teraz:** CivLab zbudował graf USA (952 węzły, 1430 krawędzi) w ~2 tygodnie agentami LLM w falach
(doc 01 §4). My mamy lepsze prymitywy niż oni: ELI API z pełnym Dziennikiem Ustaw i Monitorem Polskim (stabilne
permalinki + JSON + PDF), Sejm API, gov.pl na CC BY-SA 4.0, dane.gov.pl (CC0/CC BY) z budżetem per część.

## 2. Co kopiujemy, co robimy inaczej

| Element | CivLab US | Graf Państwa PL (decyzja) |
|---|---|---|
| Model | organizacja ⟂ stanowisko (`dept_head`) ⟂ osoba; krawędzie typowane; `sector` + pierścienie | **to samo** (schemat kompatybilny, `pl-` ID) |
| Podstawa prawna | `legalSourceUrl` (43% pokrycia, uscode.house.gov) | `legalSource {title, url, act, article}` — **cel 100%**, permalink ELI aktu bazowego + numer artykułu osobno (ELI nie ma kotwic do artykułów) |
| Krawędzie | 9 typów, `cite` na 27% | **10 typów** (+ `nominates` = wnioskuje/wskazuje — w PL kluczowe: PRM→minister, KRS→sędzia, Prezydent→Prezes NBP), `cite` + `citeUrl` obowiązkowe dla relacji władczych, flaga `disputed` |
| Osoby | name, startedAt, acting, party, imageUrl | + `sourceUrl` (obowiązkowy), `startedAtSource`, `status` (verified/unverified/acting/disputed), `verdict` z weryfikacji |
| Etaty | brak w US (są w SF) | `employeeCount {value, unit, measure, asOf, scope, source, confidence}` — 3 źródła o różnym zakresie (§5) |
| Budżet | kody departamentów (SF) | `budgetPart` = część budżetowa (rozp. MF Dz.U. 2025 poz. 1185) + kwoty z arkuszy sprawozdania z wykonania budżetu (CC0) |
| Tematy | LLM-tagging (SF) | **37 działów administracji rządowej** (art. 5 ustawy o działach) = gotowa, ustawowa taksonomia tematów; `topics[]` na pozycji ministra z rozporządzenia atrybucyjnego |
| Oś zmian | „agents monitor official sources" | parser postanowień Prezydenta/uchwał Sejmu w **M.P. przez ELI** (`/acts/search`, `/changes/acts?since=`) + newsy resortów + diff stron „kierownictwo" |
| Newsy / power map | 3 źródła, NER nazwisk, LLM-streszczenia | RSS Sejmu (11 kanałów) + ~12 RSS mediów + Google News RSS; **przechowujemy tylko tytuł+link+data+źródło** (prawo pokrewne wydawców, art. 99⁷ pr. aut.) |
| Kod/dane | zamknięte (prywatne repo, API z kluczem) | **otwarte**: JSON/CSV dump + publiczne read-API, licencja CC BY 4.0 dla naszych danych |
| Spory ustrojowe | n/d | pole `status: disputed` + `statusNote` z cytatem (TK, KRS, CBA, IPN) — **dane, nie werdykt** |

## 3. Model danych

### 3.1 Węzły — taksonomia PL → sektor / pierścień

| Typ PL | `type` / `subtype` | `sector` | `ring` | podstawa (przykład) |
|---|---|---|---|---|
| Naród (suweren) | constituency | — | sovereign | Konst. art. 4 |
| Sejm, Senat | elected / chamber | legislative | highest | art. 95–124 |
| Prezydent RP | elected | executive | highest | rozdz. V |
| Rada Ministrów, Prezes RM | department/council + dept_head | executive | highest | art. 146–162 |
| Ministerstwa + ministrowie | department/ministry + dept_head | executive | cabinet | art. 149; rozp. RM (art. 39 uRM); rozp. atrybucyjne PRM |
| KPRM, Kancelarie (Sejmu, Senatu, Prezydenta) | department/chancellery | wg organu | cabinet / satellite | uRM art. 26–31 |
| Urzędy centralne podległe PRM (GUS, UOKiK, URE, ABW, AW, CBA, PKN, Prokuratoria + lista KPRM 23) | department/central_office, service | executive | administration | ustawa o działach art. 33a |
| Urzędy centralne / inspekcje / służby podległe ministrom | department/central_office, inspection, service, military | executive | **satellite** (parent = ministerstwo) | załącznik rozp. atrybucyjnego + obwieszczenie M.P. (art. 33 ust. 1d uRM) |
| Agencje wykonawcze, IGB, fundusze celowe, państwowe osoby prawne (ZUS, KRUS, NFZ, PFRON, NFOŚiGW, PAN…) | executive_agency / state_fund / state_legal_person | executive | satellite | ufp art. 9, 18, 23, 29 |
| Wojewodowie (16) + urzędy wojewódzkie | dept_head/voivode + department | executive | administration | ustawa o wojewodzie art. 3, 6 |
| Sądy i trybunały (SN, NSA, TK, TS, WSA, klasy sądów powszechnych) | department/court, tribunal | judicial | highest / administration | rozdz. VIII |
| KRS | commission/council | judicial | oversight | art. 186–187 |
| Organy kontroli i ochrony prawa (NIK, RPO, KRRiT) | oversight_body / regulatory_body | independent | oversight | rozdz. IX |
| Niezależne powoływane przez Sejm (NBP, PKW, UODO, IPN, UKE, PIP, RPD) | wg typu | independent | oversight | ustawy szczególne |
| Regulatorzy pod PRM (KNF) | commission/regulatory_body | independent | oversight | ustawa o nadzorze nad rynkiem fin. |
| Ciała doradcze (komitety RM, SKRM, RDS, KWRiST, Rada Legislacyjna…) | advisory | executive | oversight / satellite | zarządzenia PRM w M.P., ustawy |
| Spółki SP (klasa + strategiczne) | government_corporation | executive | satellite | uzzmp art. 7–8; rozp. RM Dz.U. 2026 poz. 987 |
| Prokuratura (PG = MS ex officio, PK) | department/other | executive | administration | Prawo o prokuraturze |

Reguły: stanowisko szefa = osobny węzeł `dept_head` (`headOf` ↔ `head`); ring stanowiska = ring organu; każdy węzeł
z `parent` jest satelitą rysowanym przy rodzicu (jak sub-agencies w CivLab). ID: `pl-` + ASCII slug nazwy urzędu /
tytułu stanowiska / imię-nazwisko (`data/pl/ids-canon.json` = kanon współdzielonych ID).

### 3.2 Krawędzie (from → to) z typowymi cytatami

| typ | znaczenie | przykłady (cite) |
|---|---|---|
| `elects` | wybiera | Naród→Sejm (art. 96), Sejm→sędzia TK (art. 194), Sejm→członkowie KRS (art. 187 + art. 9a uKRS, **disputed**), Sejm→Marszałek |
| `appoints` | powołuje | Prezydent→PRM/ministrowie (art. 154, 161), Prezydent→sędziowie (art. 179), PRM→Szef KPRM (art. 27 uRM), PRM→sekretarze stanu (art. 37 uRM), PRM→wojewoda (art. 6 uW), Sejm→Prezes NIK (art. 205), Sejm→Prezes NBP (art. 227 ust. 3), Sejm→Prezes UKE (PKE art. 415) |
| `confirms` | zatwierdza / zgoda / wotum zaufania | Sejm→RM (art. 154 ust. 2), Senat→Prezes NIK / RPO / UODO / IPN / RPD |
| `nominates` | wnioskuje / wskazuje / desygnuje | PRM→ministrowie (art. 154, 161), KRS→sędziowie (art. 179), Prezydent→Prezes NBP, minister→SS/PS (art. 37 ust. 3 uRM), MSWiA→wojewoda, PRM→Prezes UKE |
| `oversees` | nadzoruje / podległość | PRM→GUS/UOKiK/… (art. 33a), minister→urząd (rozp. atrybucyjne + obwieszczenie M.P.), Sejm→NIK (art. 202 ust. 2), Sejm→PIP |
| `ex_officio` | zasiada z urzędu | minister→RM (art. 147), MS→Prokurator Generalny (art. 1 § 2 PoP), I Prezes SN→KRS/TS, Prezes NBP→RPP, ministrowie→komitety RM |
| `advises` | doradza | RDS→RM, Rada Legislacyjna→PRM, RBN→Prezydent |
| `administers` | prowadzi | ZUS→FUS, minister→instytucja kultury (rzadko) |
| `dept_head` | organ→stanowisko szefa | zawsze |
| `office` | ciało→przewodniczący | KRRiT→Przewodniczący, PKW→Przewodniczący |

`seatsAppointed` = ile miejsc w ciele obsadza `from` (KRRiT: Sejm 2, Senat 1, Prezydent 2; RPP: po 3; KRS: Sejm 15+4,
Senat 2, Prezydent 1). `disputed: true` + `statusNote` tam, gdzie spór ustrojowy (KRS 2026, TK — 8 wybranych, 2 zaprzysiężonych).

### 3.3 Osoby, statusy, provenance
- Osoba istnieje tylko z `sourceUrl` (strona, na której widziano nazwisko przy funkcji). `startedAt` tylko z datowanego
  źródła (`startedAtSource`: postanowienie w M.P., datowany news gov.pl, biogram). Brak → `null`, nigdy zgadywanie.
- `status`: `verified` / `unverified` (źródło nieosiągalne) / `acting` (p.o.) / `disputed`. Węzeł: `active` / `vacant`
  (IPN — Senat odmówił zgody 6.08.2026) / `disputed` (TK, KRS) / `pending_abolition` (CBA po wecie 11.05.2026).
- `provenance {sources[], verifiedAt, confidence, verdict}` na każdym węźle, osobie i krawędzi; `verdict` pochodzi
  z adwersarialnej weryfikacji (confirmed / corrected / refuted→usunięte / unverified).
- Wiceministrowie (SS/PS) i dyrektor generalny = `people[]` na węźle ministerstwa (nie osobne węzły) — v0.1.

### 3.4 Liczby: `employeeCount` i `budgetPart`
Model (z rundy uzupełniającej): `{value, unit: etaty|osoby, measure: przeciętne|stan_na_dzien, asOf, scope: urzad|czesc_budzetowa|korpus_sc|osoba_prawna, source{url,type}, confidence}`.
Kaskada źródeł: plan finansowy w sprawozdaniu z wykonania budżetu (arkusze 036/038/042, CC0 — agencje, IGB, państwowe
osoby prawne: wiersz „VII Zatrudnienie w przeliczeniu na pełne etaty") → wystąpienia pokontrolne NIK P/26/001 (przeciętne
zatrudnienie per dysponent; 86/166 wyciągnięte regexem do `seeds/employee-count/`) → arkusze Sprawne Państwo (KSC per urząd)
→ kategorie ze Sprawozdania Szefa SC → `null` z uzasadnieniem (ABW, AW, CBA, SKW, SWW). Uwaga na zakres: GUS = 666 etatów
KSC vs 4 981 w części 58.

## 4. Mapa źródeł (synteza; szczegóły i URL-e w doc 02)

| Warstwa | Źródło | Format / licencja | Uwagi |
|---|---|---|---|
| Prawo (legalSource, cite) | **ELI API Sejmu** `api.sejm.gov.pl/eli` (DU 97 799 + MP 66 646 aktów), permalinki `eli.gov.pl/eli/DU/{rok}/{poz}/ogl` | JSON + PDF (+HTML dla części aktów) | ISAP i sejm.gov.pl → CAPTCHA/robots `Disallow` dla botów; **tylko API**. Brak kotwic do artykułu → `article` osobno |
| Inwentarz organów | rozp. atrybucyjne PRM (Dz.U. 2025 poz. 993–1005 + starsze), obwieszczenia ministrów o wykazach jednostek (299 w M.P.), lista KPRM (23), art. 33a, xlsx KPRM „wszystkie urzędy SC" (1 743), katalog gov.pl (19 ministerstw, 34 urzędy centralne, 16 UW), sądy: dane.gov.pl 985 (377), WSA: nsa.gov.pl, spółki: xlsx MAP (108) + dane.gov.pl 1198 + rozp. RM 2026/987, uczelnie/instytuty: **RAD-on API** (837 rekordów, REGON, kierownik, historia nadzoru; CC0), instytucje kultury: RIK xlsx | mieszane; gov.pl CC BY-SA 4.0, dane.gov.pl CC0/CC BY | Nie ma jednego rejestru organów; REGON wzbogaca (forma prawna 401/402/406/428), nie enumeruje |
| Osoby | gov.pl skład RM + „kierownictwo" (niespójne slugi, daty tylko w biogramach), Sejm API (posłowie, kluby, komisje z datami funkcji, zdjęcia), senat.gov.pl (HTML), strony organów (KRRiT/UOKiK/KGP wzorcowe z datami; TK/SN/NSA/KRS/NIK bez dat), Wikidata (CC0, tylko cross-check — nieaktualna) | HTML/JSON | nbp.pl blokuje boty; IPN bez prezesa; RM 21 osób |
| Oś czasu zmian | M.P. przez ELI: postanowienia Prezydenta „o zmianie w składzie RM" (220), „o powołaniu … sędziego", uchwały Sejmu o wyborze/powołaniu; postanowienia Marszałka o mandatach; `changes/acts?since=` do inkrementu; newsy resortów o wiceministrach (~75%+ pokrycia); e-dzienniki resortowe (nieudokumentowane JSON API `/api/eli/acts/{kod}/{rok}`) | PDF→pdftotext | SS/PS, wojewodowie, szefowie urzędów NIE trafiają do M.P. |
| Newsy | Sejm RSS (11), RMF24, TVN24, rp.pl, Onet, WP, Interia, money.pl, BI, Polsat, Wyborcza, OKO.press; Google News RSS (niekomercyjnie); gov.pl **bez RSS** (scraping listingów, CC BY-SA); PAP bez API | RSS | przechowywać tylko tytuł+link+data+źródło |
| Budżet | sprawozdanie z wykonania budżetu (dane.gov.pl 163, XLS, CC0), ustawa budżetowa (PDF), klasyfikacja części (Dz.U. 2025 poz. 1185) | XLS/PDF | part → dysponent = nasz `budgetPart` |
| Zdjęcia | Sejm API (bez licencji, warunki SIS: podać źródło), Senat/Commons CC BY-SA 3.0 PL, gov.pl CC BY-NC-ND 4.0 (bez kadrowania), prezydent.pl tylko ilustracyjnie | — | przechowujemy URL + atrybucję, nie kadrujemy |

## 5. Pipeline (jak budujemy i odświeżamy)

1. **Seed w falach agentami LLM + adwersarialna weryfikacja** (tak jak CivLab, ale z twardą bramką): 11 chunków
   (organy konstytucyjne, 5 grup ministerstw z jednostkami, urzędy PRM, ciała doradcze, sądownictwo, niezależne,
   wojewodowie) → każdy chunk sprawdza osobny agent-weryfikator (otwiera każde `sourceUrl`, czyta przepisy przez ELI)
   → `scripts/merge-chunks.py` scala, stosuje werdykty (refuted = usunięte), liczy `children`, `connectedNodes`,
   dokłada brakujące `dept_head`. Walidator: `scripts/validate-chunk.py`.
2. **Inkrementalne odświeżanie** (cron, np. co 6 h): (a) ELI `/changes/acts?since=` → nowe postanowienia/uchwały
   personalne w M.P. → parser (pdftotext + regex „powołuję/odwołuję Pana/Panią X na urząd/ze stanowiska Y") → wpis
   na oś czasu + zmiana `people`; statusy aktów (`uchylony`) zamykają węzły organizacji (np. Ministerstwo Przemysłu);
   (b) diff stron „kierownictwo"/„skład RM" (hash treści + ekstrakcja LLM przy zmianie); (c) newsy resortów o
   powołaniach; (d) kwartalnie: xlsx MAP, RAD-on, sprawozdanie budżetowe (etaty), Sprawozdanie SSC.
3. **Newsy i power map:** pobór RSS → dopasowanie wzmianek nazwisk/organów (słownik aliasów z grafu + NER) → liczniki
   per osoba/organ w oknie 90 dni (`total`, `recent`, `weeks[12]`, `heat`) jak w CivLab; streszczenia LLM z tagami
   encji (`<gov_entities='pl-…'>`) tylko na bazie tytułów/linków własnych źródeł oficjalnych (gov.pl CC BY-SA), nie
   pełnych tekstów prasy.
4. **Publikacja:** `data/pl/graph.json` (+ CSV: nodes, edges, people) na CC BY 4.0; strona „O danych" (źródła, licencje,
   RODO art. 14 — obowiązek informacyjny przez publikację polityki, tryb sprostowania, „to dane, nie werdykt").

## 6. Stack

- **v0.1 (teraz):** statyczny `graph.json` + `viewer/index.html` (D3 v7, jeden plik, dark/light, deep-link `#node=`,
  arkusz mobilny). Zero backendu. Testowane na 952 węzłach oryginału (płynne).
- **v1:** Supabase Postgres (tabele `node`, `position`, `person`, `tenure`, `edge`, `legal_source`, `change_event`,
  `article`, `mention`) + PostgREST jako publiczne read-API + Storage na zrzuty; Render cron dla pipeline'u; front
  Next.js SSR (strony organów indeksowalne; profile osób — do decyzji `noindex`). Zbieżne ze stackiem
  kontrola-obywatelska, więc infrastruktura jest wspólna.
- Otwarte pytanie (to samo, które zaparkowało kontrola-obywatelską): **konto Supabase firmowe Horyzonty vs osobne** —
  do rozstrzygnięcia przed v1; v0.1 nie wymaga żadnej infrastruktury.

## 7. Zakres: v0.1 → v1 → v2

- **v0.1 (seed, w budowie 2026-09-17):** ~300–450 węzłów: organy konstytucyjne, RM + 19 ministerstw + 21 ministrów
  + wiceministrowie/DG, jednostki podległe ministrom (max 45/grupę), 23 jednostki PRM + art. 33a, ~30 ciał doradczych,
  sądownictwo (SN, NSA, TK, TS, KRS, 16 WSA, klasy sądów, prokuratura), organy niezależne, 16 wojewodów + UW.
  Osoby: szefowie organów ze źródłem; statusy sporów. Bez newsów, bez etatów (seedy w `seeds/employee-count/`).
- **v1:** 100% podstaw prawnych, etaty i części budżetowe, oś czasu zmian (M.P.), open API +
  zrzuty, strona „O danych", automatyczne odświeżanie, komisje sejmowe/senackie z przewodniczącymi (Sejm API).
- **v2:** liście z RAD-on (136 uczelni, ~160 instytutów), 108 spółek SP z zarządami (KRS API), sądy per jednostka
  (377) z prezesami, pełnomocnicy rządu (18), placówki zagraniczne, administracja niezespolona; ewentualnie JST
  (osobny produkt — patrz kontrola-obywatelska).

## 8. Prawo i licencje — decyzje

1. **Nazwiska + funkcje osób publicznych są jawne** (art. 5 ust. 2 UDIP, art. 6 ust. 2 ustawy o otwartych danych;
   UODO: art. 6 ust. 1 lit. e/f + art. 86 RODO; precedensy rejestr.io 2019 i NSA III OSK 2582/21). Nie publikujemy
   danych prywatnych (adresy, majątek, PESEL). `party` tylko dla wybieralnych i tylko ze źródła oficjalnego (klub).
2. **Obowiązek informacyjny art. 14 RODO** (lekcja Bisnode): publiczna „Polityka danych" + tryb sprostowania +
   kontakt; brak masowej korespondencji (wyjątek niewspółmiernego wysiłku uzasadniamy publicznie).
3. **Wyrok TK K 2/23** dotyczy tylko oświadczeń majątkowych — nie blokuje grafu; wniosek: nie budować rankingów
   „osobowych" bez kontekstu, dane historyczne (byli piastuni) z datami, bez ocen.
4. **Zdjęcia:** Sejm API i Senat/Commons — tak; gov.pl (CC BY-NC-ND) — tak, bez kadrowania, z atrybucją; prezydent.pl
   — tylko w kontekście działalności Prezydenta; w wątpliwości inicjały zamiast zdjęcia.
5. **Newsy:** wyłącznie tytuł + link + data + źródło (prawo pokrewne wydawców od 20.09.2024); streszczenia własne
   z oficjalnych komunikatów (CC BY-SA). Google News RSS — użytek niekomercyjny z atrybucją.
6. **Scraping:** tylko API (Sejm, ELI, dane.gov.pl, RAD-on, KRS) i serwisy z `Allow: /` (gov.pl); nigdy HTML
   sejm.gov.pl / orka / monitorpolski.gov.pl (robots `Disallow: /`).
7. **Spory ustrojowe (TK, KRS, CBA, IPN):** modelujemy jako dane z cytatem obu stron (uchwała Sejmu / weto / wyrok),
   `disputed`/`vacant`/`pending_abolition`, język „stan sporu", nie „nielegalny".
8. **Nasza licencja:** dane CC BY 4.0, kod MIT; `provenance` na każdym fakcie umożliwia audyt.

## 9. Ryzyka

- **Dryf danych:** kierownictwa zmieniają się bez śladu w M.P. (SS/PS, wojewodowie, szefowie urzędów) → diff stron +
  newsy resortów; akceptujemy opóźnienie dni, nie tygodni. Miernik: odsetek osób z `verifiedAt` < 30 dni.
- **Halucynacje agentów:** twarda reguła `sourceUrl`/`startedAtSource`, weryfikacja adwersarialna, `refuted` = usunięte,
  `unverified` widoczne w UI. Test regresji: próbka 50 osób sprawdzana ręcznie przed każdą publikacją.
- **Blokady anty-bot** (nbp.pl, ISAP, sejm.gov.pl z chmury): pipeline na VPS musi zakładać CAPTCHA; używać API; dla NBP
  źródła wtórne + M.P.
- **Spory ustrojowe i zniesławienie:** tylko fakty z cytatem; nigdy oceny legalności; tryb sprostowania.
- **Reputacja/„pozorna jawność":** graf bez osi czasu jest tylko ładnym schematem — v1 musi mieć warstwę
  dynamiczną. U nas jest nią oś zmian personalnych z Monitora Polskiego, nie newsy (decyzja z 17.09.2026).

## 10. Następne kroki

1. Dokończyć seed (workflow 11 chunków + weryfikacja) → `merge-chunks.py` → `data/pl/graph.json` → QA w viewerze.
2. Opublikować prototyp (viewer + graph.json) jako stronę do oglądania; zebrać feedback 3–5 osób (dziennikarz,
   prawnik-konstytucjonalista, urzędnik) — czy graf jest *actionable* (bramka wartości jak w sejm-gazecie).
3. Zdecydować hosting (konto Supabase) i nazwę produktu; założyć repo.
4. v1 w kolejności: parser M.P. (oś czasu) → etaty/budżet (CC0 arkusze) → open API. Newsy i power map wycofane (17.09.2026).

## Powiązania
  dla szczebla centralnego), `poczekalnia/sejm-gazeta` (ślad legislacyjny jako źródło newsów).
