# Helpers for the daily NEWS refresh (run from the repo root).
# usage: python3 fashionday.py DATE [fun.json] — copies DATE's items from fashion-week.json into fun.json
# (replacing any fashion items already there). Good-news items in fun.json are kept.
import json, sys
day = sys.argv[1]; path = sys.argv[2] if len(sys.argv) > 2 else "fun.json"
week = json.load(open("fashion-week.json"))
picks = [dict((k, v) for k, v in x.items() if k not in ("day", "published", "category")) for x in week["items"] if x["day"] == day]
if not picks:
    sys.exit(f"no fashion items for {day} in fashion-week.json ({week['weekStart']} to {week['weekEnd']}): collect a new week first")
fun = json.load(open(path))
good = [x for x in fun["items"] if x.get("type") != "fashion"]
used = {x["color"] for x in good}
pal = ["#7c2d12", "#1e3a8a", "#14532d", "#581c87", "#9f1239", "#0f766e", "#78350f", "#334155", "#831843", "#155e75", "#3f6212", "#4c1d95"]
for x in picks:  # keep colours unique within the day's fun deck
    if x["color"] in used: x["color"] = next(c for c in pal if c not in used)
    used.add(x["color"])
fun["items"] = picks + good
json.dump(fun, open(path, "w"), ensure_ascii=False, indent=1); open(path, "a").write("\n")
print(f"{day}: {len(picks)} fashion items from {len({x['source'] for x in picks})} publishers + {len(good)} good-news items")
