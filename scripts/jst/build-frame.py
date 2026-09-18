#!/usr/bin/env python3
"""Rama krajowa samorządu: wszystkie województwa, powiaty, miasta na prawach powiatu i gminy jako małe grafy w schemacie graph.json.
Źródła (wyłącznie urzędowe): arkusze PKW z wyborów samorządowych 7 i 21 kwietnia 2024 r. (jednostki, organy, liczba mandatów, wybrani),
szablony ustrojowe ze sprawdzonymi cytatami ustaw (scripts/jst/templates.json), osoby organów nadzoru z grafu centralnego (data/pl/graph.json),
nakładki z danymi spoza rejestrów (data/jst/overlay/<woj>.json: zarządy, starostowie, przewodniczący rad; tylko rekordy potwierdzone).
Z plików PKW NIE są przenoszone: wiek, wykształcenie, miejsce zamieszkania, płeć, wyniki głosowania.
Wynik (zwarty, bo ustrój jest wspólny dla szczebla): data/jst/tiers.json = szablon grafu dla każdego wariantu jednostki ze znacznikami @@…@@,
 data/jst/woj/<XX>.json = dane jednostek (nazwy, mandaty, wybrani, nakładki), data/jst/index.json = spis do wyszukiwarki i nawigacji.
 Pełny graf jednostki składa funkcja expand() poniżej; jej bliźniak w JS jest w widoku (expandJst). Jedna jednostka w jednej linii = czytelne różnice w gicie.
Skrypt wywraca się, gdy liczba wybranych radnych nie zgadza się z liczbą mandatów z plików okręgów (poza wypisanymi wyjątkami).
Użycie: python3 scripts/jst/build-frame.py --date RRRR-MM-DD [--only 10]"""
import csv, glob, io, json, os, re, sys, unicodedata, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(ROOT, 'data/jst/src'); OUT = os.path.join(ROOT, 'data/jst')
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
DATE = arg('--date'); ONLY = arg('--only'); assert DATE, 'podaj --date'
PKW_PAGE = 'https://samorzad2024.pkw.gov.pl/samorzad2024/pl/dane_w_arkuszach'; ELECTED_AT = '2024-04-07'
T = json.load(open(os.path.join(ROOT, 'scripts/jst/templates.json'), encoding='utf-8')); CENTRAL = json.load(open(os.path.join(ROOT, 'data/pl/graph.json'), encoding='utf-8'))['nodes']
def rows(name):
    path = glob.glob(os.path.join(SRC, name, '*.csv'))[0]; txt = open(path, 'rb').read().decode('utf-8-sig'); rd = csv.reader(io.StringIO(txt), delimiter=';'); hdr = next(rd)
    for r in rd:
        if len(r) >= len(hdr) - 1: yield dict(zip(hdr, r))
def slug(s): s = unicodedata.normalize('NFD', s.replace('ł', 'l').replace('Ł', 'L')); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower(); return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')
def person_name(raw):  # „KOWALSKA-NOWAK Anna Maria” → „Anna Maria Kowalska-Nowak”
    tok = raw.split(); sur = [t for t in tok if t.upper() == t and any(c.isalpha() for c in t)]; giv = [t for t in tok if t not in sur]
    cap = lambda t: '-'.join(x[:1].upper() + x[1:].lower() for x in t.split('-'))
    return ' '.join(giv + [cap(t) for t in sur]).strip()
def cite(key): c = T['cites'][key]; a = T['acts'][c['act']]; return {'cite': f"{c['label']} — {a['title']}", 'citeUrl': f"https://eli.gov.pl/eli/{a['eli']}/ogl", 'act': a['eli'], 'article': c['label']}
def legal(key): c = cite(key); return {'title': c['cite'], 'url': c['citeUrl'], 'act': c['act'], 'article': c['article']}
PROV = lambda extra=None: {'sources': [PKW_PAGE] + (extra or []), 'verifiedAt': DATE, 'confidence': 'high', 'verdict': 'confirmed'}
RIO = {'02': 'we Wrocławiu', '04': 'w Bydgoszczy', '06': 'w Lublinie', '08': 'w Zielonej Górze', '10': 'w Łodzi', '12': 'w Krakowie', '14': 'w Warszawie', '16': 'w Opolu', '18': 'w Rzeszowie', '20': 'w Białymstoku', '22': 'w Gdańsku', '24': 'w Katowicach', '26': 'w Kielcach', '28': 'w Olsztynie', '30': 'w Poznaniu', '32': 'w Szczecinie'}

# ---------- wejście: PKW ----------
woj_name = {}; units = {}   # teryt6 → jednostka
for r in rows('okregi_sejmiki_wojewodztw'):
    t = r['TERYT Województwa']; u = units.setdefault(t, {'t': t, 'kind': 'wojewodztwo', 'parent': None, 'woj': t[:2], 'name': 'Województwo ' + r['Województwo'], 'council': r['Wybierany organ'], 'seats': 0, 'pop': 0}); u['seats'] += int(r['Liczba mandatów']); u['pop'] += int(r['Mieszkańcy'] or 0); woj_name[t[:2]] = r['Województwo']
