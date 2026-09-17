#!/usr/bin/env python3
"""Wysyła projekt na GitHuba przez API (gh), bez lokalnego gita. Jedno uruchomienie = jeden commit z pełnym stanem katalogu.
Pomija wszystko, co pasuje do .gitignore (prosta obsługa: katalogi „nazwa/”, ścieżki dokładne i wzorce z „*”).
Wysyła tylko pliki, których treść różni się od tej w repozytorium (porównanie po skrócie SHA-1 obiektu git).
Bez gita trzeba samemu pilnować zmian zrobionych w repozytorium przez kogoś innego (np. bota cotygodniowej aktualizacji):
skrypt pamięta w .publish-state.json skróty plików z repozytorium po swojej ostatniej publikacji albo pobraniu.
Plik zmieniony tylko w repozytorium jest pobierany na dysk; zmieniony po obu stronach zatrzymuje publikację.
Użycie: python3 scripts/publish-github.py <właściciel/repo> "opis zmiany" [--dry-run] [--pull-only] [--exclude wzorzec]…
"""
import base64, fnmatch, hashlib, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo, message = sys.argv[1], sys.argv[2]; dry = '--dry-run' in sys.argv; BRANCH = 'main'
def gh(method, path, body=None):
    cmd = ['gh', 'api', '-X', method, path]; inp = None
    if body is not None: cmd += ['--input', '-']; inp = json.dumps(body).encode()
    r = subprocess.run(cmd, input=inp, capture_output=True)
    if r.returncode != 0: raise SystemExit(f'gh api {method} {path}: {r.stderr.decode()[:400]}')
    return json.loads(r.stdout) if r.stdout.strip() else {}
rules = [l.strip() for l in open(os.path.join(ROOT, '.gitignore'), encoding='utf-8') if l.strip() and not l.startswith('#')]
rules += [sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == '--exclude']  # doraźne pominięcie plików w toku pracy: --exclude 'scripts/build-budget.py'
def ignored(rel):
    parts = rel.split('/')
    for rule in rules:
        if rule.endswith('/'):
            d = rule.rstrip('/')
            if ('/' in d and (rel == d or rel.startswith(d + '/'))) or ('/' not in d and d in parts[:-1]): return True
        elif '/' in rule:
            if fnmatch.fnmatch(rel, rule): return True
        elif fnmatch.fnmatch(parts[-1], rule): return True
    return False
files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = sorted(d for d in dn if d != '.git' and not ignored(os.path.relpath(os.path.join(dp, d), ROOT).replace(os.sep, '/') + '/x'))
    for f in sorted(fn):
        rel = os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, '/')
        if not ignored(rel): files.append(rel)
def blob_sha(data): return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
local = {}
for rel in files:
    data = open(os.path.join(ROOT, rel), 'rb').read(); mode = '100755' if os.access(os.path.join(ROOT, rel), os.X_OK) and rel.endswith(('.sh', '.py')) else '100644'
    local[rel] = (blob_sha(data), mode, data)
total = sum(len(v[2]) for v in local.values()); print(f'plików do repozytorium: {len(local)}, razem {total / 1e6:.1f} MB')
if dry:
    for rel in files: print(' ', rel)
    big = sorted(local.items(), key=lambda kv: -len(kv[1][2]))[:6]; print('największe:', [(k, f'{len(v[2]) / 1e6:.2f} MB') for k, v in big]); raise SystemExit(0)
ref = gh('GET', f'repos/{repo}/git/ref/heads/{BRANCH}'); parent = ref['object']['sha']
force = '--replace-last' in sys.argv  # cofnięcie ostatniego commita: nowy commit staje na jego rodzicu, a gałąź jest przestawiana siłowo (np. gdy do repo trafiły pliki, których miało nie być)
if force: parent = gh('GET', f'repos/{repo}/git/commits/{parent}')['parents'][0]['sha']
base_tree = gh('GET', f'repos/{repo}/git/commits/{parent}')['tree']['sha']
remote = {t['path']: t['sha'] for t in gh('GET', f'repos/{repo}/git/trees/{base_tree}?recursive=1').get('tree', []) if t['type'] == 'blob'}
# --- synchronizacja z repozytorium. Stan = skróty plików W REPOZYTORIUM widziane przy ostatniej publikacji albo pobraniu (nigdy skróty lokalne).
SP = os.path.join(ROOT, '.publish-state.json'); last = json.load(open(SP)) if os.path.exists(SP) else {}
pulled, conflicts = [], []
for path, rsha in remote.items():
    if force or ignored(path): continue
    lsha = local[path][0] if path in local else None; base = last.get(path)
    if rsha == lsha or rsha == base: continue                      # zgodne albo repozytorium bez zmian od ostatniego razu (zmieniałem najwyżej ja)
    if base is None: continue                                      # nie znam historii tej ścieżki: niczego nie nadpisuję, wygrywa plik lokalny
    if lsha is None or lsha == base:                               # zmiana wyłącznie w repozytorium: pobierz
        data = base64.b64decode(gh('GET', f'repos/{repo}/git/blobs/{rsha}')['content']); full = os.path.join(ROOT, path); os.makedirs(os.path.dirname(full), exist_ok=True); open(full, 'wb').write(data)
        local[path] = (rsha, local.get(path, (None, '100644'))[1], data); pulled.append(path)
    else: conflicts.append(path)
if pulled: print('pobrano z repozytorium:', ', '.join(pulled))
if conflicts: raise SystemExit('KONFLIKT, plik zmieniony i lokalnie, i w repozytorium: ' + ', '.join(conflicts) + '. Rozstrzygnij ręcznie i uruchom ponownie.')
if '--pull-only' in sys.argv:
    json.dump(remote, open(SP, 'w'), indent=0, sort_keys=True); print('tylko pobranie: gotowe'); raise SystemExit(0)
tree = []; sent = 0
for rel, (sha, mode, data) in local.items():
    if remote.get(rel) != sha:
        got = gh('POST', f'repos/{repo}/git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'})['sha']; assert got == sha, rel; sent += 1
    tree.append({'path': rel, 'mode': mode, 'type': 'blob', 'sha': sha})
removed = [p for p in remote if p not in local]
if not sent and not removed: json.dump(remote, open(SP, 'w'), indent=0, sort_keys=True); print('bez zmian'); raise SystemExit(0)
new_tree = gh('POST', f'repos/{repo}/git/trees', {'tree': tree})['sha']   # pełne drzewo: pliki usunięte lokalnie znikają też z repozytorium
commit = gh('POST', f'repos/{repo}/git/commits', {'message': message, 'tree': new_tree, 'parents': [parent]})['sha']
gh('PATCH', f'repos/{repo}/git/refs/heads/{BRANCH}', {'sha': commit, 'force': force})
json.dump({p: v[0] for p, v in local.items()}, open(SP, 'w'), indent=0, sort_keys=True)  # po publikacji repozytorium = stan lokalny
print(f'wysłano plików: {sent}, usunięto: {len(removed)}, commit {commit[:10]}')
