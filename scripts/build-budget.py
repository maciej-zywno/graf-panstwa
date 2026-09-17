#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-budget.py - wydatki budżetu państwa według części budżetowych dla widoku „Budżet”.

Wynik:   data/pl/budget.json
Źródła:  wyłącznie urzędowe (szczegóły i licencje: docs/06-budzet-zrodla-i-metoda.md)
  * dane.gov.pl, zbiór 163 „Część tabelaryczna sprawozdań z wykonania budżetu państwa”
    (Ministerstwo Finansów, CC0 1.0) - jeden ZIP na rok, w nim Tom I i Tom II,
  * rozporządzenie MF w sprawie klasyfikacji części budżetowych oraz określenia ich
    dysponentów (t.j. Dz.U. 2025 poz. 1185) - urzędowe nazwy części,
  * rozporządzenia Prezesa RM w sprawie szczegółowego zakresu działania ministrów
    (zdanie „Minister jest dysponentem części ... budżetu państwa”),
  * ustawa budżetowa na rok 2026 (Dz.U. 2026 poz. 62), załącznik nr 2 - plan 2026.

Pliki źródłowe trafiają do pamięci podręcznej data/pl/budget-src/ (katalog jest w .gitignore;
w repozytorium zostają tylko adresy i sumy kontrolne SHA-256 zapisane niżej i w budget.json).

Zależności:
  python3 -m pip install --user xlrd openpyxl      # xlrd: arkusz .xls z 2025 r., openpyxl: .xlsx
  pdftotext (pakiet poppler; macOS: brew install poppler) - potrzebny do nazw części,
  planu 2026 i drugiego, niezależnego odczytu z PDF. Bez niego skrypt działa, ale ustawia
  planYear = null, bierze nazwy części z arkusza i pomija drugi odczyt (głośno o tym informuje).

Użycie:
  python3 scripts/build-budget.py                  # pobiera brakujące pliki, buduje, waliduje
  python3 scripts/build-budget.py --offline        # tylko pamięć podręczna, bez sieci
  python3 scripts/build-budget.py --list-resources # wypisuje zasoby zbioru 163 (pomoc przy nowym roku)
  python3 scripts/build-budget.py --date 2026-09-18  # stała data w meta.generatedAt (powtarzalny wynik)