for r in rows('okregi_rady_powiatow'):
    t = r['TERYT Powiatu']; u = units.setdefault(t, {'t': t, 'kind': 'powiat', 'parent': t[:2] + '0000', 'woj': t[:2], 'name': 'Powiat ' + r['Powiat'], 'council': r['Wybierany organ'], 'seats': 0, 'pop': 0}); u['seats'] += int(r['Liczba mandatów']); u['pop'] += int(r['Mieszkańcy'] or 0)
for r in rows('okregi_rady_gmin'):
    t = r['TERYT Gminy']; mnpp = int(t[2:4]) >= 61; g = r['Gmina']; nm = ('Miasto ' + g[3:]) if g.startswith('m. ') else ('Gmina ' + g[4:]) if g.startswith('gm. ') else g
    u = units.setdefault(t, {'t': t, 'kind': 'mnpp' if mnpp else 'gmina', 'parent': (t[:2] + '0000') if mnpp else (t[:4] + '00'), 'woj': t[:2], 'name': nm, 'council': r['Wybierany organ'], 'seats': 0, 'pop': 0, 'powiatName': r['Powiat']}); u['seats'] += int(r['Liczba mandatów']); u['pop'] += int(r['Mieszkańcy'] or 0)
heads = {}
for r in rows('wybrani_wojt_burmistrz_prezydent'): heads[r['TERYT Gminy']] = {'organ': r['Wybierany organ'], 'name': person_name(r['Wybrany kandydat']), 'committee': r['Komitet zgłaszający kandydata'].strip()}
members = collections.defaultdict(list)
for f, key in (('kandydaci_sejmiki_wojewodztw', 'TERYT Województwa'), ('kandydaci_rady_powiatow', 'TERYT Powiatu'), ('kandydaci_rady_gmin_do_20k', 'TERYT Gminy'), ('kandydaci_rady_gmin_powyzej_20k', 'TERYT Gminy')):
    for r in rows(f):
        if r.get('Czy uzyskał mandat') == 'Tak': members[r[key]].append({'name': person_name(r['Nazwisko i imiona']), 'committee': (r.get('Skrót nazwy komitetu') or r.get('Nazwa komitetu') or '').strip()})

# ---------- kontrola sum ----------
problems = []; short = []
for t, u in units.items():
    got = len(members.get(t, []))
    if got > u['seats']: problems.append(f"{t} {u['name']}: wybranych {got} > mandatów {u['seats']}")
    elif got < u['seats']: short.append((t, u['name'], got, u['seats']))
    if u['kind'] in ('gmina', 'mnpp') and t not in heads: short.append((t, u['name'], 'brak wybranego organu wykonawczego w pliku PKW', ''))
for t in heads:
    if t not in units: problems.append(f'{t}: wójt bez jednostki')
for t, u in units.items():
    if u['parent'] and u['parent'] not in units: problems.append(f"{t} {u['name']}: brak jednostki nadrzędnej {u['parent']}")
if problems: print('\n'.join(problems[:20])); raise SystemExit(f'kontrola sum: {len(problems)} niezgodności')

# ---------- osoby organów nadzoru z grafu centralnego ----------
def central_people(nid): n = CENTRAL.get(nid) or {}; return [dict(p) for p in ((n.get('people') or {}).get('people') or [])][:1]
voiv = {}
for n in CENTRAL.values():
    if n.get('subtype') == 'voivode': voiv[n['name'].lower()] = n['id']
def voivode_for(w): adj = woj_name[w][:-1]; return voiv.get('wojewoda ' + adj.lower())

overlay = {}
for path in glob.glob(os.path.join(OUT, 'overlay', '*.json')):
    o = json.load(open(path, encoding='utf-8'))
    for k, v in (o.get('units') or {}).items(): overlay[k] = v
def overlay_for(u):  # klucze nakładki: województwo „10”, powiat „1001”, miasto na prawach powiatu „1061”, gmina pełny kod „100201”
    t = u['t']; return overlay.get(t[:2] if u['kind'] == 'wojewodztwo' else t if u['kind'] == 'gmina' else t[:4]) or {}
def canonical_name(name, t):
    """Strony BIP podają zwykle jedno imię, PKW wszystkie. Gdy w radzie tej jednostki jest dokładnie jedna osoba o tym samym pierwszym imieniu i nazwisku, używamy pełnego zapisu PKW, żeby ta sama osoba miała jeden zapis w całym kole."""
    parts = name.split()
    if len(parts) < 2: return name
    key = (slug(parts[0]), slug(parts[-1]))
    hits = [m['name'] for m in members.get(t, []) if (slug(m['name'].split()[0]), slug(m['name'].split()[-1])) == key]
    return hits[0] if len(hits) == 1 else name
def ov_people(ov, roles, position_id, position_name):
    out = []; t = position_id.split('-')[1]
    for pos in ov.get('positions') or []:
        if pos.get('role') not in roles: continue
        for p in pos.get('people') or []:
            if p.get('verdict') != 'confirmed' or not p.get('sourceUrl'): continue
            name = canonical_name(p['name'], t)
            out.append({'id': f"{position_id}-{slug(name)}", 'name': name, 'positionId': position_id, 'positionName': pos.get('title') or position_name, 'type': 'elected', 'startedAt': p.get('startedAt'), 'startedAtSource': p.get('startedAtSource'), 'acting': False, 'status': 'verified', 'party': None, 'imageUrl': None, 'sourceUrl': p['sourceUrl'], 'note': None, 'verdict': 'confirmed', 'verifiedAt': p.get('retrievedAt')})
    return out

