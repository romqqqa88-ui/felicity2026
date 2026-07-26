import urllib.request, urllib.parse, re, sys

sys.stdout.reconfigure(encoding='utf-8')

qc = "погода в Старом Осколе"
url = "https://lite.duckduckgo.com/lite/"
data = urllib.parse.urlencode({'q': qc}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Content-Type': 'application/x-www-form-urlencoded'
})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

# Match table rows in Lite HTML
rows = re.findall(r'<td class=\'result-snippet\'>(.*?)</td>', html, re.DOTALL)
if not rows:
    rows = re.findall(r'<td[^>]*class="[^"]*snippet[^"]*"[^>]*>(.*?)</td>', html, re.DOTALL)
if not rows:
    # Match any text in td elements after links
    rows = re.findall(r'<td[^>]*>\s*([А-Яа-яA-Za-z0-9\s\.,\-—–\:\%\+\°\«\»]+)\s*</td>', html)

print(f"Found {len(rows)} rows:")
for r in rows[:5]:
    t = re.sub(r'<[^>]+>', '', r).strip()
    t = re.sub(r'\s+', ' ', t)
    if len(t) > 20:
        print(" ->", t)