Kod wyjścia != 0, gdy nie zgadza się którakolwiek suma kontrolna albo walidacja.
"""
import argparse
import datetime
import hashlib
import io
import json
import random
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / 'data' / 'pl' / 'budget-src'
OUT = ROOT / 'data' / 'pl' / 'budget.json'
GRAPH = ROOT / 'data' / 'pl' / 'graph.json'
UA = 'Mozilla/5.0 (compatible; graf-panstwa-budget/1.0; +https://grafpanstwa.pl)'

CURRENT_YEAR = 2025
PLAN_YEAR = 2026
DATASET_URL = 'https://dane.gov.pl/pl/dataset/163'
DATASET_API = 'https://api.dane.gov.pl/1.4/datasets/163/resources?per_page=100&sort=-created'
TOL = 0.001  # tys. zł, czyli 1 zł - dopuszczalna różnica sum (szum zmiennoprzecinkowy w arkuszach)

# ---------------------------------------------------------------------------------------------
# 1. ŹRÓDŁA (adresy + sumy kontrolne; pliki w data/pl/budget-src/)
# ---------------------------------------------------------------------------------------------
YEARS = {
    2025: {'zip': 'wyk2025.zip', 'resource': 2054935,
           'url': 'https://api.dane.gov.pl/resources/2054935,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2025-r/file',
           'sha256': 'ea4e38df86da7b41b12f2fd00dc80c94b260ee0e0687222e97995862a183e7d7'},
    2024: {'zip': 'wyk2024.zip', 'resource': 72399,
           'url': 'https://api.dane.gov.pl/resources/72399,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2024-r/file',
           'sha256': '22bbb6c47434c48da5b28d539262b425b5fe1eaacf57e4b4604bd5830ac1e3cb'},
    2023: {'zip': 'wyk2023.zip', 'resource': 58249,
           'url': 'https://api.dane.gov.pl/resources/58249,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2023-r/file',
           'sha256': '08b05037c6163d9ed3572b69190b08e13420f98ba90c3d28d40611055782ca74'},
    2022: {'zip': 'wyk2022.zip', 'resource': 48622,
           'url': 'https://api.dane.gov.pl/resources/48622,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2022-r/file',
           'sha256': 'df384cb1d09e2c06e652a85044d6c9f04dcbb48f7626a7a60e4b823f1ab1ddf5'},
    2021: {'zip': 'wyk2021.zip', 'resource': 38967,
           'url': 'https://api.dane.gov.pl/resources/38967,czesc-tabelaryczna-sprawozdania-z-wykonania-budzetu-panstwa-w-2021-r/file',
           'sha256': 'db463035dbe382a405d84625af7528db4cbdc8096fd4389dea8f80634f285f14'},
}
# Pliki w Tomie I / Tomie II (wzorce na nazwę pliku bez katalogu; układ jest ten sam od 2021 r.)
FILES = [
    # (klucz, tom, wzorzec, co zawiera)
    ('005', 1, r'^005\b', 'zestawienie ogólne: oficjalna łączna kwota wydatków (wykonanie razem z niewygasającymi)'),
    ('011', 1, r'^011\b', 'zestawienie zbiorcze według działów + wiersz OGÓŁEM'),
    ('012', 1, r'^012\b', 'części 01-84 (z podczęściami 15/xx)'),
    ('013', 1, r'^013\b', 'części 81 i 83 (rezerwy)'),
    ('014', 1, r'^014\b', 'część 85 zbiorczo'),
    ('015', 1, r'^015\b', 'części 86 (z podczęściami), 88-91'),
    ('t2-07', 2, r'WYDATKI.*WG WOJEW', 'podczęści 85/02-85/32'),
]
LICENSE_DANE = 'CC0 1.0'
LICENSE_ACT = 'materiał urzędowy (art. 4 pkt 1 i 2 ustawy o prawie autorskim i prawach pokrewnych)'

ACTS = {
    'klasyfikacja': {
        'title': 'Rozporządzenie Ministra Finansów z dnia 4 grudnia 2009 r. w sprawie klasyfikacji części '
                 'budżetowych oraz określenia ich dysponentów (t.j. Dz.U. 2025 poz. 1185)',
        'eli': 'DU/2025/1185', 'file': 'D20251185.pdf',
        'url': 'https://api.sejm.gov.pl/eli/acts/DU/2025/1185/text/O/D20251185.pdf',
        'page': 'https://eli.gov.pl/eli/DU/2025/1185/ogl',
        'sha256': 'bd8949d3b053ec96abb8c00ec811ecdc7dfca88d8128923beaac73b5593f1dd7'},
    'ub2026': {
        'title': 'Ustawa budżetowa na rok 2026 z dnia 9 stycznia 2026 r. (Dz.U. 2026 poz. 62), załącznik nr 2',
        'eli': 'DU/2026/62', 'file': 'D20260062.pdf',
        'url': 'https://api.sejm.gov.pl/eli/acts/DU/2026/62/text/O/D20260062.pdf',
        'page': 'https://eli.gov.pl/eli/DU/2026/62/ogl',
        'sha256': 'a2486ce997442850401d19c763c767afbfda3a7b187985d343c3d3f10dc960da'},
}

# ---------------------------------------------------------------------------------------------
# 2. DYSPONENCI I WĘZŁY GRAFU
# ---------------------------------------------------------------------------------------------
# 2a. Ministrowie: zdanie „Minister jest dysponentem części ... budżetu państwa” w rozporządzeniu
#     Prezesa RM o szczegółowym zakresie działania. Skrypt pobiera akt i sprawdza listę części.
#     'office' = urząd obsługujący ministra w zakresie danej części (węzeł wybierany po kliknięciu).
MINISTER_ACTS = [
    {'eli': 'DU/2023/2707', 'minister': 'Minister Obrony Narodowej', 'position': 'pl-minister-obrony-narodowej',
     'office': {'29': 'pl-ministerstwo-obrony-narodowej'}},
    {'eli': 'DU/2023/2711', 'minister': 'Minister Funduszy i Polityki Regionalnej', 'position': 'pl-minister-funduszy-i-polityki-regionalnej',
     'office': {'34': 'pl-ministerstwo-funduszy-i-polityki-regionalnej'}},
    {'eli': 'DU/2023/2715', 'minister': 'Minister Rodziny, Pracy i Polityki Społecznej', 'position': 'pl-minister-rodziny-pracy-i-polityki-spolecznej',
     'office': {c: 'pl-ministerstwo-rodziny-pracy-i-polityki-spolecznej' for c in ('31', '44', '63')}},
    {'eli': 'DU/2023/2717', 'minister': 'Minister Edukacji', 'position': 'pl-minister-edukacji',
     'office': {'30': 'pl-ministerstwo-edukacji-narodowej'}},
    {'eli': 'DU/2023/2720', 'minister': 'Minister Cyfryzacji', 'position': 'pl-minister-cyfryzacji',
     'office': {'27': 'pl-ministerstwo-cyfryzacji'}},
    {'eli': 'DU/2023/2725', 'minister': 'Minister Infrastruktury', 'position': 'pl-minister-infrastruktury',
     'office': {c: 'pl-ministerstwo-infrastruktury' for c in ('21', '22', '39', '69')}},
    {'eli': 'DU/2025/68', 'minister': 'Minister Nauki i Szkolnictwa Wyższego', 'position': 'pl-minister-nauki-i-szkolnictwa-wyzszego',
     # 67: część nosi nazwę PAN i w grafie jest węzeł PAN; 90: Akademia Kopernikańska nie ma węzła
     'office': {'28': 'pl-ministerstwo-nauki-i-szkolnictwa-wyzszego', '67': 'pl-polska-akademia-nauk',
                '90': 'pl-ministerstwo-nauki-i-szkolnictwa-wyzszego'}},
    {'eli': 'DU/2025/993', 'minister': 'Minister Spraw Zagranicznych', 'position': 'pl-minister-spraw-zagranicznych',
     'office': {c: 'pl-ministerstwo-spraw-zagranicznych' for c in ('23', '45')}},
    {'eli': 'DU/2025/994', 'minister': 'Minister Aktywów Państwowych', 'position': 'pl-minister-aktywow-panstwowych',
     'office': {c: 'pl-ministerstwo-aktywow-panstwowych' for c in ('26', '55')}},
    {'eli': 'DU/2025/995', 'minister': 'Minister Klimatu i Środowiska', 'position': 'pl-minister-klimatu-i-srodowiska',
     'office': {c: 'pl-ministerstwo-klimatu-i-srodowiska' for c in ('41', '51')}},
    {'eli': 'DU/2025/996', 'minister': 'Minister Kultury i Dziedzictwa Narodowego', 'position': 'pl-minister-kultury-i-dziedzictwa-narodowego',
     'office': {'24': 'pl-ministerstwo-kultury-i-dziedzictwa-narodowego'}},
    {'eli': 'DU/2025/997', 'minister': 'Minister Finansów i Gospodarki', 'position': 'pl-minister-finansow-i-gospodarki',
     # § 1 ust. 4: MRiT obsługuje działy budownictwo (cz. 18) i gospodarka (cz. 20), MF - budżet, finanse, instytucje finansowe (cz. 19)
     'office': {'18': 'pl-ministerstwo-rozwoju-i-technologii', '19': 'pl-ministerstwo-finansow',
                '20': 'pl-ministerstwo-rozwoju-i-technologii'}},
    {'eli': 'DU/2025/999', 'minister': 'Minister Spraw Wewnętrznych i Administracji', 'position': 'pl-minister-spraw-wewnetrznych-i-administracji',
     'office': {c: 'pl-ministerstwo-spraw-wewnetrznych-i-administracji' for c in ('17', '42', '43')}},
    {'eli': 'DU/2025/1000', 'minister': 'Minister Rolnictwa i Rozwoju Wsi', 'position': 'pl-minister-rolnictwa-i-rozwoju-wsi',
     'office': {c: 'pl-ministerstwo-rolnictwa-i-rozwoju-wsi' for c in ('32', '33', '35', '62')}},
    {'eli': 'DU/2025/1002', 'minister': 'Minister Sportu i Turystyki', 'position': 'pl-minister-sportu-i-turystyki',
     'office': {c: 'pl-ministerstwo-sportu-i-turystyki' for c in ('25', '40')}},
    {'eli': 'DU/2025/1004', 'minister': 'Minister Zdrowia', 'position': 'pl-minister-zdrowia',
     'office': {'46': 'pl-ministerstwo-zdrowia'}},
    {'eli': 'DU/2025/1005', 'minister': 'Minister Sprawiedliwości', 'position': 'pl-minister-sprawiedliwosci',
     # 15: część „Sądy powszechne” ma w grafie własny węzeł zbiorczy
     'office': {'15': 'pl-sady-powszechne', '37': 'pl-ministerstwo-sprawiedliwosci'}},
    {'eli': 'DU/2025/1206', 'minister': 'Minister Energii', 'position': 'pl-minister-energii',
     'office': {c: 'pl-ministerstwo-energii' for c in ('47', '48')}},
]

# 2b. Części, których dysponenta wskazuje wprost § 2 ust. 2 rozporządzenia o klasyfikacji
#     („minister właściwy do spraw ...”); konkretny minister wynika z aktów z tabeli 2a.
CLASSIFICATION_DISPOSERS = {
    '79': ('DU/2025/997', '§ 2 ust. 2 pkt 2 rozp. o klasyfikacji części: minister właściwy do spraw budżetu, finansów publicznych i instytucji finansowych'),
    '82': ('DU/2025/997', '§ 2 ust. 2 pkt 2 rozp. o klasyfikacji części: minister właściwy do spraw budżetu, finansów publicznych i instytucji finansowych'),
    '84': ('DU/2025/997', '§ 2 ust. 2 pkt 2 rozp. o klasyfikacji części: minister właściwy do spraw budżetu, finansów publicznych i instytucji finansowych'),
    '80': ('DU/2025/999', '§ 2 ust. 2 pkt 3 rozp. o klasyfikacji części: minister właściwy do spraw administracji publicznej'),
}
CLASSIFICATION_OFFICE = {'79': 'pl-ministerstwo-finansow', '82': 'pl-ministerstwo-finansow',
                         '84': 'pl-ministerstwo-finansow', '80': 'pl-ministerstwo-spraw-wewnetrznych-i-administracji'}

# 2c. Części noszące nazwę instytucji, która ma węzeł w grafie. Dysponentem jest kierownik jednostki
#     (art. 2 pkt 8 ustawy o finansach publicznych); nazwę stanowiska bierzemy z pola `head` węzła
#     i oznaczamy jako NIEzweryfikowaną w akcie szczegółowym (dysponentVerified = false).
INSTITUTION_NODES = {
    '01': 'pl-kancelaria-prezydenta-rp', '02': 'pl-kancelaria-sejmu', '03': 'pl-kancelaria-senatu',
    '04': 'pl-sad-najwyzszy', '05': 'pl-nsa', '06': 'pl-trybunal-konstytucyjny', '07': 'pl-nik',
    '08': 'pl-biuro-rpo', '09': 'pl-krrit', '10': 'pl-uodo', '11': 'pl-kbw', '12': 'pl-pip', '13': 'pl-ipn',
    '14': 'pl-biuro-rpd', '16': 'pl-kprm', '49': 'pl-urzad-zamowien-publicznych', '50': 'pl-ure',
    '52': 'pl-krajowa-rada-sadownictwa', '53': 'pl-uokik',
    '54': 'pl-urzad-do-spraw-kombatantow-i-osob-represjonowanych', '56': 'pl-cba', '57': 'pl-abw',
    '58': 'pl-gus', '59': 'pl-aw', '60': 'pl-wyzszy-urzad-gorniczy', '61': 'pl-urzad-patentowy-rp',
    '64': 'pl-glowny-urzad-miar', '65': 'pl-polski-komitet-normalizacyjny',
    '66': 'pl-biuro-rzecznika-praw-pacjenta', '68': 'pl-panstwowa-agencja-atomistyki', '71': 'pl-utk',
    '72': 'pl-kasa-rolniczego-ubezpieczenia-spolecznego', '73': 'pl-zus', '74': 'pl-prokuratoria-generalna-rp',
    '75': 'pl-rcl', '76': 'pl-uke', '88': 'pl-prokuratura', '89': 'pl-pkdp',
    '15/01': 'pl-ministerstwo-sprawiedliwosci',
}
# Strażnik „nie zgaduj”: dla przypisań po nazwie skrypt sprawdza, czy rdzenie słów z urzędowej nazwy części
# występują w nazwie, skrócie albo aliasach węzła. Wyjątek wymaga wpisu z uzasadnieniem (dziś żaden nie jest potrzebny).
NAME_MATCH_EXCEPTIONS = {}
# Województwo (nazwa podczęści 85/xx) -> węzeł urzędu wojewódzkiego i wojewody.
VOIVODESHIP_NODES = {
    '85/02': ('pl-dolnoslaski-urzad-wojewodzki', 'pl-wojewoda-dolnoslaski'),
    '85/04': ('pl-kujawsko-pomorski-urzad-wojewodzki', 'pl-wojewoda-kujawsko-pomorski'),
    '85/06': ('pl-lubelski-urzad-wojewodzki', 'pl-wojewoda-lubelski'),
    '85/08': ('pl-lubuski-urzad-wojewodzki', 'pl-wojewoda-lubuski'),
    '85/10': ('pl-lodzki-urzad-wojewodzki', 'pl-wojewoda-lodzki'),
    '85/12': ('pl-malopolski-urzad-wojewodzki', 'pl-wojewoda-malopolski'),
    '85/14': ('pl-mazowiecki-urzad-wojewodzki', 'pl-wojewoda-mazowiecki'),
    '85/16': ('pl-opolski-urzad-wojewodzki', 'pl-wojewoda-opolski'),
    '85/18': ('pl-podkarpacki-urzad-wojewodzki', 'pl-wojewoda-podkarpacki'),
    '85/20': ('pl-podlaski-urzad-wojewodzki', 'pl-wojewoda-podlaski'),
    '85/22': ('pl-pomorski-urzad-wojewodzki', 'pl-wojewoda-pomorski'),
    '85/24': ('pl-slaski-urzad-wojewodzki', 'pl-wojewoda-slaski'),
    '85/26': ('pl-swietokrzyski-urzad-wojewodzki', 'pl-wojewoda-swietokrzyski'),
    '85/28': ('pl-warminsko-mazurski-urzad-wojewodzki', 'pl-wojewoda-warminsko-mazurski'),
    '85/30': ('pl-wielkopolski-urzad-wojewodzki', 'pl-wojewoda-wielkopolski'),
    '85/32': ('pl-zachodniopomorski-urzad-wojewodzki', 'pl-wojewoda-zachodniopomorski'),
}
# Części bez węzła - powód trafia do pola `note`.
NO_NODE_REASON = {
    '81': 'Część techniczna (rezerwa ogólna): nie jest budżetem żadnego urzędu, więc nie ma węzła. Rezerwą dysponuje Rada Ministrów (art. 155 ust. 1 ustawy o finansach publicznych).',
    '83': 'Część techniczna (rezerwy celowe): nie jest budżetem żadnego urzędu, więc nie ma węzła. Podziału rezerw dokonuje Minister Finansów w porozumieniu z dysponentami części (art. 154 ust. 1 ustawy o finansach publicznych).',
    '85': 'Część zbiorcza: suma 16 budżetów wojewodów. Węzły mają podczęści 85/02-85/32 (urzędy wojewódzkie); w grafie nie ma węzła zbiorczego „wojewodowie”.',
    '86': 'W grafie nie ma węzłów samorządowych kolegiów odwoławczych; dysponenta nie ustalono w sprawdzonych aktach.',
    '91': 'W grafie nie ma węzła Rady Fiskalnej ani jej Biura; dysponenta nie ustalono w sprawdzonych aktach.',
}
NO_NODE_SUBPART = {
    '15': 'W grafie nie ma węzłów poszczególnych sądów apelacyjnych; podczęść obejmuje wszystkie sądy z obszaru apelacji. Zobacz część macierzystą 15 (węzeł „Sądy powszechne”).',
    '86': 'W grafie nie ma węzłów samorządowych kolegiów odwoławczych.',
}
# Uwagi merytoryczne do części (ręczne, każda ma pokrycie w danych albo w akcie).
PART_NOTES = {
    '15/01': 'W sprawozdaniach za wszystkie lata 2021-2025 wykonanie tej podczęści wynosi 0 (w 2025 r. wiersz „c” jest pusty także w PDF), a plan po zmianach (2025: 195 170 tys. zł) jest wielokrotnie niższy od planu z ustawy (2025: 1 785 888 tys. zł). Interpretacja, nie fakt ze źródła: to pula w dyspozycji Ministra Sprawiedliwości rozdzielana w ciągu roku między podczęści obszarów apelacji.',
    '20': 'W 2025 r. 94% wykonania tej części to dział 757 „Obsługa długu publicznego”, rozdział 75704 „Rozliczenia z tytułu poręczeń i gwarancji udzielonych przez Skarb Państwa” (34 662 332 tys. zł), dlatego reguła „największy dział” umieszcza część w grupie „Obsługa długu publicznego”, a nie w gospodarce.',
    '73': 'Część obejmuje nie tylko dotacje do Funduszu Ubezpieczeń Społecznych (dział 753), ale też świadczenia z działu 855 „Rodzina” wypłacane przez ZUS; dział 753 to w 2025 r. ok. 53% wykonania.',
    '84': 'Od budżetu na rok 2027 część zmienia nazwę na „Zasoby własne Unii Europejskiej” (Dz.U. 2026 poz. 1026).',
    '85': 'Największy dział (855 „Rodzina”) to tylko ok. 33% wykonania; budżety wojewodów obejmują 29 działów (m.in. pomoc społeczna, ochrona zdrowia, rolnictwo, bezpieczeństwo).',
    '90': 'Akademia Kopernikańska nie ma węzła w grafie; węzeł wskazuje urząd obsługujący dysponenta (Minister Nauki i Szkolnictwa Wyższego, Dz.U. 2025 poz. 68).',
    '80': 'Regionalne izby obrachunkowe nie mają węzła w grafie; węzeł wskazuje urząd obsługujący dysponenta (minister właściwy do spraw administracji publicznej).',
    '91': 'Część utworzona 15 lutego 2025 r. (Dz.U. 2025 poz. 189): w ustawie budżetowej na 2025 r. plan wynosił 0, środki pojawiły się dopiero w planie po zmianach. W ustawie budżetowej na 2026 r. jest tylko rezerwa celowa „na realizację zadań wynikających z ustawy o Radzie Fiskalnej”.',
}

# ---------------------------------------------------------------------------------------------
# 3. GRUPY (wewnętrzny pierścień). Reguła: grupa części = grupa działu klasyfikacji budżetowej
#    o największym wykonaniu w tej części (gdy wykonanie całej części = 0, czyli rezerwy: o największym
#    planie). Dział 758 „Różne rozliczenia” jest workiem technicznym, więc rozstrzyga w nim rozdział.
# ---------------------------------------------------------------------------------------------
GROUPS = [
    ('obrona', 'Obrona narodowa i bezpieczeństwo', 'functional'),
    ('administracja', 'Władza państwowa, administracja i wymiar sprawiedliwości', 'functional'),
    ('zdrowie', 'Ochrona zdrowia', 'functional'),
    ('nauka-kultura', 'Nauka, oświata, kultura i sport', 'functional'),
    ('spoleczne', 'Rodzina i polityka społeczna', 'functional'),
    ('gospodarka', 'Gospodarka, infrastruktura, rolnictwo i środowisko', 'functional'),
    ('ubezpieczenia', 'Ubezpieczenia społeczne (ZUS i KRUS)', 'technical'),
    ('dlug', 'Obsługa długu publicznego', 'technical'),
    ('samorzady', 'Subwencje ogólne dla samorządów', 'technical'),
    ('ue', 'Składka do budżetu Unii Europejskiej', 'technical'),
    ('rezerwy', 'Rezerwy budżetowe', 'technical'),
]
DZIAL_TO_GROUP = {
    '010': 'gospodarka', '020': 'gospodarka', '050': 'gospodarka', '100': 'gospodarka', '150': 'gospodarka',
    '400': 'gospodarka', '500': 'gospodarka', '550': 'gospodarka', '600': 'gospodarka', '630': 'gospodarka',
    '700': 'gospodarka', '710': 'gospodarka', '900': 'gospodarka', '925': 'gospodarka',
    '720': 'administracja', '750': 'administracja', '751': 'administracja', '755': 'administracja', '756': 'administracja',
    '752': 'obrona', '754': 'obrona',
    '753': 'ubezpieczenia',
    '757': 'dlug',
    '758': None,  # rozstrzyga rozdział, patrz ROZDZIAL_758_TO_GROUP
    '730': 'nauka-kultura', '801': 'nauka-kultura', '854': 'nauka-kultura', '921': 'nauka-kultura', '926': 'nauka-kultura',
    '851': 'zdrowie',
    '852': 'spoleczne', '853': 'spoleczne', '855': 'spoleczne',
}
ROZDZIAL_758_TO_GROUP = {
    '75817': 'rezerwy', '75818': 'rezerwy',
    '75801': 'samorzady', '75802': 'samorzady', '75803': 'samorzady', '75804': 'samorzady', '75805': 'samorzady',
    '75806': 'samorzady', '75807': 'samorzady', '75809': 'samorzady', '75833': 'samorzady', '75834': 'samorzady',
    '75835': 'samorzady',
    '75850': 'ue',
    # programy regionalne współfinansowane z UE (część 34 „Rozwój regionalny”)
    '75863': 'gospodarka', '75864': 'gospodarka', '75865': 'gospodarka', '75866': 'gospodarka', '75868': 'gospodarka',
    # rozliczenia państwa ze związkami wyznaniowymi i partiami - brak lepszej grupy funkcjonalnej
    '75822': 'administracja', '75823': 'administracja',
    '75814': 'administracja',
}


# ---------------------------------------------------------------------------------------------
# 4. NARZĘDZIA
# ---------------------------------------------------------------------------------------------
class BuildError(Exception):
    pass


LOG = []


def log(msg=''):
    print(msg)
    LOG.append(msg)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest_path():
    return SRC_DIR / '_manifest.json'


def load_manifest():
    p = manifest_path()
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def save_manifest(m):
    manifest_path().write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + '.part')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=300) as r, open(tmp, 'wb') as f:
            shutil.copyfileobj(r, f)
    except Exception as e:  # np. brak certyfikatów w Pythonie - próbujemy curl
        if shutil.which('curl') is None:
            raise BuildError(f'Nie udało się pobrać {url}: {e}')
        res = subprocess.run(['curl', '-sS', '-L', '--fail', '-A', UA, '-m', '600', '-o', str(tmp), url])
        if res.returncode != 0:
            raise BuildError(f'Nie udało się pobrać {url} (urllib: {e}; curl: kod {res.returncode})')
    tmp.replace(dest)


def fetch(url, dest, offline, expected_sha='', accept_changed=False):
    """Zwraca (ścieżka, sha256, retrievedAt). Pobiera tylko wtedy, gdy pliku nie ma w pamięci podręcznej."""
    manifest = load_manifest()
    key = str(dest.relative_to(SRC_DIR))
    if not dest.exists() or dest.stat().st_size == 0:
        if offline:
            raise BuildError(f'--offline: brak pliku {dest} w pamięci podręcznej (adres: {url})')
        log(f'  pobieram {url}')
        download(url, dest)
        manifest[key] = {'url': url, 'retrievedAt': datetime.date.today().isoformat()}
        save_manifest(manifest)
    digest = sha256_of(dest)
    if expected_sha is None and dest.parent == SRC_DIR:
        log(f'  UWAGA: {dest.name} nie ma zapisanej sumy w skrypcie; SHA-256 = {digest}')
    if expected_sha and digest != expected_sha:
        msg = (f'Suma SHA-256 pliku {dest.name} różni się od zapisanej w skrypcie:\n'
               f'    oczekiwana {expected_sha}\n    jest       {digest}\n'
               '    Wydawca mógł podmienić plik. Sprawdź zmianę i zaktualizuj sumę w skrypcie '
               '(albo uruchom z --accept-changed).')
        if not accept_changed:
            raise BuildError(msg)
        log('UWAGA: ' + msg)
    retrieved = manifest.get(key, {}).get('retrievedAt')
    if not retrieved:
        retrieved = datetime.date.fromtimestamp(dest.stat().st_mtime).isoformat()
    return dest, digest, retrieved


def num(v):
    """Kwota w tys. zł z dokładnością źródła (grosze = 5 miejsc po przecinku), bez szumu float."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return 0
    if isinstance(v, str):
        raise BuildError(f'Tekst w kolumnie kwot: {v!r}')
    r = round(float(v), 5)
    return int(r) if r == int(r) else r


