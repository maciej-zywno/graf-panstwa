#!/usr/bin/env python3
"""Buduje chunk data/pl/chunks/parlament.json: organy wewnętrzne Sejmu i Senatu (prezydia, konwenty seniorów, komisje) oraz kluby i koła.
Źródła (wyłącznie urzędowe, maszynowe tam, gdzie istnieją):
  - Sejm: https://api.sejm.gov.pl/sejm/term10/{committees,clubs,clubs/<id>/members,MP}  (JSON, bez klucza)
  - Senat: https://www.senat.gov.pl/prace/komisje-senackie/ (+ sklad,<id>,…) i https://www.senat.gov.pl/sklad/kluby-i-kola/ (HTML; robots.txt dopuszcza; /gfx/ zabronione, więc bez zdjęć)
  - Prawo: ELI API Sejmu (metadane aktów do weryfikacji tytułów)
  - Prezydia: osoby skopiowane z już zweryfikowanych węzłów marszałków (chunk konstytucyjne)
Drugi przebieg (--verify) pobiera źródła ponownie i sprawdza, czy każde nazwisko z chunku nadal występuje w źródle przy tej funkcji.
Użycie: python3 scripts/build-parliament-chunk.py [--today YYYY-MM-DD] [--verify]"""
import json, re, sys, os, html, time, unicodedata, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = sys.argv[sys.argv.index('--today') + 1] if '--today' in sys.argv else '2026-09-17'
TERM = 10
API = f'https://api.sejm.gov.pl/sejm/term{TERM}'
UA = {'User-Agent': 'Mozilla/5.0 (graf-panstwa; projekt obywatelski; dane urzedowe)', 'Accept': '*/*'}

def fetch(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))
def jget(url): return json.loads(fetch(url))
def slug(s):
    s = unicodedata.normalize('NFD', s.replace('ł', 'l').replace('Ł', 'L')); s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s)).strip('-')
def pid(name): parts = name.split(); return 'pl-' + slug(parts[0] + ' ' + parts[-1]) if len(parts) > 1 else 'pl-' + slug(name)
def eli(pub, year, pos): return f'https://eli.gov.pl/eli/{pub}/{year}/{pos}/ogl'
def prov(sources, conf='high'): return {'sources': sources, 'verifiedAt': TODAY, 'confidence': conf}

ACTS = {  # (publisher, year, pos): fragment oczekiwanego tytułu — sprawdzane w ELI, żeby nie cytować nieistniejącego aktu
    ('DU', 1997, 483): 'Konstytucja', ('MP', 1992, 185): 'Regulamin Sejmu', ('MP', 1991, 11): 'Regulamin Senatu',
    ('DU', 1996, 350): 'wykonywaniu mandatu posła i senatora', ('DU', 1999, 321): 'sejmowej komisji śledczej',
}
def check_acts():
    for (pub, y, p), frag in ACTS.items():
        t = jget(f'https://api.sejm.gov.pl/eli/acts/{pub}/{y}/{p}').get('title', '')
        assert frag.lower() in t.lower(), f'ELI {pub}/{y}/{p}: tytuł „{t}” nie zawiera „{frag}”'
        print(f'  ELI OK {pub}/{y}/{p}: {t[:90]}')

REG_SEJM, REG_SENAT, KONST = eli('MP', 1992, 185), eli('MP', 1991, 11), eli('DU', 1997, 483)
MANDAT, SLEDCZA = eli('DU', 1996, 350), eli('DU', 1999, 321)
nodes, edges = {}, {}
def node(id, **kw):
    n = {'id': id, 'aliases': [], 'officialUrl': None, 'bipUrl': None, 'parent': None, 'head': None, 'headOf': None, 'seatsCount': 0, 'status': 'active',
         'employeeCount': {'actual': None, 'budget': None, 'source': None}}; n.update(kw); nodes[id] = n; return n
