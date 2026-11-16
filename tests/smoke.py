"""Tests HTTP reels, sans dependance. Ne supprime aucune donnee."""
import argparse
import html
import http.cookiejar
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8080')
parser.add_argument('--persistence', action='store_true')
args = parser.parse_args()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def request(path, fields=None):
    data = None if fields is None else urllib.parse.urlencode(fields).encode()
    try:
        with client.open(args.url + path, data=data, timeout=10) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()

for attempt in range(60):
    try:
        status, body = request('/health.php')
        if status == 200 and body == 'OK':
            break
    except (OSError, urllib.error.URLError):
        pass
    time.sleep(2)
else:
    raise SystemExit('ECHEC : service indisponible apres 120 secondes')

marker_file = Path(__file__).with_name('.persistence-marker')
status, page = request('/')
assert status == 200
if args.persistence:
    marker = marker_file.read_text()
    assert marker in page, 'Article perdu apres recreation des conteneurs'
    print('OK : persistance apres suppression/recreation des conteneurs')
    raise SystemExit(0)

token = re.search(r'name="csrf" value="([a-f0-9]+)"', page).group(1)
assert request('/validation.php')[0] == 405
assert request('/validation.php', {'title': 'interdit'})[0] == 403
assert request('/validation.php', {'csrf': token, 'title': ' ', 'author': 'Test', 'content': 'x'})[0] == 422
assert request('/validation.php', {'csrf': token, 'title': 'x' * 101, 'author': 'Test', 'content': 'x'})[0] == 422
assert request('/validation.php', {'csrf': token, 'title': ['x'], 'author': 'Test', 'content': ''})[0] == 422
marker = 'Persistance-' + str(time.time_ns())
payload = '<script>alert("xss")</script>'
status, page = request('/validation.php', {'csrf': token, 'title': marker, 'author': 'Test integration', 'content': payload})
assert status == 200 and marker in page
assert html.escape(payload, quote=True) in page and payload not in page, 'Echappement XSS absent'
marker_file.write_text(marker)
print('OK : sante, lecture, ajout, validation, CSRF, XSS et marqueur de persistance')