# ---------- budowa grafu jednostki ----------
def build(u):
    t = u['t']; K = u['kind']; P = f'jst-{t}'; nodes = {}; edges = {}; ov = overlay_for(u)
    tier = 'g' if K in ('gmina', 'mnpp') else 'p' if K == 'powiat' else 'w'
    gen = {'g': ('gminy', 'Mieszkańcy gminy'), 'p': ('powiatu', 'Mieszkańcy powiatu'), 'w': ('województwa', 'Mieszkańcy województwa')}[tier]
    if K == 'mnpp' or u['name'].startswith('Miasto '): gen = ('miasta', 'Mieszkańcy miasta')
    def node(i, **kw):
        n = {'id': f'{P}-{i}', 'type': 'department', 'subtype': None, 'sector': 'executive', 'ring': 'administration', 'name': '', 'shortName': None, 'description': '', 'aliases': [], 'legalSource': None, 'officialUrl': None, 'bipUrl': None, 'regon': None, 'budgetPart': None,
             'parent': None, 'children': [], 'head': None, 'headOf': None, 'seatsCount': 0, 'status': 'active', 'statusNote': None, 'topics': [], 'employeeCount': {'actual': None, 'budget': None, 'source': None}, 'people': {'type': 'people', 'people': []}, 'provenance': PROV(), 'externalRef': None}
        n.update(kw); n['id'] = f'{P}-{i}'; nodes[n['id']] = n; return n
    def edge(a, b, ty, key, seats=0):
        c = cite(key); i = f"e-{t}-{a}--{ty}--{b}"; edges[i] = {'id': i, 'type': ty, 'fromId': f'{P}-{a}', 'toId': f'{P}-{b}', 'cite': c['cite'], 'citeUrl': c['citeUrl'], 'seatsAppointed': seats, 'disputed': False, 'provenance': {'sources': [c['citeUrl']], 'verifiedAt': DATE, 'confidence': 'high', 'verdict': 'confirmed'}}
    NO = dict(status='unverified', statusNote='Obsada tego stanowiska nie wynika z żadnego rejestru urzędowego. Zostanie uzupełniona ze strony BIP jednostki, ze wskazaniem źródła.')
    pop = f"{u['pop']:,}".replace(',', ' ')
    node('m', type='constituency', sector=None, ring='sovereign', name=f"{gen[1]}: {u['name']}", shortName=gen[1], description=f"Wspólnota samorządowa: {pop} mieszkańców według danych PKW przygotowanych na wybory samorządowe 2024.", legalSource=legal('k.wybory'))
    council = node('rada', type='elected', subtype='council', sector='legislative', ring='highest', name=u['council'], description=f"Organ stanowiący i kontrolny. {u['seats']} mandatów. Skład według wyników wyborów z 7 kwietnia 2024 r. ogłoszonych przez PKW; zmiany w trakcie kadencji nie są jeszcze śledzone.", legalSource=legal(tier + ('.rada' if tier != 'w' else '.sejmik')), seatsCount=u['seats'], head=f'{P}-przew')
    council['people']['people'] = [{'id': f"{P}-{slug(m['name'])}", 'name': m['name'], 'positionId': council['id'], 'positionName': 'Radny' if tier != 'w' else 'Radny województwa', 'type': 'elected', 'startedAt': None, 'startedAtSource': None, 'electedAt': ELECTED_AT, 'acting': False, 'status': 'verified', 'party': m['committee'] or None, 'imageUrl': None, 'sourceUrl': PKW_PAGE, 'note': None, 'verdict': 'confirmed'} for m in sorted(members.get(t, []), key=lambda m: (slug(m['name'].split()[-1]), slug(m['name'])))]
    chair_people = ov_people(ov, ('przewodniczacy_rady',), f'{P}-przew', 'Przewodniczący')
    node('przew', type='dept_head', sector='legislative', ring='highest', name='Przewodniczący: ' + u['council'], shortName='Przewodniczący rady' if tier != 'w' else 'Przewodniczący sejmiku', headOf=council['id'], description='Organizuje pracę rady i prowadzi jej obrady. Wybierany przez radę ze swego grona.', legalSource=legal(tier + '.przewodniczacy'), people={'type': 'people', 'people': chair_people}, **({} if chair_people else NO))
    vice = ov_people(ov, ('wiceprzewodniczacy_rady',), f'{P}-wiceprzew', 'Wiceprzewodniczący')
    node('wiceprzew', type='dept_head', sector='legislative', ring='highest', name='Wiceprzewodniczący: ' + u['council'], shortName='Wiceprzewodniczący rady' if tier != 'w' else 'Wiceprzewodniczący sejmiku', description='Od jednego do trzech wiceprzewodniczących wybieranych przez radę ze swego grona; zastępują przewodniczącego.', legalSource=legal(tier + '.wiceprzewodniczacy'), people={'type': 'people', 'people': vice}, **({} if vice else NO))
    node('kom-rew', type='commission', subtype='committee', sector='legislative', ring='satellite', parent=council['id'], name='Komisja rewizyjna', description='Obowiązkowa komisja rady do kontroli organu wykonawczego i jednostek organizacyjnych.', legalSource=legal(tier + '.kontrola'), people={'type': 'count', 'count': 0})
    node('kom-skarg', type='commission', subtype='committee', sector='legislative', ring='satellite', parent=council['id'], name='Komisja skarg, wniosków i petycji', description='Obowiązkowa komisja rady rozpatrująca skargi, wnioski i petycje mieszkańców.', legalSource=legal(tier + '.skargi'), people={'type': 'count', 'count': 0})
    edge('m', 'rada', 'elects', 'k.wybory', u['seats']); edge('rada', 'przew', 'dept_head', tier + '.przewodniczacy'); edge('rada', 'przew', 'elects', tier + '.przewodniczacy', 1); edge('rada', 'wiceprzew', 'elects', tier + '.wiceprzewodniczacy'); edge('rada', 'kom-rew', 'appoints', tier + '.kontrola'); edge('rada', 'kom-skarg', 'appoints', tier + '.skargi')
    if tier == 'g':
        h = heads.get(t); organ = h['organ'] if h else 'Wójt, burmistrz albo prezydent miasta'; word = organ.split()[0]
        ex = node('wojt', type='elected', sector='executive', ring='highest', name=organ, shortName=word, description='Organ wykonawczy gminy, wybierany przez mieszkańców w wyborach bezpośrednich. Kieruje urzędem.', legalSource=legal('g.wojt'), seatsCount=1)
        if h: ex['people']['people'] = [{'id': f"{P}-{slug(h['name'])}", 'name': h['name'], 'positionId': ex['id'], 'positionName': organ, 'type': 'elected', 'startedAt': None, 'startedAtSource': None, 'electedAt': ELECTED_AT, 'acting': False, 'status': 'verified', 'party': h['committee'] or None, 'imageUrl': None, 'sourceUrl': PKW_PAGE, 'note': 'Wybrany w wyborach samorządowych 2024 (pierwsza albo druga tura) według pliku PKW „wybrani wójtowie, burmistrzowie, prezydenci”.', 'verdict': 'confirmed'}]
        else: ex.update(status='vacant', statusNote='Plik PKW z wybranymi nie zawiera tej gminy (np. wybory nie dały rozstrzygnięcia).')
        urz = node('urzad', type='department', sector='executive', ring='administration', name='Urząd miasta' if gen[0] == 'miasta' else 'Urząd gminy', description=f'Aparat pomocniczy organu wykonawczego ({organ}). Oficjalna nazwa urzędu może brzmieć inaczej, np. urząd miejski.', legalSource=legal('g.urzad'), people={'type': 'count', 'count': 0})
        dep = ov_people(ov, ('zastepca_prezydenta',), f'{P}-zastepca', 'Zastępca')
        node('zastepca', type='dept_head', sector='executive', ring='administration', name=f'Zastępca: {organ}', shortName='Zastępca ' + {'Wójt': 'wójta', 'Burmistrz': 'burmistrza', 'Prezydent': 'prezydenta'}.get(word, 'wójta'), description='Powoływany i odwoływany zarządzeniem organu wykonawczego.', legalSource=legal('g.zastepca'), people={'type': 'people', 'people': dep}, **({} if dep else NO))
        sk = ov_people(ov, ('skarbnik',), f'{P}-skarbnik', 'Skarbnik')
        node('skarbnik', type='dept_head', sector='executive', ring='administration', name='Skarbnik gminy' if gen[0] != 'miasta' else 'Skarbnik miasta', description='Główny księgowy budżetu. Powoływany przez radę na wniosek organu wykonawczego.', legalSource=legal('g.skarbnik'), people={'type': 'people', 'people': sk}, **({} if sk else NO))
        node('jednostki', type='department', subtype='other', sector='executive', ring='satellite', parent=urz['id'], name='Jednostki organizacyjne (szkoły, ośrodki pomocy społecznej, zakłady)', shortName='Jednostki organizacyjne', description='Jednostki tworzone przez gminę do wykonywania jej zadań. Lista nie jest jeszcze zebrana.', legalSource=legal('g.jednostki'), people={'type': 'count', 'count': 0})
        node('pomocnicze', type='department', subtype='other', sector='legislative', ring='satellite', parent=council['id'], name='Jednostki pomocnicze (sołectwa, dzielnice, osiedla)', shortName='Jednostki pomocnicze', description='Tworzone uchwałą rady po konsultacjach z mieszkańcami. Lista nie jest jeszcze zebrana.', legalSource=legal('g.pomocnicze'), people={'type': 'count', 'count': 0})
        edge('m', 'wojt', 'elects', 'g.mieszkancy', 1); edge('rada', 'wojt', 'oversees', 'g.kontrola'); edge('wojt', 'urzad', 'oversees', 'g.urzad'); edge('urzad', 'wojt', 'administers', 'g.urzad'); edge('wojt', 'zastepca', 'appoints', 'g.zastepca'); edge('rada', 'skarbnik', 'appoints', 'g.skarbnik'); edge('wojt', 'skarbnik', 'nominates', 'g.skarbnik'); edge('rada', 'pomocnicze', 'oversees', 'g.pomocnicze')
        execs = ['wojt']; nadzor = 'g.nadzor'; boss = 'wojt'; sec_name = 'Sekretarz miasta' if gen[0] == 'miasta' else 'Sekretarz gminy'
    else:
        lead_role, lead_title, board_name, office = (('starosta', 'Starosta', 'Zarząd powiatu', 'Starostwo powiatowe') if tier == 'p' else ('marszalek', 'Marszałek województwa', 'Zarząd województwa', 'Urząd marszałkowski'))
        board_people = ov_people(ov, ('wicestarosta', 'wicemarszalek', 'czlonek_zarzadu'), f'{P}-zarzad', 'Członek zarządu')
        node('zarzad', type='department', subtype='council', sector='executive', ring='highest', name=f"{board_name}: {u['name']}", shortName=board_name, description='Kolegialny organ wykonawczy wybierany przez radę.' if tier == 'p' else 'Kolegialny organ wykonawczy wybierany przez sejmik.', legalSource=legal(tier + '.zarzad'), head=f'{P}-lider', seatsCount=5 if tier == 'w' else 0, people={'type': 'people', 'people': board_people}, **({} if board_people else {'statusNote': 'Skład zarządu nie wynika z żadnego rejestru urzędowego. Zostanie uzupełniony ze strony BIP jednostki.'}))
        lp = ov_people(ov, (lead_role,), f'{P}-lider', lead_title)
        node('lider', type='dept_head', sector='executive', ring='highest', name=f"{lead_title}: {u['name']}", shortName=lead_title, headOf=f'{P}-zarzad', description='Przewodniczący zarządu, kieruje urzędem jednostki.' + (' Zwierzchnik powiatowych służb, inspekcji i straży.' if tier == 'p' else ''), legalSource=legal(tier + '.wybor'), people={'type': 'people', 'people': lp}, **({} if lp else NO))
        urz = node('urzad', type='department', sector='executive', ring='administration', name=office, description='Aparat pomocniczy zarządu.', legalSource=legal('p.starostwo' if tier == 'p' else 'w.urzad'), people={'type': 'count', 'count': 0})
        edge('rada', 'zarzad', 'elects', tier + '.wybor'); edge('zarzad', 'lider', 'dept_head', tier + '.zarzad'); edge('rada', 'lider', 'elects', tier + '.wybor', 1); edge('rada', 'zarzad', 'oversees', tier + '.kontrola'); edge('lider', 'urzad', 'oversees', 'p.starostwo' if tier == 'p' else 'w.urzad'); edge('urzad', 'zarzad', 'administers', 'p.starostwo' if tier == 'p' else 'w.urzad')
        sk_name = 'Skarbnik powiatu' if tier == 'p' else 'Skarbnik województwa'; sk = ov_people(ov, ('skarbnik',), f'{P}-skarbnik', sk_name)
        node('skarbnik', type='dept_head', sector='executive', ring='administration', name=sk_name, description='Główny księgowy budżetu powiatu. Powoływany przez radę na wniosek starosty.' if tier == 'p' else 'Główny księgowy budżetu województwa. Powoływany przez sejmik na wniosek marszałka.', legalSource=legal(tier + '.skarbnik'), people={'type': 'people', 'people': sk}, **({} if sk else NO))
        edge('rada', 'skarbnik', 'appoints', tier + '.skarbnik'); edge('lider', 'skarbnik', 'nominates', tier + '.skarbnik')
        if tier == 'p':
            node('sluzby', type='department', subtype='other', sector='executive', ring='satellite', parent=urz['id'], name='Powiatowe służby, inspekcje i straże', description='Administracja zespolona pod zwierzchnictwem starosty. Lista nie jest jeszcze zebrana.', legalSource=legal('p.starostwo'), people={'type': 'count', 'count': 0})
            edge('lider', 'sluzby', 'oversees', 'p.starostwo')
        execs = ['zarzad']; nadzor = tier + '.nadzor'; boss = 'lider'; sec_name = 'Sekretarz powiatu' if tier == 'p' else 'Sekretarz województwa'
    # sekretarz: stanowisko obowiązkowe w każdym urzędzie (ustawa o pracownikach samorządowych), podlega kierownikowi urzędu
    sec = ov_people(ov, ('sekretarz',), f'{P}-sekretarz', sec_name)
    node('sekretarz', type='dept_head', sector='executive', ring='administration', name=sec_name, description='Odpowiada za organizację pracy urzędu z upoważnienia jego kierownika. Zatrudniany na umowę o pracę, nie może należeć do partii politycznej.', legalSource=legal('ups.sekretarz'), people={'type': 'people', 'people': sec}, **({} if sec else NO))
    edge(boss, 'sekretarz', 'oversees', 'ups.sekretarz.podleglosc')
    # nadzór i kontrola: te same organy na każdym szczeblu, osoby z grafu centralnego
    w = u['woj']; vid = voivode_for(w); adj = woj_name[w][:-1]
    node('wojewoda', type='dept_head', sector='independent', ring='oversight', name='Wojewoda ' + '-'.join(x.capitalize() for x in adj.split('-')), description='Przedstawiciel Rady Ministrów w województwie. Organ nadzoru nad legalnością działania samorządu.', legalSource=legal('k.nadzor'), externalRef=vid, people={'type': 'people', 'people': central_people(vid)}, provenance={'sources': ['https://grafpanstwa.pl/#node=' + (vid or '')], 'verifiedAt': DATE, 'confidence': 'high', 'verdict': 'confirmed'})
    node('prm', type='dept_head', sector='independent', ring='oversight', name='Prezes Rady Ministrów', description='Organ nadzoru nad działalnością samorządu terytorialnego.', legalSource=legal('k.nadzor'), externalRef='pl-prezes-rady-ministrow', people={'type': 'people', 'people': central_people('pl-prezes-rady-ministrow')}, provenance={'sources': ['https://grafpanstwa.pl/#node=pl-prezes-rady-ministrow'], 'verifiedAt': DATE, 'confidence': 'high', 'verdict': 'confirmed'})
    node('rio', type='commission', subtype='oversight_body', sector='independent', ring='oversight', name='Regionalna Izba Obrachunkowa ' + RIO[w], shortName='RIO', description='Organ nadzoru w zakresie spraw finansowych.', legalSource=legal('k.nadzor'), people={'type': 'count', 'count': 0})
    node('sko', type='commission', subtype='adjudicative_body', sector='independent', ring='oversight', name='Samorządowe kolegium odwoławcze', shortName='SKO', description='Organ wyższego stopnia w sprawach indywidualnych z zakresu administracji publicznej należących do samorządu. Właściwe miejscowo kolegium nie jest jeszcze wskazane z nazwy.', legalSource=legal('sko.art1'), people={'type': 'count', 'count': 0})
    node('nik', type='department', subtype='oversight_body', sector='independent', ring='oversight', name='Najwyższa Izba Kontroli', shortName='NIK', description='Może kontrolować samorząd z punktu widzenia legalności, gospodarności i rzetelności.', legalSource=legal('k.nik'), externalRef='pl-nik', people={'type': 'count', 'count': 0})
    for x in execs: edge('wojewoda', x, 'oversees', nadzor); edge('rio', x, 'oversees', nadzor); edge('nik', x, 'oversees', 'k.nik'); edge('sko', x, 'oversees', 'sko.art1')
    edge('wojewoda', 'rada', 'oversees', nadzor); edge('prm', 'rada', 'oversees', nadzor); edge('rio', 'rada', 'oversees', nadzor)
    for n in nodes.values():
        if n['parent']: nodes[n['parent']]['children'].append(n['id'])
    kids = sorted(c for c, x in units.items() if x['parent'] == t)
    meta = {'gov': 'jst', 'teryt': t, 'kind': K, 'name': u['name'], 'version': '0.1', 'generatedAt': DATE, 'constituency': f'{P}-m', 'parent': u['parent'], 'woj': w, 'population': u['pop'],
            'description': {'wojewodztwo': 'Samorząd województwa: sejmik, zarząd z marszałkiem i organy nadzoru.', 'powiat': 'Samorząd powiatu: rada, zarząd ze starostą i organy nadzoru.', 'mnpp': 'Miasto na prawach powiatu: rada, prezydent i organy nadzoru. Wykonuje też zadania powiatu.', 'gmina': 'Samorząd gminy: rada, organ wykonawczy i organy nadzoru.'}[K],
            'sectorTitles': {'legislative': 'STANOWIĄCA I KONTROLNA', 'executive': 'WYKONAWCZA', 'independent': 'NADZÓR I KONTROLA'}, 'sectorLabels': {'legislative': 'Stanowiąca i kontrolna', 'executive': 'Wykonawcza', 'independent': 'Nadzór i kontrola'}, 'children': kids}
    return {'meta': meta, 'nodes': nodes, 'edges': edges}