def close(a, b, tol=TOL):
    return abs(a - b) <= tol


def clean_ws(s):
    return ' '.join(str(s).split())


def norm_name(s):
    s = clean_ws(s).upper().replace('–', '-').replace('—', '-').replace('‒', '-')
    s = re.sub(r'\s*-\s*', '-', s)
    s = re.sub(r'\s*,\s*', ', ', s)
    return s.rstrip(',. ')


def norm_part(v):
    if isinstance(v, (int, float)):
        return f'{int(v):02d}'
    s = str(v).strip().rstrip('.')
    m = re.fullmatch(r'(\d{1,2})(?:/(\d{1,2}))?', s)
    if not m:
        raise BuildError(f'Nierozpoznany kod części: {v!r}')
    return f'{int(m.group(1)):02d}' + (f'/{int(m.group(2)):02d}' if m.group(2) else '')


def norm_code(v, width):
    if isinstance(v, (int, float)):
        return f'{int(v):0{width}d}'
    s = str(v).strip()
    if not re.fullmatch(r'\d{1,%d}' % width, s):
        raise BuildError(f'Nierozpoznany kod klasyfikacji: {v!r}')
    return s.zfill(width)


def zip_name(info):
    """Nazwy w starszych ZIP-ach MF są w CP852 bez flagi UTF-8."""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode('cp437').decode('cp852')
    except Exception:
        return info.filename


def open_tom(zpath, tom):
    z = zipfile.ZipFile(zpath)
    for info in z.infolist():
        name = zip_name(info)
        if not name.upper().endswith('.ZIP'):
            continue
        is_tom2 = bool(re.search(r'TOM II\b', name.upper()))
        if is_tom2 == (tom == 2):
            return name, zipfile.ZipFile(io.BytesIO(z.read(info)))
    raise BuildError(f'W {zpath.name} nie znaleziono wewnętrznego ZIP-a Tomu {"II" if tom == 2 else "I"}')


def find_member(inner, pattern):
    hits = []
    for info in inner.infolist():
        if info.is_dir():
            continue
        base = zip_name(info).split('/')[-1]
        if re.search(pattern, base, re.I) and base.lower().endswith(('.xls', '.xlsx')):
            hits.append((info, base))
    if len(hits) != 1:
        raise BuildError(f'Wzorzec {pattern!r}: oczekiwano 1 pliku, jest {len(hits)}: {[b for _, b in hits]}')
    return hits[0]


