# Helpers for the daily NEWS refresh (run from the repo root).
# usage: python3 heads.py URL [pattern] — lists article links (title | url) found on a section page
import sys, subprocess, re, html
url = sys.argv[1]; pat = sys.argv[2] if len(sys.argv) > 2 else r"/20\d\d/|/news/|/buzz/"
t = subprocess.run(["curl", "-sS", "-L", "-m", "25", url], capture_output=True, text=True, errors="ignore").stdout
seen = set()
for href, inner in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', t, re.S):
    title = html.unescape(re.sub(r"<[^>]+>|\s+", " ", inner)).strip()
    if len(title) > 35 and re.search(pat, href) and href not in seen:
        seen.add(href); print(title[:120], "|", href if href.startswith("http") else url.split("/")[0] + "//" + url.split("/")[2] + href)
