# Różnice zamierzone (nie zgłaszać jako błąd)

1. **Cztery płyty sektorów** zamiast trzech: dochodzi „Niezależne i kontrola” (NIK, RPO, NBP, KRRiT, PKW…), bo w Polsce to odrębna grupa konstytucyjna.
2. **Osobny łuk „Wojewodowie”** za pasmem Rady Ministrów (brak odpowiednika w US).
3. **Klik w linię relacji** przewija panel do tej relacji z przepisem; w oryginale linia tylko pokazuje słowo.
4. **Żetony typów relacji** (filtr) nad listą powiązań i na dole sceny: nasz dodatek.
5. **Typ relacji „wnioskuje / wskazuje”**: w US nie ma odpowiednika.
6. **Statusy „stan sporu”, „likwidacja w toku”** na węzłach i osobach (TK, KRS, CBA).
7. **Panel**: zamiast zakładki News mamy „Powiązania” i „Źródła i metryka”; brak newsów i power map jest znanym brakiem funkcji, nie błędem skórki (patrz `docs/00` parytet funkcji).
8. **Język i nazwy** po polsku; pieczęć „Naród Polski”.
9. **Motyw jasny wymuszony na starcie**, dopóki użytkownik nie przełączy (oryginał idzie za ustawieniem systemu; sprostowane 2026-09-17).
10. **Zoom przyciskami, kółkiem i przeciąganie sceny**: oryginał nie ma zoomu ani przesuwania w ogóle (sprostowane 2026-09-17).
11. **Brak strzałek ‹ ›** w prawym górnym rogu: w oryginale to poprzedni/następny węzeł, nie historia (sprostowane 2026-09-17).
12. **Rząd kwadracików to jeden węzeł zbiorczy** (np. „Prokuratury regionalne”); w oryginale każdy kwadracik to osobny węzeł.
13. **Pieczęć suwerena reaguje na najazd i jest klikalna** (w oryginale nie).
14. **Esc zamyka legendę, a dopiero potem odznacza węzeł; klik poza legendą ją zamyka** (decyzja właściciela z 2026-09-17).
15. **Reszta sceny przygasa przy wyborze węzła** (oryginał nie przygasza).
16. **Tryb huba** (ponad 60 relacji): domyślnie tylko dominujący typ relacji, jedna linia na organ, żeton „Wszystkie N”.
17. **Kapsuła „Parlament” jest samą etykietą grupy** (decyzja właściciela 2026-09-17): obrys nie reaguje na najazd ani klik, klikalne są izby; Zgromadzenie Narodowe jest dostępne z wyszukiwarki i z list powiązań, a po wybraniu podświetla kapsułę. W oryginale kapsuła to węzeł „Congress”.
18. **Relacja między sąsiadującymi glifami rysuje się jako mały łuk-mostek** (w oryginale takiej linii nie widać).
19. **Pod kursorem wygrywa wnętrze glifu, potem linia dokładnie pod kursorem, potem glif w tolerancji 5 px (drobne kropki), potem linia w tolerancji 7 px.**
20. **Napisy po obrocie zostają czytelne** (runda 4, B1): po obrocie grafu napisy sektorów, pierścieni, „PARLAMENT”, „RADA MINISTRÓW” i „WOJEWODOWIE” odwracają kierunek ścieżki, gdy wypadają w dolnej połowie, a tekst pieczęci jest kontr-obracany. W oryginale napisy stają do góry nogami.
21. **Wybór z adresu obraca od razu, wybór kliknięciem płynnie** (B1): link `#node=`, Wstecz/Dalej i zmiana hasha ustawiają graf od razu w położeniu docelowym; klik w glif, wynik wyszukiwania albo pozycję panelu obraca ok. 1 s najkrótszą drogą. Naród nie obraca grafu (wraca do 0°).
22. **Skala nie zmienia się przy obrocie** (B1): „Dopasuj” liczy skalę zawsze z ramki w położeniu wyjściowym, po obrocie zmienia się tylko wyśrodkowanie; na telefonie wybrany węzeł po obrocie jest dosuwany nad arkusz.
23. **Wachlarz stoi w wolnym pasie, nie na miejscu kropek** (B2): dla organów zewnętrznego pierścienia między pasmem Rady Ministrów a gronami kropek, dla organów z głębszych pierścieni między pierścieniami (wtedy napisy pierścieni chowają się na czas wachlarza), a przy hubie zawsze na zewnątrz, żeby nie stał na drodze pękowi promieni. Rzędy kwadracików (klasy zbiorcze) zostają na miejscu.
24. **Duże grona (izby parlamentu) rozwijają się w kilku łukach grupami**: ciała kolegialne i kancelaria, kluby i koła, komisje stałe, nadzwyczajne, śledcze. W oryginale nie ma tak licznych podjednostek.
25. **Kluby i koła to osobny typ „struktura polityczna”** z własnym glifem (zaokrągłony trójkąt, obrys przerywany) i pozycją w legendzie; w US nie ma odpowiednika.
26. **Legenda-filtr ma więcej pozycji** niż oryginał (Naród, Parlament, kluby i koła, klasy zbiorcze, wakat, p.o.) i każda jest przełącznikiem; wybrany z wyszukiwarki węzeł ukrytego typu jest pokazywany tymczasowo z komunikatem. Filtr żyje w `sessionStorage` (oryginał: tylko w pamięci strony).
27. **Rząd podjednostek rozsuwa się jak w oryginale, ale stoi we własnym pasie** (runda 5): tempo i kształt ruchu są przeniesione z pomiaru oryginału (start z kątów kropek, ok. 0,72 s, easeInOutCubic, wybrany element 1,6× większy, stały odstęp krawędzi, linie relacji wracają po ruchu, zamknięcie bez animacji rozsuwania). Różnica: w oryginale rząd zajmuje promień kropek, więc sąsiednie grona odjeżdżają na boki; u nas rząd ma wolny pas między pasmem a gronami, więc sąsiedzi zostają na miejscu i przygasają tylko przy realnym nałożeniu. Powód: kontur płyty ma zęby dopasowane do gron, a przesuwanie gron wymagałoby animowania konturu.
28. **Mini-glif wyrasta z kropki także promieniowo** (ok. 0,3 s): u nas kropki leżą dalej od środka niż pas rzędu, więc bez tego elementy przeskakiwałyby o 20–50 j.; w oryginale promień jest ten sam.
29. **Przełącznik skórek pływa w prawym górnym rogu** zamiast paska u góry, a przycisk motywu stoi na lewo od niego. W oryginale w tym rogu są motyw i strzałki poprzedni/następny węzeł. Powód: pasek zabierał 45 px wysokości i koło wychodziło wyraźnie mniejsze niż w oryginale.
30. **Wyszukiwarka to ikona w lewym górnym rogu sceny**, jak w oryginale, ale na telefonie zostaje polem w arkuszu panelu.
31. **Box informacyjny ma pod podstawą prawną wiersz etykiet** (skrót, sektor, typ, pierścień, status) i tytuł aktu; oryginał ich nie ma. Reszta boxu (tytuł 30 px / 600, opis 16 px, linki 14 px, siatka kart osób po dwie, „Zobacz wszystkich (N)”) jest przeniesiona z pomiaru strony organu w oryginale.
32. **Bez newsów i bez power map**: decyzja właściciela z 17.09.2026. W oryginale druga karta panelu to „News”, u nas „Powiązania”.
33. **Widok „Budżet” pokazuje budżet państwa według części budżetowych**, a nie budżet miasta według departamentów jak w wersji SF. Wewnętrzny pierścień to grupy funkcjonalne wyznaczone z działu klasyfikacji budżetowej o największym wykonaniu; części techniczne (dług, rezerwy, subwencje, składka do UE, ubezpieczenia społeczne) mają własne grupy. Źródła i metoda: `docs/06-budzet-zrodla-i-metoda.md`.
34. **Koło budżetu nie obraca się po wyborze** (decyzja właściciela z 18.09.2026). W oryginale wybrany segment staje na godz. 6; u nas zostaje na miejscu, a podpisy po łuku stają przy nim i w dolnej połowie biegną odwrotnie, żeby nie stać do góry nogami. Skutek: pierścień jest o kilka procent mniejszy, bo podpisy potrzebują miejsca dookoła.
35. **Część budżetowa bez własnego organu w grafie** (np. samorządowe kolegia odwoławcze) ma kartę części zamiast strony węzła; oryginał ma węzeł dla każdego departamentu.