def read_sheets(data, filename):
    """Zwraca listę (nazwa arkusza, wiersze). .xls -> xlrd, .xlsx -> openpyxl."""
    out = []
    if filename.lower().endswith('.xls'):
        try:
            import xlrd
        except ImportError:
            raise BuildError('Brak biblioteki xlrd: python3 -m pip install --user xlrd')
        wb = xlrd.open_workbook(file_contents=data)
        for s in wb.sheets():
            rows = [[s.cell_value(r, c) if s.cell_type(r, c) not in (0, 6) else None for c in range(s.ncols)]
                    for r in range(s.nrows)]
            out.append((s.name, rows))
    else:
        try:
            import openpyxl
        except ImportError:
            raise BuildError('Brak biblioteki openpyxl: python3 -m pip install --user openpyxl')
        wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        for ws in wb.worksheets:
            out.append((ws.title, [list(r) for r in ws.iter_rows(values_only=True)]))
    return out


def is_blank(v):
    return v is None or (isinstance(v, str) and v.strip() in ('', 'brak'))


# ---------------------------------------------------------------------------------------------
# 5. PARSER ARKUSZY WYDATKÓW
#    Każda pozycja (część / dział / rozdział) to blok wierszy oznaczonych literą:
#      a - budżet wg ustawy budżetowej, b - budżet po zmianach, c - wykonanie, d - wydatki niewygasające.
#    Arkusz rezerw (013): a - ustawa, f - budżet po zmianach (rezerwy), g - wykorzystanie w drodze
#      przeniesień, b - budżet po zmianach: pozostałość rezerw. Wiersza „c” nie ma: rezerw się nie
#      „wykonuje”, tylko przenosi do innych części, gdzie widać je w wykonaniu.
# ---------------------------------------------------------------------------------------------
def parse_sheet(rows, label):
    poz = raz = None
    for r in rows[:20]:
        for c, v in enumerate(r):
            if isinstance(v, str) and v.strip() == 'Poz.':
                poz = c
            if isinstance(v, str) and v.strip() == 'Razem':
                raz = c
        if poz is not None and raz is not None:
            break
    if poz is None or raz is None or raz != poz + 1:
        raise BuildError(f'{label}: nie znaleziono kolumn „Poz.” i „Razem” w nagłówku')
    let = poz - 1
    ents, cur = [], None
    for ri, r in enumerate(rows):
        if len(r) <= raz:
            continue
        letter = r[let].strip() if isinstance(r[let], str) else r[let]
        if letter == 'a':
            codes = [None if is_blank(r[c]) else r[c] for c in (0, 1, 2)]
            # nazwa stoi w jednej z kolumn między kodami a literą (w pliku 011 - w kolumnie 2)
            name = next((clean_ws(r[c]) for c in range(3, let) if isinstance(r[c], str) and not is_blank(r[c])), None)
            if name is None and isinstance(r[2], str) and not re.fullmatch(r'\d+', r[2].strip() or '0'):
                name = clean_ws(r[2])
            cur = {'codes': codes, 'name': name, 'row': ri + 1, 'last': ri + 1, 'v': {'a': num(r[raz])}}
            ents.append(cur)
        elif letter in ('b', 'c', 'd', 'f', 'g') and cur is not None:
            if letter in cur['v']:
                raise BuildError(f'{label}: powtórzona litera {letter!r} w bloku z wiersza {cur["row"]}')
            cur['v'][letter] = num(r[raz])
            cur['last'] = ri + 1
        elif is_blank(letter) and cur is not None and 'g' in cur['v'] and ri + 1 == cur['last'] + 1 \
                and isinstance(r[raz], (int, float)):
            # nieopisany piąty wiersz w arkuszu rezerw - musi być zerem
            if abs(r[raz]) > TOL:
                raise BuildError(f'{label}: nieopisany wiersz {ri + 1} w bloku rezerw ma kwotę {r[raz]}')
    return ents


def values_of(ent, reserve=False):
    v = ent['v']
    out = {'plan': v.get('a', 0), 'planAfterChanges': v.get('b', 0), 'actual': v.get('c', 0)}
    if v.get('d'):
        out['carriedOver'] = v['d']
    if reserve:
        if 'c' in v or 'f' not in v or 'g' not in v:
            raise BuildError(f'Arkusz rezerw: nieoczekiwany układ liter w wierszu {ent["row"]}: {sorted(v)}')
        out['reserveAfterChanges'] = v['f']
        out['reserveTransferred'] = v['g']
    return out


def parse_headline(rows, label):
    """Plik 005 „Zestawienie ogólne”: wiersz „2. WYDATKI BUDŻETU PAŃSTWA” (kolumna 1: wg ustawy, kolumna 3: wykonanie)."""
    for r in rows:
        if r and isinstance(r[0], str) and clean_ws(r[0]).upper().startswith('2. WYDATKI BUDŻETU PAŃSTWA'):
            if len(r) < 4 or not isinstance(r[1], (int, float)) or not isinstance(r[3], (int, float)):
                raise BuildError(f'{label}: wiersz „2. WYDATKI BUDŻETU PAŃSTWA” bez kwot w kolumnach 1 i 3')
            return {'plan': num(r[1]), 'actualWithCarriedOver': num(r[3])}
    raise BuildError(f'{label}: brak wiersza „2. WYDATKI BUDŻETU PAŃSTWA”')


def load_year(year, zpath):
    """Czyta wszystkie arkusze wydatków z jednego rocznego ZIP-a. Zwraca (części, ogółem, działy_011, pliki, nagłówek_005)."""
    toms = {}
    parts, files = {}, {}
    total, dzial_totals, headline = None, {}, None
    for key, tom, pattern, _desc in FILES:
        if tom not in toms:
            toms[tom] = open_tom(zpath, tom)
        inner_name, inner = toms[tom]
        info, base = find_member(inner, pattern)
        data = inner.read(info)
        sheets = read_sheets(data, base)
        if len(sheets) != 1:
            raise BuildError(f'{year}/{base}: oczekiwano 1 arkusza, jest {len(sheets)}')
        sheet_name, rows = sheets[0]
        label = f'{year}/{base}'
        files[key] = {'innerZip': inner_name, 'file': base, 'sheet': sheet_name,
                      'fileSha256': hashlib.sha256(data).hexdigest()}
        if key == '005':
            headline = parse_headline(rows, label)
            continue
        ents = parse_sheet(rows, label)
        if key == '011':
            for e in ents:
                c0, c1 = e['codes'][0], e['codes'][1]
                if isinstance(c1, str) and c1.strip().upper() == 'OGÓŁEM':
                    total = values_of(e)
                elif c0 is not None:
                    dzial_totals[norm_code(c0, 3)] = values_of(e)
            if total is None:
                raise BuildError(f'{label}: brak wiersza OGÓŁEM')
            continue
        reserve = key == '013'
        cur = dz = None
        for e in ents:
            c0, c1, c2 = e['codes']
            if c0 is not None:
                code = norm_part(c0)
                if code in parts:
                    raise BuildError(f'{label}: część {code} występuje drugi raz (wcześniej w {parts[code]["fileKey"]})')
                cur = {'code': code, 'nameInSource': e['name'], 'fileKey': key, 'firstRow': e['row'], 'lastRow': e['last'],
                       'values': values_of(e, reserve), 'dzialy': [], 'reserve': reserve}
                parts[code] = cur
                dz = None
            elif cur is None:
                raise BuildError(f'{label}: wiersz {e["row"]} przed pierwszą częścią')
            elif c1 is not None:
                dz = {'dzial': norm_code(c1, 3), 'name': e['name'], 'values': values_of(e, reserve), 'rozdzialy': []}
                cur['dzialy'].append(dz)
                cur['lastRow'] = e['last']
            elif c2 is not None:
                if dz is None:
                    raise BuildError(f'{label}: rozdział w wierszu {e["row"]} bez działu')
                dz['rozdzialy'].append({'rozdzial': norm_code(c2, 5), 'name': e['name'], 'values': values_of(e, reserve)})
                cur['lastRow'] = e['last']
            else:
                cur['lastRow'] = e['last']  # pozycje rezerw celowych (bez kodu)
    return parts, total, dzial_totals, files, headline


COLS = ('plan', 'planAfterChanges', 'actual', 'carriedOver')

# Znane niespójności w samych arkuszach MF. Każda jest sprawdzana co do złotówki: jeśli rozbieżność
# zniknie albo zmieni wartość, skrypt się wywróci. Nie dotyczą kwot części, tylko podziału na działy.
KNOWN_SOURCE_ISSUES = {
    (2023, '83', 'plan'): {
        'dzial': '758', 'excess': 16163834,
        'note': 'Arkusz rezerw za 2023 r. (rok nowelizacji ustawy budżetowej): w kolumnie „a” drugi blok działu 758 '
                '(rezerwy dodane w trakcie roku, 16 163 834 tys. zł) nie wchodzi do kwoty części 83 (65 444 572 tys. zł), '
                'choć w kolumnach f, g i b wchodzi. Kwota części zgadza się z wierszem OGÓŁEM i z plikiem 011; '
                'niespójny jest tylko podział planu części 83 na działy, którego budget.json nie zawiera.'},
}


