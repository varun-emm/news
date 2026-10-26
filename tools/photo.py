# Helpers for the daily NEWS refresh (run from the repo root).
# usage: python3 photo.py queries.json out.json — finds a freely licensed Wikimedia Commons photo per query
import json, sys, subprocess, re, html, urllib.parse, time
UA = "NEWS-personal-reader/1.0 (https://varun-emm.github.io/news; personal non-commercial news reader)"
OK = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0|Public domain|PD.*)$", re.I)
def search(q):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 12,
        "gsrsearch": q + " filetype:bitmap", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1200})
    for _ in range(3):
        r = subprocess.run(["curl", "-sS", "-m", "30", "-A", UA, url], capture_output=True, text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(3)
    return {}
qs = json.load(open(sys.argv[1])); out = {}
for sid, q in qs.items():
    pages = sorted(search(q).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]; m = ii.get("extmetadata", {})
        lic = html.unescape(m.get("LicenseShortName", {}).get("value", ""))
        if "logo" in p["title"].lower() or ii.get("mime") != "image/jpeg" or not OK.match(lic) or ii.get("width", 0) < 900 or ii.get("width", 0) < ii.get("height", 1) * 0.9:
            continue
        artist = html.unescape(re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", ""))).strip() or "Unknown"
        out[sid] = {"url": ii.get("thumburl") or ii["url"], "credit": f"{artist[:60]} / Wikimedia Commons", "creditUrl": ii["descriptionurl"], "license": lic, "title": p["title"]}
        break
    print(sid, "|", q, "->", out.get(sid, {}).get("title", "NONE"), "|", out.get(sid, {}).get("license", ""))
    time.sleep(1)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