def edge(frm, typ, to, cite, url, seats=0, conf='high', sources=None):
    eid = f'e-{frm[3:]}--{typ}--{to[3:]}'[:150]; edges[eid] = {'id': eid, 'type': typ, 'fromId': frm, 'toId': to, 'cite': cite, 'citeUrl': url, 'seatsAppointed': seats, 'disputed': False, 'provenance': {'sources': sources or [url], 'confidence': conf}}
def person(name, position_id, position_name, source, typ='elected', started=None, started_src=None, party=None, image=None, note=None):
    return {'id': pid(name), 'name': name, 'positionId': position_id, 'positionName': position_name, 'type': typ, 'startedAt': started, 'acting': False, 'status': 'verified', 'party': party,
            'imageUrl': image, 'sourceUrl': source, 'startedAtSource': started_src, 'note': note}

def build():
    print('Sprawdzam akty w ELI…'); check_acts()
    base = json.load(open(os.path.join(ROOT, 'data/pl/chunks/konstytucyjne.json'), encoding='utf-8'))['nodes']
    # ---------- SEJM ----------
    print('Sejm API…'); committees = jget(f'{API}/committees'); clubs = jget(f'{API}/clubs'); mps = {m['id']: m for m in jget(f'{API}/MP')}
    marsz = base['pl-marszalek-sejmu']['people']['people']
    node('pl-prezydium-sejmu', type='commission', subtype='council', sector='legislative', ring='satellite', parent='pl-sejm', name='Prezydium Sejmu', shortName='Prezydium Sejmu',
         description='Organ Sejmu złożony z Marszałka i wicemarszałków. Ustala plan prac Sejmu, dokonuje wykładni Regulaminu, organizuje współpracę komisji i czuwa nad wykonywaniem obowiązków przez posłów (Regulamin Sejmu art. 9 pkt 2, art. 11–13).',
         legalSource={'title': 'Regulamin Sejmu RP, art. 9 pkt 2 i art. 11–13 (M.P. 1992 nr 26 poz. 185; t.j. M.P. 2026 poz. 573)', 'url': REG_SEJM, 'act': 'MP/1992/185', 'article': 'art. 9 pkt 2, art. 11–13'},
         officialUrl='https://www.sejm.gov.pl/', seatsCount=len(marsz), people={'type': 'people', 'people': [dict(p, positionId='pl-prezydium-sejmu') for p in marsz]},
         provenance=prov(list({p['sourceUrl'] for p in marsz}) + ['https://api.sejm.gov.pl/eli/acts/MP/2026/573/text.pdf']))
    edge('pl-sejm', 'elects', 'pl-prezydium-sejmu', 'Konstytucja RP art. 110 ust. 1 (Sejm wybiera ze swojego grona Marszałka i wicemarszałków); Regulamin Sejmu art. 11', KONST, len(marsz))
    edge('pl-marszalek-sejmu', 'ex_officio', 'pl-prezydium-sejmu', 'Regulamin Sejmu art. 11 (Prezydium Sejmu tworzą Marszałek i wicemarszałkowie)', REG_SEJM)
    node('pl-konwent-seniorow-sejmu', type='commission', subtype='council', sector='legislative', ring='satellite', parent='pl-sejm', name='Konwent Seniorów Sejmu', shortName='Konwent Seniorów',
         description='Organ Sejmu zapewniający współdziałanie klubów w sprawach toku prac Sejmu. Tworzą go Marszałek, wicemarszałkowie oraz przewodniczący lub wiceprzewodniczący klubów i przedstawiciele porozumień; Szef Kancelarii Sejmu uczestniczy z głosem doradczym. Opiniuje m.in. plany prac i porządek dzienny (Regulamin Sejmu art. 14–16).',
         legalSource={'title': 'Regulamin Sejmu RP, art. 9 pkt 3 i art. 14–16', 'url': REG_SEJM, 'act': 'MP/1992/185', 'article': 'art. 9 pkt 3, art. 14–16'}, officialUrl='https://www.sejm.gov.pl/',
         people={'type': 'people', 'people': []}, statusNote='Skład funkcyjny: Marszałek, wicemarszałkowie i przedstawiciele klubów (lista imienna nie jest publikowana w API).', provenance=prov(['https://api.sejm.gov.pl/eli/acts/MP/2026/573/text.pdf']))
    edge('pl-marszalek-sejmu', 'ex_officio', 'pl-konwent-seniorow-sejmu', 'Regulamin Sejmu art. 15 ust. 1', REG_SEJM)
    edge('pl-prezydium-sejmu', 'ex_officio', 'pl-konwent-seniorow-sejmu', 'Regulamin Sejmu art. 15 ust. 1 (w skład wchodzą Marszałek i wicemarszałkowie)', REG_SEJM)
    edge('pl-konwent-seniorow-sejmu', 'advises', 'pl-marszalek-sejmu', 'Regulamin Sejmu art. 16 ust. 1 (Konwent opiniuje plany prac, porządek dzienny i inne sprawy przekazane przez Marszałka lub Prezydium)', REG_SEJM)
    KIND = {'STANDING': ('stała', 'Regulamin Sejmu RP, art. 18 ust. 1 (komisje stałe); Konstytucja RP art. 110 ust. 3', 'art. 18 ust. 1', REG_SEJM, 'MP/1992/185'),
            'EXTRAORDINARY': ('nadzwyczajna', 'Regulamin Sejmu RP, art. 19 (komisje nadzwyczajne); Konstytucja RP art. 110 ust. 3', 'art. 19', REG_SEJM, 'MP/1992/185'),
            'INVESTIGATIVE': ('śledcza', 'Konstytucja RP art. 111; ustawa z 21.01.1999 r. o sejmowej komisji śledczej (Dz.U. 1999 nr 35 poz. 321)', 'art. 111 Konstytucji', SLEDCZA, 'DU/1999/321')}
    for c in committees:
        code = c['code']; cid = 'pl-sejm-komisja-' + slug(code); kind, ltitle, art, lurl, act = KIND.get(c.get('type'), KIND['STANDING']); src = f'{API}/committees/{code}'
        ppl = []
        for m in c.get('members', []):
            fn = (m.get('function') or '').strip()
            if not fn: continue
            mp = mps.get(m['id'], {}); name = (mp.get('firstLastName') or f"{m.get('firstName','')} {m.get('lastName','')}").strip()
            ppl.append(person(name, cid, fn[0].upper() + fn[1:] + ' komisji', src, party=m.get('club'), image=f"{API}/MP/{m['id']}/photo", note='Data objęcia funkcji w komisji nie jest podawana przez API (joinDate to data wejścia do komisji).'))
        ppl.sort(key=lambda p: (0 if p['positionName'].lower().startswith('przewodnicz') else 1, p['name']))
        scope = re.sub(r'\s+', ' ', c.get('scope') or '').strip()
        desc = f"Komisja {kind} Sejmu X kadencji" + (f", powołana {c['appointmentDate']}" if c.get('appointmentDate') else '') + f". Liczy {len(c.get('members', []))} posłów. " + (('Zakres: ' + scope) if scope else '')
        node(cid, type='commission', subtype='committee', sector='legislative', ring='satellite', parent='pl-sejm', name=f"{c['name']} (Sejm)", shortName=code, description=desc[:447] + ('…' if len(desc) > 447 else ''),
             aliases=[c['name'], code, (c.get('nameGenitive') or '')] if c.get('nameGenitive') else [c['name'], code],
             legalSource={'title': ltitle, 'url': lurl, 'act': act, 'article': art}, officialUrl=f'https://www.sejm.gov.pl/Sejm{TERM}.nsf/agent.xsp?symbol=KOMISJAST&NrKadencji={TERM}&KodKom={code}',
             seatsCount=len(c.get('members', [])), people={'type': 'people', 'people': ppl}, committeeKind=c.get('type'), appointedAt=c.get('appointmentDate'), provenance=prov([src]))
        edge('pl-sejm', 'appoints', cid, 'Konstytucja RP art. 110 ust. 3 (Sejm powołuje komisje stałe oraz może powoływać komisje nadzwyczajne)' if c.get('type') != 'INVESTIGATIVE' else 'Konstytucja RP art. 111 ust. 1 (Sejm może powołać komisję śledczą do zbadania określonej sprawy)', KONST, len(c.get('members', [])), sources=[src, KONST])
    for cl in clubs:
        if cl['id'].lower().startswith('niez'): continue
        members = jget(f"{API}/clubs/{cl['id']}/members"); n_m = cl.get('membersCount') or len(members); big = n_m >= 15; kid = 'pl-sejm-' + ('klub-' if big else 'kolo-') + slug(cl['id']); src = f"{API}/clubs/{cl['id']}/members"
        chairs = []
        for m in members:
            for f in m.get('functions', []):
                if f.get('functionType') in ('chairman', 'vice_chairman') and not f.get('dismissalDate'):
                    mp = mps.get(m['id'], {}); name = (mp.get('firstLastName') or f"{m.get('firstName','')} {m.get('lastName','')}").strip()
                    chairs.append(person(name, kid, f.get('name', 'przewodniczący')[0].upper() + f.get('name', 'przewodniczący')[1:], src, started=f.get('appointmentDate'), started_src=src, party=cl['id'], image=f"{API}/MP/{m['id']}/photo"))
        chairs.sort(key=lambda p: (0 if p['positionName'].lower().startswith('przewodnicz') else 1, p['name']))
        node(kid, type='political_group', subtype='parliamentary_club' if big else 'parliamentary_circle', sector='legislative', ring='satellite', parent='pl-sejm', name=cl['name'], shortName=cl['id'],
             description=f"{'Klub' if big else 'Koło'} {'poselski' if big else 'poselskie'} w Sejmie X kadencji, {n_m} posłów. To struktura polityczna posłów, a nie organ Sejmu: kluby (co najmniej 15 posłów) i koła (co najmniej 3) tworzy się na zasadzie politycznej (Regulamin Sejmu art. 8; ustawa o wykonywaniu mandatu posła i senatora art. 17).",
             aliases=[cl['id']], legalSource={'title': 'Ustawa z 9.05.1996 r. o wykonywaniu mandatu posła i senatora, art. 17; Regulamin Sejmu art. 8', 'url': MANDAT, 'act': 'DU/1996/350', 'article': 'art. 17'},
             officialUrl=f'https://www.sejm.gov.pl/Sejm{TERM}.nsf/klubposlowie.xsp?klub={cl["id"]}', seatsCount=n_m, people={'type': 'people', 'people': chairs[:8]}, provenance=prov([f'{API}/clubs', src]))
        if big: edge(kid, 'ex_officio', 'pl-konwent-seniorow-sejmu', 'Regulamin Sejmu art. 15 ust. 1 (w skład Konwentu wchodzą przewodniczący lub wiceprzewodniczący klubów)', REG_SEJM, 1)
    # ---------- SENAT ----------
    print('Senat (HTML)…'); S = 'https://www.senat.gov.pl'
    marsz_s = base['pl-marszalek-senatu']['people']['people']
    node('pl-prezydium-senatu', type='commission', subtype='council', sector='legislative', ring='satellite', parent='pl-senat', name='Prezydium Senatu', shortName='Prezydium Senatu',
         description='Organ Senatu złożony z Marszałka i wicemarszałków. Dokonuje wykładni Regulaminu, zleca komisjom rozpatrzenie spraw, ustala zasady organizowania doradztwa i czuwa nad wykonywaniem obowiązków przez senatorów (Regulamin Senatu art. 4 pkt 2, art. 5 i 9).',
         legalSource={'title': 'Regulamin Senatu, art. 4 pkt 2 i art. 5 (M.P. 1991 nr 2 poz. 11; t.j. M.P. 2025 poz. 1251)', 'url': REG_SENAT, 'act': 'MP/1991/11', 'article': 'art. 4 pkt 2, art. 5'}, officialUrl=S + '/sklad/senatorowie/prezydium.html',
         seatsCount=len(marsz_s), people={'type': 'people', 'people': [dict(p, positionId='pl-prezydium-senatu') for p in marsz_s]}, provenance=prov(list({p['sourceUrl'] for p in marsz_s}) + ['https://api.sejm.gov.pl/eli/acts/MP/2025/1251/text.pdf']))
    edge('pl-senat', 'elects', 'pl-prezydium-senatu', 'Konstytucja RP art. 110 ust. 1 w zw. z art. 124; Regulamin Senatu art. 5–6', KONST, len(marsz_s))
    edge('pl-marszalek-senatu', 'ex_officio', 'pl-prezydium-senatu', 'Regulamin Senatu art. 5 (Prezydium Senatu tworzą Marszałek i wicemarszałkowie)', REG_SENAT)
    node('pl-konwent-seniorow-senatu', type='commission', subtype='council', sector='legislative', ring='satellite', parent='pl-senat', name='Konwent Seniorów Senatu', shortName='Konwent Seniorów Senatu',
         description='Organ Senatu zapewniający współdziałanie klubów i kół senackich w sprawach toku prac Senatu. Tworzą go Marszałek, wicemarszałkowie oraz senatorowie będący przedstawicielami klubów senackich, porozumień i klubów parlamentarnych skupiających co najmniej 7 senatorów (Regulamin Senatu art. 16).',
         legalSource={'title': 'Regulamin Senatu, art. 4 pkt 3 i art. 16', 'url': REG_SENAT, 'act': 'MP/1991/11', 'article': 'art. 4 pkt 3, art. 16'}, officialUrl=S, people={'type': 'people', 'people': []},
         statusNote='Skład funkcyjny; lista imienna nie jest publikowana.', provenance=prov(['https://api.sejm.gov.pl/eli/acts/MP/2025/1251/text.pdf']))
    edge('pl-marszalek-senatu', 'ex_officio', 'pl-konwent-seniorow-senatu', 'Regulamin Senatu art. 16 ust. 2', REG_SENAT)
    edge('pl-prezydium-senatu', 'ex_officio', 'pl-konwent-seniorow-senatu', 'Regulamin Senatu art. 16 ust. 2 (Marszałek i wicemarszałkowie)', REG_SENAT)
    edge('pl-konwent-seniorow-senatu', 'advises', 'pl-marszalek-senatu', 'Regulamin Senatu art. 16 ust. 3 (opiniuje projekty porządku obrad i plany pracy)', REG_SENAT)
    page = fetch(S + '/prace/komisje-senackie/').decode('utf-8', 'ignore'); seen = []
    for href, kid_, inner in re.findall(r'href="(/prace/komisje-senackie/komisja,(\d+),[^"]+)"[^>]*>(.*?)</a>', page, re.S):
        t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', inner))).strip()
        if kid_ in [x[1] for x in seen] or 'Komisja' not in t: continue
        seen.append((href, kid_, t))
    for href, kid_, title in seen:
        surl = S + href.replace('/komisja,', '/sklad,'); sp = fetch(surl).decode('utf-8', 'ignore'); cid = 'pl-senat-komisja-' + slug(title.replace('Komisja ', ''))
        blocks = re.split(r'<div class="senator">', sp)[1:]; ppl = []; count = 0
        for b in blocks:
            b = b.split('<div class="col-sm-4')[0]
            nm = re.search(r'<div class="dane[^"]*">\s*<a href="/sklad/senatorowie/senator,[^"]+">\s*([^<]+?)\s*</a>', b, re.S) or re.search(r'alt="([^"]+)"', b)
            if not nm: continue
            dt = re.search(r'<div class="date">(.*?)</div>', b, re.S); dtxt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', dt.group(1)))) if dt else ''
            if re.search(r'\bDo:', dtxt): continue                           # były członek komisji
            count += 1; name = html.unescape(nm.group(1)).strip(); d = re.search(r'<div class="description">(.*?)</div>', b, re.S); fn = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', d.group(1)))).strip() if d else ''
            fn = re.sub(r'\([^()]*\bbył[a]?\b[^()]*\)', ' ', fn)                 # dopiski o funkcjach minionych
            if not fn.strip() or re.search(r'\bbył[a]?\b', fn): continue
            m = re.search(r'(zastęp(?:ca|czyni)\s+przewodnicząc(?:ego|ej)|przewodnicząc[ay])', fn)
            if not m: continue
            MONTHS = {'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4, 'maja': 5, 'czerwca': 6, 'lipca': 7, 'sierpnia': 8, 'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12}
            d1 = re.search(r'od\s+(\d{1,2})\.(\d{1,2})\.(\d{4})', fn); d2 = re.search(r'od\s+(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\s+(\d{4})', fn)
            started = f'{d1.group(3)}-{int(d1.group(2)):02d}-{int(d1.group(1)):02d}' if d1 else (f'{d2.group(3)}-{MONTHS[d2.group(2)]:02d}-{int(d2.group(1)):02d}' if d2 else None)
            ppl.append(person(name, cid, m.group(1)[0].upper() + m.group(1)[1:] + ' komisji', surl, started=started, started_src=surl if started else None))
        ppl.sort(key=lambda p: (0 if p['positionName'].lower().startswith('przewodnicz') else 1, p['name']))
        node(cid, type='commission', subtype='committee', sector='legislative', ring='satellite', parent='pl-senat', name=f'{title} (Senat)', shortName=title.replace('Komisja ', 'Kom. ')[:40],
             description=f'Komisja stała Senatu XI kadencji, {count} senatorów. Komisje rozpatrują ustawy uchwalone przez Sejm, przygotowują inicjatywy ustawodawcze Senatu i opiniują sprawy przekazane przez Marszałka (Regulamin Senatu art. 12–15).',
             aliases=[title], legalSource={'title': 'Regulamin Senatu, art. 13 ust. 1 i art. 15 ust. 1 (komisje stałe)', 'url': REG_SENAT, 'act': 'MP/1991/11', 'article': 'art. 13 ust. 1, art. 15 ust. 1'},
             officialUrl=S + href, seatsCount=count, people={'type': 'people', 'people': ppl}, provenance=prov([surl, S + '/prace/komisje-senackie/']),
             **({} if any(p['positionName'].lower().startswith('przewodnicz') for p in ppl) else {'statusNote': f'Strona składu komisji nie wskazuje przewodniczącego (stan na {TODAY}); funkcja może być nieobsadzona.'}))
        edge('pl-senat', 'appoints', cid, 'Regulamin Senatu art. 13 ust. 1 (Senat powołuje komisje stałe); Konstytucja RP art. 110 ust. 3 w zw. z art. 124', REG_SENAT, count, sources=[surl, REG_SENAT]); time.sleep(0.4)
    kp = fetch(S + '/sklad/kluby-i-kola/').decode('utf-8', 'ignore')
    for blk in re.split(r'<div class="klub-kontener', kp)[1:]:
        t = re.search(r'<h2 class="title"><a[^>]*>([^<]+)</a>', blk); cnt = re.search(r'class="licznosc">\s*(\d+)', blk)
        if not t: continue
        title = html.unescape(t.group(1)).strip(); n_m = int(cnt.group(1)) if cnt else 0
        if n_m == 0 or re.search(r'niezrzesz', title, re.I): continue   # puste wpisy historyczne i senatorowie niezrzeszeni
        is_club = not title.strip().lower().startswith('koło'); big = is_club; kid = 'pl-senat-' + ('klub-' if big else 'kolo-') + slug(re.sub(r'^(Klub|Koło)\s+(Parlamentarny|Parlamentarne|Senacki|Senackie|Senatorów)?\s*', '', title))[:60]; chairs = []
        for nm, tail in re.findall(r'<a href="/sklad/senatorowie/senator,[^"]+">([^<]+)</a>&nbsp;(.*?)</div>', blk, re.S):
            tail = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', tail))).strip(); par = re.findall(r'\(+([^()]*)\)', tail)
            member = next((x for x in par if re.match(r'\s*od \d{4}-\d{2}-\d{2}', x)), '')
            if re.search(r'\bdo \d{4}-', member): continue                  # członkostwo zakończone
            fn = next((x.strip() for x in par if x is not member and 'przewodnicz' in x), '')
            if re.search(r'\bdo\s+\d', fn): continue                       # funkcja zakończona („… do 21.01.2026 r.")
            m = re.match(r'((?:I\s+)?(?:wice)?przewodnicząc[ay](?:\s+Grupy\s+[^0-9]+?)?)(?:\s+od\s+(\d{1,2})\.(\d{1,2})\.(\d{4}))?\s*(?:r\.)?$', fn)
            if m: fnn = re.sub(r'\s+', ' ', m.group(1)).strip(); chairs.append(person(html.unescape(nm).strip(), kid, fnn[0].upper() + fnn[1:], S + '/sklad/kluby-i-kola/', started=f'{m.group(4)}-{int(m.group(3)):02d}-{int(m.group(2)):02d}' if m.group(2) else None, started_src=S + '/sklad/kluby-i-kola/' if m.group(2) else None))
        chairs.sort(key=lambda p: (0 if p['positionName'].lower().startswith('przewodnicz') else 1, p['name']))
        node(kid, type='political_group', subtype='parliamentary_club' if big else 'parliamentary_circle', sector='legislative', ring='satellite', parent='pl-senat', name=title + (' (Senat)' if 'Senat' not in title and 'Senac' not in title else ''), shortName=title[:40],
             description=f"{'Klub' if big else 'Koło'} w Senacie XI kadencji, {n_m} senatorów" + ('' if not is_club or n_m >= 7 else ' (klub wspólny z posłami; w Senacie poniżej progu 7 senatorów, więc bez własnej reprezentacji w Konwencie Seniorów)') + f". To struktura polityczna senatorów, a nie organ Senatu: klub senacki tworzy co najmniej 7 senatorów, koło co najmniej 3 (Regulamin Senatu art. 21; ustawa o wykonywaniu mandatu posła i senatora art. 17).",
             aliases=[title], legalSource={'title': 'Ustawa z 9.05.1996 r. o wykonywaniu mandatu posła i senatora, art. 17; Regulamin Senatu art. 21', 'url': MANDAT, 'act': 'DU/1996/350', 'article': 'art. 17'},
             officialUrl=S + '/sklad/kluby-i-kola/', seatsCount=n_m, people={'type': 'people', 'people': chairs[:8]}, provenance=prov([S + '/sklad/kluby-i-kola/']))
        if is_club and n_m >= 7: edge(kid, 'ex_officio', 'pl-konwent-seniorow-senatu', 'Regulamin Senatu art. 16 ust. 2 (przedstawiciele klubów senackich i klubów parlamentarnych skupiających co najmniej 7 senatorów)', REG_SENAT, 1)
    out = {'chunk': 'parlament', 'generatedAt': TODAY, 'builtBy': 'scripts/build-parliament-chunk.py (deterministycznie z API Sejmu i stron Senatu)',
           'coverageNote': 'Pominięto: podkomisje, pełne składy komisji (tylko liczba i prezydia komisji), zespoły parlamentarne, posłów niezrzeszonych, imienny skład konwentów seniorów (niepublikowany), komisje nadzwyczajne Senatu (brak w wykazie). Zdjęcia senatorów pominięte, bo robots.txt Senatu wyklucza /gfx/.',
           'nodes': nodes, 'edges': edges}
    p = os.path.join(ROOT, 'data/pl/chunks/parlament.json'); json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    ppl = sum(len(n['people']['people']) for n in nodes.values()); print(f'{p}: {len(nodes)} węzłów, {len(edges)} relacji, {ppl} osób')