def validate_year(year, parts, total, dzial_totals, headline=None):
    """Twarda walidacja: sumy części = OGÓŁEM, podczęści = część macierzysta, działy = część, działy = plik 011,
    OGÓŁEM = oficjalna kwota z zestawienia ogólnego (plik 005)."""
    top = [c for c in parts if '/' not in c]
    report = {}
    if headline is not None:
        if not close(headline['plan'], total.get('plan', 0)):
            raise BuildError(f'{year}: plan w zestawieniu ogólnym (005) {headline["plan"]} != OGÓŁEM (011) {total.get("plan", 0)}')
        both = total.get('actual', 0) + total.get('carriedOver', 0)
        if not close(headline['actualWithCarriedOver'], both, 0.01):
            raise BuildError(f'{year}: wydatki w zestawieniu ogólnym (005) {headline["actualWithCarriedOver"]} != wykonanie + niewygasające {both}')
        report['headline005'] = {'plan': headline['plan'], 'actualWithCarriedOver': headline['actualWithCarriedOver'],
                                 'actualPlusCarriedOverFrom011': num(both)}
    for col in COLS:
        s = sum(parts[c]['values'].get(col, 0) for c in top)
        t = total.get(col, 0)
        report[col] = {'sumOfParts': num(s), 'sourceTotal': num(t), 'diff': num(s - t)}
        if not close(s, t):
            raise BuildError(f'{year}: suma części ({col}) = {s:.5f}, a wiersz OGÓŁEM = {t:.5f} (różnica {s - t:.5f})')
    for parent in sorted({c.split('/')[0] for c in parts if '/' in c}):
        if parent not in parts:
            raise BuildError(f'{year}: podczęści {parent}/xx bez części macierzystej')
        for col in COLS:
            s = sum(p['values'].get(col, 0) for c, p in parts.items() if c.startswith(parent + '/'))
            if not close(s, parts[parent]['values'].get(col, 0)):
                raise BuildError(f'{year}: suma podczęści {parent}/xx ({col}) = {s:.5f} != część {parent} = {parts[parent]["values"].get(col, 0):.5f}')
    excess, known = {}, []
    for c, p in parts.items():
        for col in COLS:
            s = sum(d['values'].get(col, 0) for d in p['dzialy'])
            if not close(s, p['values'].get(col, 0)):
                issue = KNOWN_SOURCE_ISSUES.get((year, c, col))
                if issue and close(s - p['values'].get(col, 0), issue['excess']):
                    excess[(issue['dzial'], col)] = excess.get((issue['dzial'], col), 0) + issue['excess']
                    known.append({'year': year, 'part': c, 'column': col, 'excess': issue['excess'], 'note': issue['note']})
                    continue
                raise BuildError(f'{year}: część {c}: suma działów ({col}) = {s:.5f} != kwota części {p["values"].get(col, 0):.5f}')
    for (yy, c, col), issue in KNOWN_SOURCE_ISSUES.items():
        if yy == year and not any(k['part'] == c and k['column'] == col for k in known):
            raise BuildError(f'{year}: znana niespójność źródła (część {c}, {col}) już nie występuje - usuń ją z KNOWN_SOURCE_ISSUES')
        for d in p['dzialy']:
            if d['rozdzialy']:
                for col in COLS:
                    s = sum(r['values'].get(col, 0) for r in d['rozdzialy'])
                    if not close(s, d['values'].get(col, 0)):
                        raise BuildError(f'{year}: część {c} dział {d["dzial"]}: suma rozdziałów ({col}) = {s:.5f} != {d["values"].get(col, 0):.5f}')
    by_dzial = {}
    for c in top:
        for d in parts[c]['dzialy']:
            acc = by_dzial.setdefault(d['dzial'], dict.fromkeys(COLS, 0))
            for col in COLS:
                acc[col] += d['values'].get(col, 0)
    if set(by_dzial) != set(dzial_totals):
        raise BuildError(f'{year}: zbiór działów w częściach różni się od pliku 011: {sorted(set(by_dzial) ^ set(dzial_totals))}')
    for dz, acc in by_dzial.items():
        for col in COLS:
            mine = acc[col] - excess.get((dz, col), 0)
            if not close(mine, dzial_totals[dz].get(col, 0), 0.01):
                raise BuildError(f'{year}: dział {dz} ({col}): suma po częściach {mine:.5f} != plik 011 {dzial_totals[dz].get(col, 0):.5f}')
    report['knownSourceIssues'] = known
    return report


# ---------------------------------------------------------------------------------------------
# 6. PDF: nazwy części (rozporządzenie), plan 2026 (ustawa budżetowa), drugi odczyt (PDF sprawozdania)
# ---------------------------------------------------------------------------------------------
def pdf_text(pdf_path):
    """Tekst PDF w układzie kolumnowym; wynik trzymamy obok PDF-a jako .txt."""
    txt = pdf_path.with_suffix('.layout.txt')
    if txt.exists() and txt.stat().st_mtime >= pdf_path.stat().st_mtime:
        return txt.read_text(encoding='utf-8')
    exe = shutil.which('pdftotext')
    if exe is None:
        return None
    res = subprocess.run([exe, '-layout', str(pdf_path), str(txt)], capture_output=True, text=True)
    if res.returncode != 0:
        raise BuildError(f'pdftotext nie przetworzył {pdf_path.name}: {res.stderr.strip()}')
    return txt.read_text(encoding='utf-8')


def parse_classification_names(text):
    """Urzędowe nazwy części z § 1 rozporządzenia o klasyfikacji części budżetowych."""
    names, block = {}, None
    for raw in text.split('\n'):
        line = raw.strip()
        if line.startswith('§ 2.'):
            break
        m = re.match(r'^(\d{2})/00\s+(\S.*)$', line)
        if m:
            block = m.group(1)
            names[block] = clean_ws(m.group(2))
            continue
        if block and line.startswith('a nazwę części'):
            block = None
            continue
        m = re.match(r'^(\d{2})\.(?:\d\))?\s+(\S.*?),?$', line)
        if m:
            code, name = m.group(1), clean_ws(m.group(2))
            if name.startswith('(uchylon'):
                continue
            names[f'{block}/{code}' if block else code] = name
    return names


NUM_RE = re.compile(r'^\d{1,3}(?: \d{3})*$')


def to_int(tok):
    return int(tok.replace(' ', ''))


def parse_plan(text, year):
    """Załącznik nr 2 do ustawy budżetowej: plan wydatków według części (i działów - do walidacji)."""
    m = re.search(r'łączną kwotę wydatków budżetu państwa w wysokości ([\d  ]+) tys\. zł', text)
    if not m:
        raise BuildError('ustawa budżetowa: nie znaleziono kwoty wydatków w art. 1')
    statutory = to_int(clean_ws(m.group(1)))
    lines = text.split('\n')
    start = next(i for i, l in enumerate(lines) if re.search(r'Załącznik nr 2\b', l))
    end = next(i for i, l in enumerate(lines) if i > start and re.search(r'Załącznik nr 3\b', l))

    def clean(l):
        l = l.replace('﻿', ' ')
        l = re.sub(r'–\s*\d+\s*–', ' ', l)
        l = re.sub(r'Dziennik Ustaw|Poz\. \d+', ' ', l)
        return l.rstrip()

    body = [clean(l) for l in lines[start:end]]
    part_re = re.compile(r'^\s{0,3}(\d{2}(?:/\d{2})?)\s{2,}(\S.*)$')
    dzial_re = re.compile(r'^\s{4,12}(\d{3})\s{2,}(\S.*)$')
    rozdz_re = re.compile(r'^\s{8,22}(\d{5})\s{2,}\S')
    summary_re = re.compile(r'^\s{0,2}(\d{3})\s{2,}(\S.*)$')

    def amount_after_poz(tokens, want_poz=None):
        """W tokenach (rozdzielonych >= 2 spacjami) szuka pary: Poz., kwota planu."""
        for i in range(len(tokens) - 1):
            if re.fullmatch(r'\d{1,3}', tokens[i]) and NUM_RE.match(tokens[i + 1]):
                if want_poz is None or int(tokens[i]) == want_poz:
                    return int(tokens[i]), to_int(tokens[i + 1])
        return None

    def find_amount(idx, first_tokens, want_poz=None):
        got = amount_after_poz(first_tokens, want_poz)
        j = idx
        while got is None and j + 1 < len(body) and j < idx + 4:
            j += 1
            nxt = body[j]
            if part_re.match(nxt) or dzial_re.match(nxt) or rozdz_re.match(nxt):
                break
            if nxt.strip():
                got = amount_after_poz(re.split(r'\s{2,}', nxt.strip()), want_poz)
        return got

    summary, total, parts, cur = {}, None, {}, None
    in_summary = True
    for idx, line in enumerate(body):
        if not line.strip():
            continue
        pm = part_re.match(line)
        if pm and not re.search(r'[a-ząćęłńóśźż]', re.split(r'\s{2,}', pm.group(2))[0]):
            in_summary = False
            code = pm.group(1)
            got = find_amount(idx, re.split(r'\s{2,}', pm.group(2).strip())[1:], want_poz=1)
            if got is None:
                raise BuildError(f'plan {year}: część {code}: nie znaleziono kwoty (Poz. 1)')
            if code in parts:
                raise BuildError(f'plan {year}: część {code} występuje drugi raz')
            cur = {'plan': got[1], 'dzialy': {}}
            parts[code] = cur
            continue
        if in_summary:
            sm = summary_re.match(line)
            if sm:
                toks = re.split(r'\s{2,}', sm.group(2).strip())
                nums = [t for t in toks[1:] if NUM_RE.match(t)]
                if nums:
                    summary[sm.group(1)] = to_int(nums[0])
            elif re.match(r'^\s*Ogółem\s', line):
                toks = re.split(r'\s{2,}', line.strip())
                total = to_int(toks[1])
            continue
        dm = dzial_re.match(line)
        if dm and cur is not None and not rozdz_re.match(line):
            got = find_amount(idx, re.split(r'\s{2,}', dm.group(2).strip())[1:])
            if got is None:
                raise BuildError(f'plan {year}: dział {dm.group(1)}: nie znaleziono kwoty (linia {start + idx + 1})')
            cur['dzialy'][dm.group(1)] = cur['dzialy'].get(dm.group(1), 0) + got[1]

    checks = []
    if total is None:
        raise BuildError(f'plan {year}: brak wiersza „Ogółem” w zestawieniu zbiorczym')
    top = [c for c in parts if '/' not in c]
    s = sum(parts[c]['plan'] for c in top)
    checks.append(('kwota z art. 1 ustawy = wiersz „Ogółem” załącznika', statutory, total))
    checks.append(('suma części = wiersz „Ogółem”', s, total))
    for parent in sorted({c.split('/')[0] for c in parts if '/' in c}):
        checks.append((f'suma podczęści {parent}/xx = część {parent}',
                       sum(p['plan'] for c, p in parts.items() if c.startswith(parent + '/')), parts[parent]['plan']))
    bad_dz = [c for c, p in parts.items() if sum(p['dzialy'].values()) != p['plan']]
    checks.append(('liczba części, w których suma działów != plan części', len(bad_dz), 0))
    by_dz = {}
    for c in top:
        for dz, v in parts[c]['dzialy'].items():
            by_dz[dz] = by_dz.get(dz, 0) + v
    checks.append(('liczba działów niezgodnych z zestawieniem zbiorczym',
                   len([d for d in set(by_dz) | set(summary) if by_dz.get(d) != summary.get(d)]), 0))
    failed = [f'{name}: {a} != {b}' for name, a, b in checks if a != b]
    if bad_dz:
        failed.append('części z niezgodną sumą działów: ' + ', '.join(sorted(bad_dz)))
    return {'statutory': statutory, 'total': total, 'parts': parts, 'failed': failed,
            'checks': [{'check': n, 'left': a, 'right': b, 'ok': a == b} for n, a, b in checks]}


