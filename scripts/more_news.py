"""Research extra Daily Swipe stories for today and append them to more.json.

Run by .github/workflows/more-news.yml when the "More news" button is pressed.
Needs ANTHROPIC_API_KEY. COUNT (1-10) sets how many stories to add.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import anthropic

MODEL = "claude-opus-5-5"
IST = timezone(timedelta(hours=5, minutes=30))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FALLBACK = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

client = anthropic.Anthropic()

STORY_SCHEMA = {
    "type": "object",
    "properties": {
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "enum": ["world", "india", "money"]},
                    "source": {"type": "string"},
                    "kicker": {"type": "string"},
                    "emoji": {"type": "string"},
                    "stat": {"type": "string"},
                    "statLabel": {"type": "string"},
                    "headline": {"type": "string"},
                    "body": {"type": "array", "items": {"type": "string"}},
                    "joke": {"type": "string"},
                    "vc": {"type": "string"},
                    "url": {"type": "string"},
                    "linkLabel": {"type": "string"},
                    "color": {"type": "string"},
                    "font": {"type": "string", "enum": ["editorial", "news", "impact", "tech", "finance", "serious"]},
                    "image": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "credit": {"type": "string"},
                            "creditUrl": {"type": "string"},
                        },
                        "required": ["url", "credit", "creditUrl"],
                        "additionalProperties": False,
                    },
                },
                "required": ["section", "source", "kicker", "emoji", "stat", "statLabel", "headline",
                             "body", "joke", "vc", "url", "linkLabel", "color", "font", "image"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["stories"],
    "additionalProperties": False,
}

RESEARCH_PROMPT = """You find extra stories for Varun's "Daily Swipe" news app. Varun lives in Bangalore, runs a manufacturing/trading business, and wants to become a purposeful VC who helps startups.

Today is {date} (Asia/Kolkata). Find {count} NEW stories from the last 24 hours that are NOT already in the deck below. Mix them: world (different regions, not only US), India (markets, business, startups, policy), and money/VC/tech. Prefer big, consequential news.

Already in today's deck (do not repeat these topics):
{existing}

For each story:
1. Use web search, then fetch the article page to get real facts. Never invent facts or numbers.
2. Find one FREE Unsplash photo that fits the topic: search "unsplash photo <topic>", fetch the photo page, and take the direct images.unsplash.com/photo-... URL plus the photographer's name and the photo page URL. Only use photos marked "Free to use under the Unsplash License"; skip plus.unsplash.com. Do not reuse these photos: {used_images}

Finish with plain notes for each story: section, source name, article URL, the key facts (with numbers), one headline-worthy statistic, the photo URL, photographer and photo page URL."""

FORMAT_PROMPT = """Turn these research notes into Daily Swipe stories for {date}.

Rules:
- section is world, india or money. source is a short source name; linkLabel is the site name; url is the article URL from the notes.
- kicker: 2-3 word topic. emoji: one emoji. stat: max ~12 chars (a number like "-16%", "$1B", "22x", "47% vs 45%", "Dec 7", or a short phrase). statLabel: max ~6 words.
- headline: max ~10 words. body: exactly 3 short sentences in basic English, under ~70 words total; the first sentence must work alone as a 2-line description.
- joke: one light, witty, sarcastic line, never partisan. Use "" for deaths, disasters, attacks or other tragedy.
- vc: 1-2 sentences on why it matters to a VC or wealth-builder.
- color: a hex colour that suits THIS story's mood (not its section), dark enough for white text, and different from: {colors}.
- font: the headline typeface that suits the story: "news" (politics, elections, diplomacy, conflict), "impact" (big market moves, IPOs, surges and crashes), "tech" (AI, startups, software, chips), "finance" (economy, banks, rates, funds, analysis), "serious" (deaths, disasters, health crises), or "editorial" (anything else).
- image.url: the images.unsplash.com URL with "?auto=format&fit=crop&w=1200&q=70" appended (replace any existing query). credit: photographer. creditUrl: the unsplash.com photo page.
- Rewrite everything in your own words. No quotes longer than 10 words. Only use facts from the notes; drop a story if the notes are too thin.

Notes:
{notes}"""


def load(path, default):
    try:
        with open(os.path.join(ROOT, path)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def research(date, count, existing, used_images):
    messages = [{"role": "user", "content": RESEARCH_PROMPT.format(
        date=date, count=count, existing="\n".join(f"- {h}" for h in existing) or "- (none)",
        used_images=", ".join(used_images) or "(none)")}]
    tools = [
        {"type": "web_search_20260209", "name": "web_search", "max_uses": 20},
        {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 30},
    ]
    turn = []  # the assistant turn so far, across pause_turn continuations
    for _ in range(6):
        with client.beta.messages.stream(
            model=MODEL, max_tokens=64000, tools=tools, messages=messages,
            output_config={"effort": "high"}, **FALLBACK,
        ) as stream:
            response = stream.get_final_message()
        if response.stop_reason == "refusal":
            sys.exit(f"Research was declined: {response.stop_details}")
        turn += response.content
        if response.stop_reason != "pause_turn":
            return "\n".join(b.text for b in turn if b.type == "text")
        messages = messages[:1] + [{"role": "assistant", "content": turn}]
    sys.exit("Research did not finish after several continuations")


def to_stories(date, notes, colors):
    with client.beta.messages.stream(
        model=MODEL, max_tokens=32000,
        messages=[{"role": "user", "content": FORMAT_PROMPT.format(date=date, notes=notes, colors=", ".join(colors))}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": STORY_SCHEMA}}, **FALLBACK,
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "refusal":
        sys.exit(f"Formatting was declined: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        sys.exit("Formatting ran out of tokens")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)["stories"]


def valid(s, seen_headlines):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", s["color"]):
        return False
    if not s["url"].startswith("https://") or not s["image"]["url"].startswith("https://images.unsplash.com/"):
        return False
    if len(s["body"]) < 2 or not s["headline"].strip():
        return False
    return s["headline"].strip().lower() not in seen_headlines


def main():
    count = os.environ.get("COUNT", "5")
    count = int(count) if count.isdigit() else 5
    count = max(1, min(10, count))

    news = load("news.json", None)
    if not news:
        sys.exit("news.json is missing")
    date = news["date"]
    more = load("more.json", {})
    extra = more.get("stories", []) if more.get("date") == date else []
    deck = news["stories"] + extra

    notes = research(date, count, [s["headline"] for s in deck], [s["image"]["url"].split("?")[0] for s in deck if s.get("image")])
    stories = to_stories(date, notes, [s.get("color", "") for s in deck])

    seen = {s["headline"].strip().lower() for s in deck}
    added = []
    for s in stories:
        if len(added) >= count or not valid(s, seen):
            continue
        seen.add(s["headline"].strip().lower())
        s["id"] = f"{date}-x{len(extra) + len(added) + 1}"
        s["image"]["url"] = s["image"]["url"].split("?")[0] + "?auto=format&fit=crop&w=1200&q=70"
        added.append({"id": s.pop("id"), **s})
    if not added:
        sys.exit("No usable new stories this time")

    out = {"date": date, "generatedAt": datetime.now(IST).isoformat(timespec="seconds"), "stories": extra + added}
    with open(os.path.join(ROOT, "more.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Added {len(added)} stories:")
    for s in added:
        print(f"  [{s['section']}] {s['headline']}")


if __name__ == "__main__":
    main()
