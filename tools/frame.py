# Helpers for the daily NEWS refresh (run from the repo root).
# usage: python3 frame.py fun.json — marks each item "embed": true when its site lets other pages show it in a frame
import json, sys, subprocess, re
def frameable(url):
    r = subprocess.run(["curl", "-sS", "-I", "-L", "-m", "20", url], capture_output=True, text=True, errors="ignore").stdout
    last = r.split("\nHTTP/")[-1] if "\nHTTP/" in r else r  # headers of the final response
    if not re.search(r"^(HTTP/)?\S*\s*200", last.strip(), re.I): return False
    if re.search(r"^x-frame-options:\s*(deny|sameorigin)", last, re.I | re.M): return False
    fa = re.search(r"frame-ancestors([^;\n]*)", last, re.I)
    return not fa or "*" in fa.group(1).split()
path = sys.argv[1]; d = json.load(open(path))
for x in d["items"]:
    x["embed"] = frameable(x["url"]); print(x["id"], x["embed"], x["url"])
open(path, "w").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