def second_read(year, zpath, parts, sample):
    """Drugi, niezależny odczyt: te same kwoty z PDF sprawozdania (inny plik, inny format, inny parser).
    PDF podaje pełne tys. zł, więc porównujemy z zaokrągleniem (tolerancja 1 tys. zł)."""
    z = zipfile.ZipFile(zpath)
    texts = {}
    for info in z.infolist():
        name = zip_name(info)
        if name.lower().endswith('.pdf'):
            tom = 2 if re.search(r'TOM II\b', name.upper()) else 1
            pdf = SRC_DIR / f'_sprawozdanie{year}-tom{tom}.pdf'
            if not pdf.exists() or pdf.stat().st_size != info.file_size:
                pdf.write_bytes(z.read(info))
            texts[tom] = (name, pdf_text(pdf))
    if not texts or any(t is None for _, t in texts.values()):
        return None
    results = []
    for code in sample:
        tom = 2 if code.startswith('85/') else 1
        if tom not in texts:
            results.append({'code': code, 'status': 'brak PDF'})
            continue
        lines = texts[tom][1].split('\n')
        head = re.compile(r'^\s{0,4}' + re.escape(code) + r'\s{2,}[A-ZĄĆĘŁŃÓŚŹŻ]')
        found = None
        for i, l in enumerate(lines):
            if not head.match(l):
                continue
            for j in range(i, min(i + 4, len(lines))):
                m = re.search(r'\sa\s+1\s+(\d{1,3}(?: \d{3})*)(?=\s{2,}|$)', lines[j])
                if m:
                    found = (j, to_int(m.group(1)))
                    break
                if re.search(r'\sa\s+1\s*$', lines[j]):
                    found = (j, 0)   # część z zerowym planem (np. 91): PDF zostawia pustą komórkę
                    break
            if found:
                break
        if not found:
            results.append({'code': code, 'status': 'nie znaleziono wiersza w PDF'})
            continue
        j, plan_pdf = found
        got = {'a': plan_pdf}
        for k in range(j + 1, min(j + 6, len(lines))):
            if re.search(r'\sa\s+\d+(\s|$)', lines[k]):
                break  # początek następnej pozycji (dział)
            # litera może stać za dalszym ciągiem zawiniętej nazwy części (np. „TERYTORIALNEGO    b   50 770 513”)
            m = re.match(r'^\s+(?:\S.*?\s{2,})?([bcdfg])(?:\s+(\d{1,3}(?: \d{3})*))?(?=\s{2,}|\s*$)', lines[k])
            if m and m.group(1) not in got:
                got[m.group(1)] = to_int(m.group(2)) if m.group(2) else 0
        v = parts[code]['values']
        expect = {'a': v['plan'], 'b': v['planAfterChanges']}
        if not parts[code]['reserve']:
            expect['c'] = v['actual']
        diffs = {}
        for letter, val in expect.items():
            if letter not in got:
                diffs[letter] = {'arkusz': val, 'pdf': None}
            elif abs(round(val) - got[letter]) > 1:
                diffs[letter] = {'arkusz': val, 'pdf': got[letter]}
        results.append({'code': code, 'pdfFile': texts[tom][0], 'pdfLine': j + 1,
                        'pdf': {'plan': got.get('a'), 'planAfterChanges': got.get('b'), 'actual': got.get('c')},
                        'status': 'zgodne' if not diffs else 'RÓŻNICA', 'diffs': diffs})
    return results


# ---------------------------------------------------------------------------------------------
# 7. SKŁADANIE WYNIKU
# ---------------------------------------------------------------------------------------------
def check_minister_acts(offline):
    """Pobiera rozporządzenia o zakresie działania ministrów i sprawdza zdanie o dysponowaniu częściami."""
    results = []
    for act in MINISTER_ACTS:
        _du, yr, pos = act['eli'].split('/')
        fname = f'D{yr}{int(pos):04d}.pdf'
        url = f'https://api.sejm.gov.pl/eli/acts/{act["eli"]}/text/O/{fname}'
        path, digest, _ = fetch(url, SRC_DIR / 'zakresy' / fname, offline)
        text = pdf_text(path)
        if text is None:
            results.append({'eli': act['eli'], 'status': 'nie sprawdzono (brak pdftotext)'})
            continue
        flat = re.sub(r'\s+', ' ', re.sub(r'-\n\s*', '', text))
        title = re.search(r'szczegółowego zakresu działania (Ministra .+?) Na podstawie', flat)
        m = re.search(r'Minister jest dysponentem części ([\d, i]+) budżetu państwa', flat)
        if not m:
            raise BuildError(f'{act["eli"]}: brak zdania „Minister jest dysponentem części ...”')
        found = sorted(f'{int(x):02d}' for x in re.findall(r'\d+', m.group(1)))
        expected = sorted(act['office'])
        if found != expected:
            raise BuildError(f'{act["eli"]}: akt wymienia części {found}, tabela w skrypcie {expected}')
        results.append({'eli': act['eli'], 'url': f'https://eli.gov.pl/eli/{act["eli"]}/ogl', 'sha256': digest,
                        'minister': act['minister'], 'titleInAct': clean_ws(title.group(1)) if title else None,
                        'parts': found, 'status': 'zgodne'})
    return results


def stems(s):
    return {w[:5] for w in re.findall(r'[a-ząćęłńóśźż]+', s.lower()) if len(w) > 3}


def assign_nodes(parts, names, nodes):
    """Wypełnia nodeId / dysponent dla każdej części. Niczego nie zgaduje: źródłem jest akt albo nazwa."""
    by_part = {}
    for act in MINISTER_ACTS:
        for code, office in act['office'].items():
            by_part[code] = {'nodeId': office, 'dysponent': act['minister'], 'dysponentNodeId': act['position'],
                             'dysponentVerified': True,
                             'dysponentBasis': f'rozporządzenie Prezesa RM o szczegółowym zakresie działania ({act["eli"].replace("DU/", "Dz.U. ").replace("/", " poz. ")}): „Minister jest dysponentem części …”'}
    ministers = {a['eli']: a for a in MINISTER_ACTS}
    for code, (eli, basis) in CLASSIFICATION_DISPOSERS.items():
        a = ministers[eli]
        by_part[code] = {'nodeId': CLASSIFICATION_OFFICE[code], 'dysponent': a['minister'], 'dysponentNodeId': a['position'],
                         'dysponentVerified': True,
                         'dysponentBasis': f'{basis}; działem kieruje {a["minister"]} ({eli.replace("DU/", "Dz.U. ").replace("/", " poz. ")})'}
    for code, node in INSTITUTION_NODES.items():
        head = nodes[node].get('head') if node in nodes else None
        if code == '15/01':
            a = ministers['DU/2025/1005']
            by_part[code] = {'nodeId': node, 'dysponent': a['minister'], 'dysponentNodeId': a['position'], 'dysponentVerified': True,
                             'dysponentBasis': '§ 1 rozp. o klasyfikacji części: nazwę podczęści stanowi nazwa jednostki właściwej dla dysponenta części „Sądy powszechne”, czyli Ministerstwo Sprawiedliwości (§ 2 ust. 2 pkt 1: dysponentem części 15/00 jest Minister Sprawiedliwości)'}
            continue
        by_part[code] = {'nodeId': node, 'dysponent': nodes[head]['name'] if head in nodes else None,
                         'dysponentNodeId': head if head in nodes else None, 'dysponentVerified': False,
                         'dysponentBasis': 'kierownik jednostki, dla której utworzono część (art. 2 pkt 8 ustawy o finansach publicznych); nazwa stanowiska z pola head węzła w grafie, niezweryfikowana w akcie szczegółowym'}
    for code, (office, voivode) in VOIVODESHIP_NODES.items():
        by_part[code] = {'nodeId': office, 'dysponent': nodes[voivode]['name'] if voivode in nodes else None,
                         'dysponentNodeId': voivode, 'dysponentVerified': True,
                         'dysponentBasis': 'wojewoda jest dysponentem części budżetowej (art. 2 pkt 8 ustawy o finansach publicznych); województwo wg nazwy podczęści w rozp. o klasyfikacji części'}
    by_part['81'] = {'nodeId': None, 'dysponent': 'Rada Ministrów', 'dysponentNodeId': 'pl-rada-ministrow', 'dysponentVerified': True,
                     'dysponentBasis': 'art. 155 ust. 1 ustawy o finansach publicznych: „Rezerwą ogólną dysponuje Rada Ministrów”'}
    by_part['83'] = {'nodeId': None, 'dysponent': ministers['DU/2025/997']['minister'], 'dysponentNodeId': ministers['DU/2025/997']['position'],
                     'dysponentVerified': True,
                     'dysponentBasis': 'art. 154 ust. 1 ustawy o finansach publicznych: podziału rezerw celowych dokonuje Minister Finansów w porozumieniu z dysponentami części'}
    empty = {'nodeId': None, 'dysponent': None, 'dysponentNodeId': None, 'dysponentVerified': False, 'dysponentBasis': None}
    warnings = []
    for code, p in parts.items():
        info = dict(by_part.get(code, empty))
        p.update(info)
        for key in ('nodeId', 'dysponentNodeId'):
            if p[key] is not None and p[key] not in nodes:
                raise BuildError(f'część {code}: {key} = {p[key]} nie istnieje w graph.json')
        # strażnik „nie zgaduj”: nazwa części powinna się zawierać w nazwie węzła (rdzenie słów)
        if p['nodeId'] and (code in INSTITUTION_NODES or code in VOIVODESHIP_NODES) and code != '15/01':
            n = nodes[p['nodeId']]
            hay = stems(' '.join([n['name'], n.get('shortName') or ''] + list(n.get('aliases') or [])))
            need = stems(names.get(code, p['nameInSource']))
            missing = need - hay
            if missing and code not in NAME_MATCH_EXCEPTIONS:
                warnings.append(f'część {code} „{names.get(code)}” -> {p["nodeId"]} „{n["name"]}”: w nazwie węzła brak rdzeni {sorted(missing)}')
    return warnings


def assign_groups(parts):
    for code, p in parts.items():
        if '/' in code:
            continue
        metric = 'actual' if p['values']['actual'] > 0 else 'plan'
        if not p['dzialy']:
            raise BuildError(f'część {code}: brak działów')
        top = max(p['dzialy'], key=lambda d: (d['values'][metric], d['dzial']))
        if top['dzial'] not in DZIAL_TO_GROUP:
            raise BuildError(f'Dział {top["dzial"]} „{top["name"]}” nie ma grupy - dopisz go do DZIAL_TO_GROUP')
        group = DZIAL_TO_GROUP[top['dzial']]
        basis = {'dzial': top['dzial'], 'dzialName': top['name'], 'metric': metric,
                 'share': round(top['values'][metric] / p['values'][metric], 4) if p['values'][metric] else None}
        if group is None:
            rz = max(top['rozdzialy'], key=lambda r: (r['values'][metric], r['rozdzial']))
            if rz['rozdzial'] not in ROZDZIAL_758_TO_GROUP:
                raise BuildError(f'Rozdział {rz["rozdzial"]} „{rz["name"]}” (część {code}) nie ma grupy - dopisz go do ROZDZIAL_758_TO_GROUP')
            group = ROZDZIAL_758_TO_GROUP[rz['rozdzial']]
            basis.update({'rozdzial': rz['rozdzial'], 'rozdzialName': rz['name']})
        p['group'], p['groupBasis'] = group, basis
    for code, p in parts.items():
        if '/' in code:
            parent = parts[code.split('/')[0]]
            p['group'] = parent['group']
            p['groupBasis'] = {'inheritedFrom': parent['code']}