# ---------- zapis: szablony wariantów + zwarte dane jednostek ----------
S_T, S_NAME, S_COUNCIL, S_ORGAN, S_SEATS, S_POP = '@@T@@', '@@NAME@@', '@@COUNCIL@@', '@@ORGAN@@', '@@SEATS@@', '@@POP@@'
def variant(u):
    if u['kind'] in ('gmina', 'mnpp'): h = heads.get(u['t']); return f"{u['kind']}:{(h['organ'].split()[0] if h else 'Wójt')}:{'m' if (u['kind'] == 'mnpp' or u['name'].startswith('Miasto ')) else 'g'}"
    return u['kind']
def template_for(v, sample):
    """Szablon wariantu: graf zbudowany dla jednostki-wzorca, w którym wartości zmienne zastąpiono znacznikami."""
    ph = dict(sample, name=('Miasto ' if v.endswith(':m') else '') + S_NAME if sample['kind'] in ('gmina', 'mnpp') and v.endswith(':m') else S_NAME, council=S_COUNCIL, seats=0, pop=0)
    t = sample['t']; saved_h, saved_m, saved_o = heads.get(t), members.get(t), dict(overlay)
    if t in heads: heads[t] = dict(heads[t], organ=heads[t]['organ'].split()[0] + ' ' + S_ORGAN, name='X', committee='')
    members[t] = []; overlay.clear()
    try: g = build(ph)
    finally:
        overlay.update(saved_o)
        if saved_h is not None: heads[t] = saved_h
        if saved_m is not None: members[t] = saved_m
    txt = json.dumps(g, ensure_ascii=False, separators=(',', ':'), sort_keys=True).replace(f'jst-{t}', 'jst-' + S_T).replace(f'e-{t}-', 'e-' + S_T + '-')
    return txt