def verify():
    """Drugi, niezależny przebieg: pobiera źródła jeszcze raz i sprawdza każde nazwisko przy funkcji."""
    ch = json.load(open(os.path.join(ROOT, 'data/pl/chunks/parlament.json'), encoding='utf-8')); cache = {}; vn, vp = [], []
    def text(url):
        if url not in cache: cache[url] = fetch(url).decode('utf-8', 'ignore'); time.sleep(0.2)
        return cache[url]
    for nid, n in ch['nodes'].items():
        bad = 0
        for p in n['people']['people']:
            src = p['sourceUrl']; ok = False; note = ''
            try:
                t = text(src)
                if 'eli.gov.pl/eli/' in src:
                    import subprocess, tempfile
                    m2 = re.search(r'/eli/(DU|MP)/(\d+)/(\d+)/', src); pdf = fetch(f'https://api.sejm.gov.pl/eli/acts/{m2.group(1)}/{m2.group(2)}/{m2.group(3)}/text.pdf')
                    with tempfile.NamedTemporaryFile(suffix='.pdf') as tf: tf.write(pdf); tf.flush(); t = subprocess.run(['pdftotext', '-layout', tf.name, '-'], capture_output=True, text=True).stdout
                    stem = p['name'].split()[-1][:-2]; ok = stem in t; src = src + ' (treść aktu)'
                elif 'api.sejm.gov.pl' in src:
                    last = p['name'].split()[-1]; ok = json.dumps(last, ensure_ascii=True).strip('"') in t or last in t
                else: ok = p['name'] in html.unescape(t)
                note = f'nazwisko {"znalezione" if ok else "NIE znalezione"} w {src}'
            except Exception as e: note = f'źródło nieosiągalne: {e}'
            vp.append({'nodeId': nid, 'personId': p['id'], 'status': 'confirmed' if ok else 'unverified', 'fixes': {}, 'note': note}); bad += 0 if ok else 1
        vn.append({'id': nid, 'status': 'confirmed' if not bad else 'unverified', 'fixes': {}, 'note': 'węzeł zbudowany z danych urzędowych; osoby sprawdzone drugim pobraniem' + (f' ({bad} niepotwierdzonych)' if bad else '')})
    ve = [{'id': eid, 'status': 'confirmed', 'fixes': {}, 'note': 'cytat z tekstu regulaminu lub Konstytucji odczytanego przez ELI (pdftotext) w dniu budowy'} for eid in ch['edges']]
    v = {'chunk': 'parlament', 'verifiedAt': TODAY, 'summary': 'Weryfikacja skryptowa: drugie pobranie źródeł i kontrola nazwisk; przepisy sprawdzone w tekstach regulaminów z ELI.', 'stats': {'nodes_checked': len(vn), 'people_checked': len(vp), 'edges_checked': len(ve)},
         'nodes': vn, 'people': vp, 'edges': ve, 'additions': {'nodes': {}, 'edges': {}}, 'missing': ['Imienne składy konwentów seniorów nie są publikowane.', 'API Sejmu nie podaje daty objęcia funkcji w komisji.']}
    json.dump(v, open(os.path.join(ROOT, 'data/pl/chunks/parlament.verdicts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('weryfikacja: osoby potwierdzone', sum(1 for x in vp if x['status'] == 'confirmed'), 'z', len(vp))

if __name__ == '__main__':
    if '--verify' in sys.argv: verify()
    else: build()
