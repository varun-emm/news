# Helpers for the daily NEWS refresh (run from the repo root).
# usage: python3 peek.py URL [chars] — prints status, title, description, og:image and the opening article text
import sys, subprocess, re, html
url = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
r = subprocess.run(["curl", "-sS", "-L", "-m", "25", "-w", "\n%{http_code}", url], capture_output=True, text=True, errors="ignore")
body, code = r.stdout.rsplit("\n", 1) if "\n" in r.stdout else (r.stdout, "?")
def meta(p):
    m = re.search(r'<meta[^>]+(?:property|name)=["\']' + p + r'["\'][^>]+content=["\']([^"\']+)', body, re.I) or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']' + p, body, re.I)
    return html.unescape(m.group(1)) if m else ""
paras = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", body, re.S)]
text = " ".join(p for p in paras if len(p) > 60)
print("HTTP", code, "|", meta("og:title"))
print("DESC:", meta("og:description")[:300]); print("IMG:", meta("og:image") or meta("twitter:image"))
print("TEXT:", text[:n])