def compact(u, committees):
    t = u['t']; h = heads.get(t); ov = overlay_for(u); ci = lambda c: committees.setdefault(c or '', len(committees))
    rec = {'n': u['name'], 'k': u['kind'], 'p': u['parent'], 'v': variant(u), 'c': u['council'], 's': u['seats'], 'pop': u['pop'], 'm': [[m['name'], ci(m['committee'])] for m in sorted(members.get(t, []), key=lambda m: (slug(m['name'].split()[-1]), slug(m['name'])))]}
    if h: rec['o'] = h['organ']; rec['h'] = [h['name'], ci(h['committee'])]
    P = f'jst-{t}'; ovp = {}
    for key, roles, title in (('przew', ('przewodniczacy_rady',), 'Przewodniczący'), ('wiceprzew', ('wiceprzewodniczacy_rady',), 'Wiceprzewodniczący'), ('lider', ('starosta', 'marszalek'), ''), ('zarzad', ('wicestarosta', 'wicemarszalek', 'czlonek_zarzadu'), 'Członek zarządu'), ('skarbnik', ('skarbnik',), 'Skarbnik'), ('sekretarz', ('sekretarz',), 'Sekretarz'), ('zastepca', ('zastepca_prezydenta',), 'Zastępca')):
        ppl = ov_people(ov, roles, f'{P}-{key}', title)
        if ppl: ovp[key] = [{k: v for k, v in p.items() if v not in (None, False, '') and k not in ('id', 'positionId', 'type', 'status', 'verdict')} for p in ppl]
    if ovp: rec['ov'] = ovp
    if ov.get('officialUrl'): rec['url'] = ov['officialUrl']
    if ov.get('bipUrl'): rec['bip'] = ov['bipUrl']
    return rec
