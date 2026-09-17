#!/usr/bin/env python3
"""Wysyła projekt na GitHuba przez API (gh), bez lokalnego gita. Jedno uruchomienie = jeden commit z pełnym stanem katalogu.
Pomija wszystko, co pasuje do .gitignore (prosta obsługa: katalogi „nazwa/”, ścieżki dokładne i wzorce z „*”).
Wysyła tylko pliki, których treść różni się od tej w repozytorium (porównanie po skrócie SHA-1 obiektu git).
Użycie: python3 scripts/publish-github.py <właściciel/repo> "opis zmiany" [--dry-run]
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
ref = gh('GET', f'repos/{repo}/git/ref/heads/{BRANCH}'); parent = ref['object']['sha']; base_tree = gh('GET', f'repos/{repo}/git/commits/{parent}')['tree']['sha']
remote = {t['path']: t['sha'] for t in gh('GET', f'repos/{repo}/git/trees/{base_tree}?recursive=1').get('tree', []) if t['type'] == 'blob'}
tree = []; sent = 0
for rel, (sha, mode, data) in local.items():
    if remote.get(rel) != sha:
        got = gh('POST', f'repos/{repo}/git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'})['sha']; assert got == sha, rel; sent += 1
    tree.append({'path': rel, 'mode': mode, 'type': 'blob', 'sha': sha})
removed = [p for p in remote if p not in local]
if not sent and not removed: print('bez zmian'); raise SystemExit(0)
new_tree = gh('POST', f'repos/{repo}/git/trees', {'tree': tree})['sha']   # pełne drzewo: pliki usunięte lokalnie znikają też z repozytorium
commit = gh('POST', f'repos/{repo}/git/commits', {'message': message, 'tree': new_tree, 'parents': [parent]})['sha']
gh('PATCH', f'repos/{repo}/git/refs/heads/{BRANCH}', {'sha': commit})
print(f'wysłano plików: {sent}, usunięto: {len(removed)}, commit {commit[:10]}')