def main():
    ap = argparse.ArgumentParser(description='Buduje data/pl/budget.json z urzędowych źródeł.')
    ap.add_argument('--offline', action='store_true', help='używaj wyłącznie pamięci podręcznej data/pl/budget-src/')
    ap.add_argument('--accept-changed', action='store_true', help='nie przerywaj, gdy suma SHA-256 pliku źródłowego się zmieniła')
    ap.add_argument('--date', help='data do meta.generatedAt (domyślnie dzisiejsza)')
    ap.add_argument('--list-resources', action='store_true', help='wypisz zasoby zbioru 163 z API dane.gov.pl i zakończ')
    args = ap.parse_args()
    SRC_DIR.mkdir(parents=True, exist_ok=True)

    if args.list_resources:
        req = urllib.request.Request(DATASET_API, headers={'User-Agent': UA, 'Accept-Language': 'pl'})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        for res in data['data']:
            a = res['attributes']
            print(res['id'], '|', a.get('title'), '|', a.get('format'), '|', a.get('file_size'), '|', a.get('data_date'), '|', a.get('download_url'))
        return 0

    generated = args.date or datetime.date.today().isoformat()
    nodes = json.loads(GRAPH.read_text(encoding='utf-8'))['nodes']
    sources, verification = [], {}

    # --- 7.1 wykonanie budżetu: wszystkie lata --------------------------------------------------
    log('== Sprawozdania z wykonania budżetu państwa (dane.gov.pl, zbiór 163)')
    years_data, totals = {}, {}
    for year in sorted(YEARS, reverse=True):
        y = YEARS[year]
        zpath, digest, retrieved = fetch(y['url'], SRC_DIR / y['zip'], args.offline, y['sha256'], args.accept_changed)
        parts_y, total, dzial_totals, files, headline = load_year(year, zpath)
        rep = validate_year(year, parts_y, total, dzial_totals, headline)
        years_data[year] = parts_y
        totals[str(year)] = {k: num(v) for k, v in total.items()}
        totals[str(year)]['actualWithCarriedOver'] = headline['actualWithCarriedOver']
        verification.setdefault('totals', {})[str(year)] = rep
        top = [c for c in parts_y if '/' not in c]
        log(f'  {year}: części {len(top)}, podczęści {len(parts_y) - len(top)}; '
            f'plan {total["plan"]:,.0f} | po zmianach {total["planAfterChanges"]:,.0f} | wykonanie {total["actual"]:,.2f} '
            f'| niewygasające {total.get("carriedOver", 0):,.2f}  -> sumy części = OGÓŁEM, podczęści = część, działy = część, działy = plik 011, OGÓŁEM = zestawienie ogólne (005): OK'.replace(',', ' '))
        for k in rep['knownSourceIssues']:
            log(f'    znana niespójność arkusza MF ({k["year"]}, część {k["part"]}, kolumna {k["column"]}, nadwyżka działów {k["excess"]}): potwierdzona co do kwoty')
        for key, _tom, _pat, desc in FILES:
            f = files[key]
            sources.append({'id': f'wyk{year}-{key}',
                            'title': f'Sprawozdanie z wykonania budżetu państwa za {year} r., część tabelaryczna: {desc}',
                            'publisher': 'Ministerstwo Finansów', 'datasetUrl': DATASET_URL, 'url': y['url'],
                            'zip': y['zip'], 'sha256': digest, 'innerZip': f['innerZip'], 'file': f['file'], 'sheet': f['sheet'],
                            'fileSha256': f['fileSha256'], 'license': LICENSE_DANE, 'retrievedAt': retrieved})

    cur = years_data[CURRENT_YEAR]

    # --- 7.2 urzędowe nazwy części ---------------------------------------------------------------
    log('== Rozporządzenie o klasyfikacji części budżetowych (nazwy części)')
    act = ACTS['klasyfikacja']
    kpath, kdigest, kretr = fetch(act['url'], SRC_DIR / act['file'], args.offline, act['sha256'], args.accept_changed)
    ktext = pdf_text(kpath)
    names = parse_classification_names(ktext) if ktext else {}
    sources.append({'id': 'klasyfikacja', 'title': act['title'], 'publisher': 'Dziennik Ustaw / Sejm RP (ELI)', 'url': act['url'],
                    'page': act['page'], 'file': act['file'], 'sheet': None, 'sha256': kdigest, 'license': LICENSE_ACT, 'retrievedAt': kretr})
    name_mismatch = []
    for code, p in cur.items():
        official = names.get(code)
        if official is None:
            name_mismatch.append(f'{code}: brak w rozporządzeniu, zostaje nazwa z arkusza „{p["nameInSource"]}”')
            p['name'] = p['nameInSource']
        else:
            if norm_name(official) != norm_name(p['nameInSource']):
                name_mismatch.append(f'{code}: rozporządzenie „{official}” / arkusz „{p["nameInSource"]}”')
            p['name'] = official
    if not names:
        log('  UWAGA: brak pdftotext - nazwy części wzięte z arkusza (wersaliki)')
    log(f'  nazwy z rozporządzenia: {len(names)}; części w danych {CURRENT_YEAR}: {len(cur)}; rozbieżności nazw: {len(name_mismatch)}')
    for m in name_mismatch:
        log('    - ' + m)
    verification['nameMismatches'] = name_mismatch

    # --- 7.3 dysponenci i węzły --------------------------------------------------------------------
    log('== Dysponenci części (rozporządzenia Prezesa RM o zakresie działania ministrów)')
    acts_report = check_minister_acts(args.offline)
    for r in acts_report:
        log(f'  {r["eli"]}: {r.get("minister", "")} -> części {", ".join(r.get("parts", []))}: {r["status"]}')
    verification['ministerActs'] = acts_report
    warnings = assign_nodes(cur, names, nodes)
    if warnings:
        raise BuildError('Przypisanie po nazwie nie ma pokrycia w nazwie węzła (dodaj uzasadniony wyjątek do NAME_MATCH_EXCEPTIONS albo popraw):\n  '
                         + '\n  '.join(warnings))
    log(f'  przypisania po nazwie (instytucje i województwa): {len(INSTITUTION_NODES) + len(VOIVODESHIP_NODES) - 1} sprawdzonych z nazwami węzłów, bez zastrzeżeń')

    # --- 7.4 grupy -----------------------------------------------------------------------------------
    assign_groups(cur)

    # --- 7.5 plan na rok następny ----------------------------------------------------------------------
    log(f'== Ustawa budżetowa na {PLAN_YEAR} r., załącznik nr 2')
    plan_year, plan_note, plan = PLAN_YEAR, None, None
    act = ACTS['ub2026']
    try:
        upath, udigest, uretr = fetch(act['url'], SRC_DIR / act['file'], args.offline, act['sha256'], args.accept_changed)
        utext = pdf_text(upath)
        if utext is None:
            raise BuildError('brak programu pdftotext (poppler), nie da się odczytać załącznika z PDF')
        plan = parse_plan(utext, PLAN_YEAR)
        for c in plan['checks']:
            log(f'  {"OK " if c["ok"] else "ŹLE"} {c["check"]}: {c["left"]:,} / {c["right"]:,}'.replace(',', ' '))
        if plan['failed']:
            raise BuildError('walidacja załącznika nr 2 nie przeszła: ' + '; '.join(plan['failed']))
        sources.append({'id': 'ub2026', 'title': act['title'], 'publisher': 'Dziennik Ustaw / Sejm RP (ELI)', 'url': act['url'],
                        'page': act['page'], 'file': act['file'], 'sheet': 'załącznik nr 2 (PDF, odczyt: pdftotext -layout)',
                        'sha256': udigest, 'license': LICENSE_ACT, 'retrievedAt': uretr})
        totals[str(PLAN_YEAR)] = {'plan': plan['total']}
        verification['plan'] = {'year': PLAN_YEAR, 'checks': plan['checks']}
    except BuildError as e:
        plan_year, plan, plan_note = None, None, f'Planu na {PLAN_YEAR} r. nie przyjęto: {e}'
        log('  UWAGA: ' + plan_note)

    # --- 7.6 budowa wpisów części ------------------------------------------------------------------------
    out_parts = {}
    history_years = sorted(y for y in YEARS if y != CURRENT_YEAR)
    for code in sorted(cur):
        p = cur[code]
        years = {str(CURRENT_YEAR): p['values']}
        notes = []
        for y in history_years:
            old = years_data[y].get(code)
            if old is None:
                continue
            entry = dict(old['values'])
            if norm_name(old['nameInSource']) != norm_name(p['nameInSource']):
                entry['nameInSource'] = old['nameInSource']
            years[str(y)] = entry
        missing = [y for y in history_years if str(y) not in years]
        if missing:
            notes.append(f'Brak części w sprawozdaniach za: {", ".join(map(str, missing))} (część jeszcze nie istniała).')
        renamed = sorted({(y, v['nameInSource']) for y, v in years.items() if 'nameInSource' in v})
        if renamed:
            old_names = sorted({n for _, n in renamed})
            yrs = ', '.join(y for y, _ in renamed)
            notes.append(f'W latach {yrs} część o tym numerze nosiła nazwę „{"” / „".join(old_names)}”. Zakres mógł się różnić; szeregu nie korygowano.')
        if plan and code in plan['parts']:
            years[str(PLAN_YEAR)] = {'plan': plan['parts'][code]['plan']}
        elif plan:
            notes.append(f'Części nie ma w załączniku nr 2 do ustawy budżetowej na {PLAN_YEAR} r.')
        if p['reserve']:
            notes.append('Rezerwy nie mają wykonania: są przenoszone do innych części i tam widać je w wykonaniu. '
                         '„planAfterChanges” to pozostałość rezerwy po przeniesieniach; „reserveAfterChanges” to rezerwa po zmianach, '
                         '„reserveTransferred” to kwota przeniesiona do innych części.')
        if code in PART_NOTES:
            notes.append(PART_NOTES[code])
        if p['nodeId'] is None:
            parent = code.split('/')[0]
            reason = NO_NODE_REASON.get(code) or (NO_NODE_SUBPART.get(parent) if '/' in code else None)
            if reason is None:
                raise BuildError(f'część {code}: nodeId = null bez podanego powodu')
            notes.append('Brak węzła: ' + reason)
        children = sorted(c for c in cur if c.startswith(code + '/')) if '/' not in code else None
        entry = {
            'code': code, 'name': p['name'], 'nameInSource': p['nameInSource'],
            'level': 'subpart' if '/' in code else 'part',
            'parent': code.split('/')[0] if '/' in code else None,
            'dysponent': p['dysponent'], 'dysponentNodeId': p['dysponentNodeId'],
            'dysponentVerified': p['dysponentVerified'], 'dysponentBasis': p['dysponentBasis'],
            'nodeId': p['nodeId'], 'group': p['group'], 'groupBasis': p['groupBasis'],
            'years': {k: years[k] for k in sorted(years)},
            'breakdown': [{'dzial': d['dzial'], 'name': d['name'], 'plan': d['values']['plan'],
                           'planAfterChanges': d['values']['planAfterChanges'], 'actual': d['values']['actual']} for d in p['dzialy']],
            'sourceRef': {'source': f'wyk{CURRENT_YEAR}-{p["fileKey"]}', 'rows': f'wiersze {p["firstRow"]}-{p["lastRow"]} arkusza (numeracja Excela)'},
            'note': ' '.join(notes) if notes else None,
        }
        if children:
            entry['children'] = children
        out_parts[code] = entry

    # --- 7.7 grupy i walidacje końcowe ----------------------------------------------------------------------
    top_codes = [c for c in out_parts if '/' not in c]
    groups = []
    for gcode, gname, kind in GROUPS:
        members = sorted(c for c in top_codes if out_parts[c]['group'] == gcode)
        gt = {col: num(sum(out_parts[c]['years'][str(CURRENT_YEAR)][col] for c in members)) for col in ('plan', 'planAfterChanges', 'actual')}
        entry = {'code': gcode, 'name': gname, 'kind': kind, 'parts': members, 'totals': {str(CURRENT_YEAR): gt}}
        if plan:
            entry['totals'][str(PLAN_YEAR)] = {'plan': sum(out_parts[c]['years'].get(str(PLAN_YEAR), {}).get('plan', 0) for c in members)}
        groups.append(entry)
    seen = [c for g in groups for c in g['parts']]
    if sorted(seen) != sorted(top_codes) or len(seen) != len(set(seen)):
        raise BuildError('Grupy: każda część najwyższego poziomu musi należeć do dokładnie jednej grupy')
    if any(not g['parts'] for g in groups):
        raise BuildError('Grupy: pusta grupa ' + ', '.join(g['code'] for g in groups if not g['parts']))
    for col in ('plan', 'planAfterChanges', 'actual'):
        s = sum(g['totals'][str(CURRENT_YEAR)][col] for g in groups)
        if not close(s, totals[str(CURRENT_YEAR)][col]):
            raise BuildError(f'Grupy: suma ({col}) {s} != OGÓŁEM {totals[str(CURRENT_YEAR)][col]}')
    for code, e in out_parts.items():
        for col in ('plan', 'planAfterChanges', 'actual'):
            s = sum(b[col] for b in e['breakdown'])
            if not close(s, e['years'][str(CURRENT_YEAR)][col]):
                raise BuildError(f'breakdown części {code} ({col}): {s} != {e["years"][str(CURRENT_YEAR)][col]}')
    log('== Walidacje końcowe: grupy rozłączne i kompletne, suma grup = OGÓŁEM, breakdown = kwota części (plan, po zmianach, wykonanie): OK')

    # pokrycie węzłami (liście = podczęści tam, gdzie są, inaczej część)
    leaves = [c for c in out_parts if not out_parts[c].get('children')]
    total_actual = totals[str(CURRENT_YEAR)]['actual']
    with_node = sum(out_parts[c]['years'][str(CURRENT_YEAR)]['actual'] for c in leaves if out_parts[c]['nodeId'])
    with_node_top = sum(out_parts[c]['years'][str(CURRENT_YEAR)]['actual'] for c in top_codes if out_parts[c]['nodeId'])
    # część liczy się jako pokryta, gdy sama ma węzeł; w przeciwnym razie liczą się jej podczęści z węzłem
    best = sum(out_parts[c]['years'][str(CURRENT_YEAR)]['actual'] if out_parts[c]['nodeId'] else
               sum(out_parts[k]['years'][str(CURRENT_YEAR)]['actual'] for k in out_parts[c].get('children', []) if out_parts[k]['nodeId'])
               for c in top_codes)
    coverage = {
        'actualShareWithNode_partOrItsSubparts': round(best / total_actual, 4),
        'entries': len(out_parts), 'parts': len(top_codes), 'subparts': len(out_parts) - len(top_codes),
        'withNodeId': sum(1 for e in out_parts.values() if e['nodeId']),
        'partsWithNodeId': sum(1 for c in top_codes if out_parts[c]['nodeId']),
        'subpartsWithNodeId': sum(1 for c in out_parts if '/' in c and out_parts[c]['nodeId']),
        'actualShareWithNode_leaves': round(with_node / total_actual, 4),
        'actualShareWithNode_topLevelOnly': round(with_node_top / total_actual, 4),
        'withoutNodeId': sorted(c for c, e in out_parts.items() if not e['nodeId']),
    }
    verification['nodeCoverage'] = coverage
    log(f'== Węzły: {coverage["withNodeId"]} z {coverage["entries"]} wpisów ma nodeId '
        f'(części {coverage["partsWithNodeId"]}/{coverage["parts"]}, podczęści {coverage["subpartsWithNodeId"]}/{coverage["subparts"]}); '
        f'udział w wykonaniu {CURRENT_YEAR}: {coverage["actualShareWithNode_leaves"]:.2%} (liczone po liściach), '
        f'{coverage["actualShareWithNode_topLevelOnly"]:.2%} (tylko części najwyższego poziomu), '
        f'{coverage["actualShareWithNode_partOrItsSubparts"]:.2%} (część albo jej podczęści)')

    # podpowiedzi budgetPart z grafu
    hint_issues = []
    for nid, n in nodes.items():
        bp = n.get('budgetPart')
        if not bp:
            continue
        for raw in re.split(r'[;,]', bp):
            raw = raw.strip()
            if not raw:
                continue
            code = norm_part(raw)
            e = out_parts.get(code)
            if e is None:
                hint_issues.append(f'{nid}: budgetPart „{raw}” - takiej części nie ma w danych {CURRENT_YEAR}')
                continue
            office_of_disposer = nodes.get(e['dysponentNodeId'] or '', {}).get('headOf')
            if nid not in (e['nodeId'], e['dysponentNodeId'], office_of_disposer):
                hint_issues.append(f'{nid}: budgetPart „{raw}”, a w budget.json część {code} -> nodeId {e["nodeId"]}, dysponent {e["dysponentNodeId"]}')
    hinted = {norm_part(x.strip()) for n in nodes.values() if n.get('budgetPart') for x in re.split(r'[;,]', n['budgetPart']) if x.strip()}
    not_hinted = sorted(c for c, e in out_parts.items() if e['nodeId'] and c not in hinted)
    verification['graphHints'] = {'conflicts': hint_issues, 'partsWithNodeButNoHintInGraph': not_hinted}
    log(f'== Podpowiedzi budgetPart w graph.json: sprzeczności {len(hint_issues)}; części z nodeId bez podpowiedzi w grafie: {", ".join(not_hinted) or "brak"}')
    for h in hint_issues:
        log('    - ' + h)

    # --- 7.8 drugi, niezależny odczyt ------------------------------------------------------------------------
    log(f'== Drugi odczyt: PDF sprawozdania za {CURRENT_YEAR} r. (10 największych części + 15 losowych wpisów)')
    top10 = sorted(top_codes, key=lambda c: -out_parts[c]['years'][str(CURRENT_YEAR)]['actual'])[:10]
    rest = sorted(c for c in out_parts if c not in top10)
    sample = top10 + sorted(random.Random(CURRENT_YEAR).sample(rest, 15))
    sr = second_read(CURRENT_YEAR, SRC_DIR / YEARS[CURRENT_YEAR]['zip'], cur, sample)
    if sr is None:
        log('  UWAGA: drugi odczyt pominięty (brak pdftotext albo PDF w ZIP-ie)')
        verification['secondRead'] = None
    else:
        bad = [r for r in sr if r['status'] != 'zgodne']
        for r in sr:
            v = cur[r['code']]['values']
            log(f'  {r["code"]:6s} arkusz: {v["plan"]:>14,.0f} | {v["planAfterChanges"]:>16,.2f} | {v["actual"]:>16,.2f}   '
                f'PDF: {r.get("pdf", {}).get("plan")!s:>12} | {r.get("pdf", {}).get("planAfterChanges")!s:>12} | {r.get("pdf", {}).get("actual")!s:>12}   {r["status"]}'.replace(',', ' '))
        verification['secondRead'] = {'method': 'pdftotext -layout na PDF Tomu I/II z tego samego ZIP-a; porównanie po zaokrągleniu do 1 tys. zł',
                                      'top10': top10, 'random15': sample[10:], 'seed': CURRENT_YEAR, 'differences': bad,
                                      'checked': len(sr), 'ok': len(sr) - len(bad)}
        log(f'  zgodnych {len(sr) - len(bad)} z {len(sr)}')
        if bad:
            raise BuildError('Drugi odczyt wykazał różnice: ' + json.dumps(bad, ensure_ascii=False))

    meta = {
        'unit': 'tys. zł', 'currentYear': CURRENT_YEAR, 'currentKind': 'wykonanie', 'planYear': plan_year, 'planNote': plan_note,
        'generatedAt': generated, 'historyYears': history_years,
        'columns': {
            'plan': 'budżet według ustawy budżetowej (wiersz „a” sprawozdania); dla roku planu: załącznik nr 2 do ustawy budżetowej',
            'planAfterChanges': 'budżet po zmianach na koniec roku (wiersz „b”)',
            'actual': 'wykonanie (wiersz „c”), bez wydatków niewygasających',
            'carriedOver': 'wydatki, które nie wygasły z upływem roku (wiersz „d”); pole występuje tylko, gdy kwota jest większa od zera',
            'actualWithCarriedOver': 'tylko w meta.totals: oficjalna łączna kwota wydatków z zestawienia ogólnego sprawozdania (plik 005) = actual + carriedOver',
        },
        'precision': 'kwoty z dokładnością źródła: plan w pełnych tys. zł, pozostałe do 5 miejsc po przecinku (grosze); bez przeliczeń',
        'totals': totals, 'sources': sources, 'verification': verification,
    }
    result = {'meta': meta, 'groups': groups, 'parts': out_parts}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    log(f'== Zapisano {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BuildError as e:
        print(f'\nBŁĄD: {e}', file=sys.stderr)
        sys.exit(1)