def expand(tiers, bundle, t):
    """Bliźniak funkcji expandJst z widoku: szablon wariantu + dane jednostki → pełny graf w schemacie graph.json."""
    u = bundle['units'][t]; sh = bundle['shared']; esc = lambda v: json.dumps(str(v), ensure_ascii=False)[1:-1]; nm = u['n'][7:] if u['v'].endswith(':m') and u['n'].startswith('Miasto ') else u['n']
    txt = tiers['variants'][u['v']].replace(S_T, t).replace(S_NAME, esc(nm)).replace(S_COUNCIL, esc(u['c'])).replace(S_ORGAN, esc(' '.join((u.get('o') or '').split()[1:])))
    g = json.loads(txt); P = f'jst-{t}'; N = g['nodes']; com = bundle['committees']
    person = lambda nid, name, pos, party, extra=None: dict({'id': f'{P}-{slug(name)}', 'name': name, 'positionId': nid, 'positionName': pos, 'type': 'elected', 'startedAt': None, 'startedAtSource': None, 'electedAt': ELECTED_AT, 'acting': False, 'status': 'verified', 'party': party or None, 'imageUrl': None, 'sourceUrl': PKW_PAGE, 'note': None, 'verdict': 'confirmed'}, **(extra or {}))
    r = N[f'{P}-rada']; r['seatsCount'] = u['s']; r['description'] = r['description'].replace('0 mandatów', f"{u['s']} mandatów"); r['people'] = {'type': 'people', 'people': [person(r['id'], m[0], 'Radny województwa' if u['k'] == 'wojewodztwo' else 'Radny', com[m[1]]) for m in u['m']]}
    m = N[f'{P}-m']; m['description'] = m['description'].replace(' 0 mieszkańców', ' ' + f"{u['pop']:,}".replace(',', ' ') + ' mieszkańców')
    if u.get('h'): w = N[f'{P}-wojt']; w['people'] = {'type': 'people', 'people': [person(w['id'], u['h'][0], u['o'], com[u['h'][1]])]}
    for key, ppl in (u.get('ov') or {}).items():
        n = N.get(f'{P}-{key}')
        if not n: continue
        n['people'] = {'type': 'people', 'people': [dict(person(n['id'], p['name'], p.get('positionName') or n['name'], None), electedAt=None, sourceUrl=p['sourceUrl'], startedAt=p.get('startedAt'), startedAtSource=p.get('startedAtSource'), verifiedAt=p.get('verifiedAt')) for p in ppl]}; n['status'] = 'active'; n['statusNote'] = None
        n['provenance'] = {'sources': sorted({p['sourceUrl'] for p in ppl}), 'verifiedAt': max((p.get('verifiedAt') or DATE) for p in ppl), 'confidence': 'high', 'verdict': 'confirmed'}
    for key in ('urzad', 'rada'):
        if u.get('url') and key == 'urzad': N[f'{P}-urzad']['officialUrl'] = u['url']
        if u.get('bip') and key == 'urzad': N[f'{P}-urzad']['bipUrl'] = u['bip']
    wv = N[f'{P}-wojewoda']; wv['name'] = sh['wojewoda']['name']; wv['externalRef'] = sh['wojewoda']['ref']; wv['people'] = {'type': 'people', 'people': sh['wojewoda']['people']}; wv['provenance']['sources'] = ['https://grafpanstwa.pl/#node=' + (sh['wojewoda']['ref'] or '')]
    N[f'{P}-prm']['people'] = {'type': 'people', 'people': sh['prm']['people']}; N[f'{P}-rio']['name'] = 'Regionalna Izba Obrachunkowa ' + sh['rio']
    g['meta'].update(teryt=t, kind=u['k'], name=u['n'], parent=u['p'], woj=t[:2], population=u['pop'], children=sorted(c for c, x in bundle['units'].items() if x['p'] == t), parentName=(bundle['units'].get(u['p']) or {}).get('n'))
    return g

os.makedirs(os.path.join(OUT, 'woj'), exist_ok=True); index = []; stats = collections.Counter(); variants = {}
for t, u in sorted(units.items()): variants.setdefault(variant(u), u)
tiers = {'meta': {'generatedAt': DATE, 'note': 'Szablon grafu dla każdego wariantu jednostki. Znaczniki: @@T@@ kod TERYT, @@NAME@@ nazwa, @@COUNCIL@@ nazwa rady, @@ORGAN@@ nazwa organu wykonawczego bez pierwszego słowa.', 'acts': T['acts']}, 'variants': {v: template_for(v, sample) for v, sample in sorted(variants.items())}}
json.dump(tiers, open(os.path.join(OUT, 'tiers.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for w in sorted(woj_name):
    if ONLY and w != ONLY: continue
    committees = {}; recs = {t: compact(u, committees) for t, u in sorted(units.items()) if u['woj'] == w}; vid = voivode_for(w); adj = woj_name[w][:-1]
    bundle = {'meta': {'woj': w, 'name': woj_name[w], 'generatedAt': DATE, 'units': len(recs), 'source': PKW_PAGE, 'electedAt': ELECTED_AT},
              'shared': {'wojewoda': {'name': 'Wojewoda ' + '-'.join(x.capitalize() for x in adj.split('-')), 'ref': vid, 'people': central_people(vid)}, 'prm': {'people': central_people('pl-prezes-rady-ministrow')}, 'rio': RIO[w]},
              'committees': [c for c, _ in sorted(committees.items(), key=lambda kv: kv[1])], 'units': recs}
    with open(os.path.join(OUT, 'woj', w + '.json'), 'w', encoding='utf-8') as fh:
        head_part = {k: v for k, v in bundle.items() if k != 'units'}; fh.write(json.dumps(head_part, ensure_ascii=False, separators=(',', ':'))[:-1] + ',\n"units":{\n'); fh.write(',\n'.join(json.dumps(t) + ':' + json.dumps(r, ensure_ascii=False, separators=(',', ':')) for t, r in recs.items())); fh.write('\n}}\n')
    # kontrola: każdy graf da się złożyć i jest spójny (węzły relacji istnieją, rodzice istnieją, liczba radnych = liczba mandatów)
    for t in recs:
        g = expand(tiers, bundle, t); N = g['nodes']
        for e in g['edges'].values(): assert e['fromId'] in N and e['toId'] in N, (t, e['id'])
        for n in N.values(): assert not n['parent'] or n['parent'] in N, (t, n['id']); assert n['legalSource'] and n['legalSource']['url'], (t, n['id'])
        assert len(N[f'jst-{t}-rada']['people']['people']) == units[t]['seats'], t; assert '@@' not in json.dumps(g, ensure_ascii=False), t
        u = units[t]; stats['units'] += 1; stats[u['kind']] += 1; stats['people'] += sum(len((n.get('people') or {}).get('people') or []) for n in N.values()); stats['nodes'] += len(N); stats['edges'] += len(g['edges'])
        index.append({'t': t, 'n': u['name'], 'k': u['kind'], 'p': u['parent'], 'pop': u['pop'], 's': u['seats'], 'h': (heads.get(t) or {}).get('name')})
if not ONLY:
    json.dump({'meta': {'generatedAt': DATE, 'source': PKW_PAGE, 'electedAt': ELECTED_AT, 'stats': dict(stats), 'woj': woj_name}, 'units': index}, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('jednostek:', stats['units'], {k: stats[k] for k in ('wojewodztwo', 'powiat', 'mnpp', 'gmina')}, '| wariantów szablonu:', len(tiers['variants']), sorted(tiers['variants']))
print('po złożeniu: osób', stats['people'], '| węzłów', stats['nodes'], '| relacji', stats['edges'], '| wyjątków od kontroli sum:', len(short))
json.dump([{'teryt': s_[0], 'name': s_[1], 'elected': s_[2], 'seats': s_[3]} for s_ in short], open(os.path.join(OUT, 'frame-exceptions.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
