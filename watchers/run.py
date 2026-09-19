"""One watcher = one Daytona sandbox running this loop. Reads params.json next to it."""
import json, os, sys, time, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources, brain

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "params.json")))
SEEN = os.path.join(HERE, "seen.json")
LOG = os.path.join(HERE, "watch.log")
TG = f"https://api.telegram.org/bot{P['tg_token']}/sendMessage"

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")

def notify(text):
    requests.post(TG, json={"chat_id": P["chat_id"], "text": text, "disable_web_page_preview": True}, timeout=20)

def fetch():
    t = P["type"]
    if t == "news": return sources.news_rss(P["query"])
    if t == "page": return sources.page_text(P["query"])
    if t == "price": return sources.price(P["query"])
    raise ValueError(t)

def check(items, seen, first_run=False):
    hits = []
    for it in items:
        if it["id"] in seen: continue
        seen.add(it["id"])
        if P["type"] == "price":
            v, th, op = it["value"], float(P["threshold"]), P.get("op", "<")
            ok = v < th if op == "<" else v > th
            if ok: hits.append((it, f"{P['query']} = {v:,.0f} ({op} {th:,.0f})", "rule"))
            continue
        if first_run and P["type"] == "news":
            continue  # don't spam old headlines on start; /test covers them
        m, reason, model = brain.judge(P["condition"], it)
        log(f"judge {m} [{model}] {it['title'][:50]} — {reason}")
        if m: hits.append((it, reason, model))
    return hits

if __name__ == "__main__":
    seen = set(json.load(open(SEEN))) if os.path.exists(SEEN) else set()
    first = not seen
    log(f"start watch#{P['id']} type={P['type']} q={P['query']} every {P['interval_min']}m")
    while True:
        try:
            hits = check(fetch(), seen, first_run=first)
            first = False
            for it, reason, model in hits:
                notify(f"🔔 감시 #{P['id']} 조건 충족\n{it['title']}\n{it['url']}\n— {reason}\n[{model}]")
            json.dump(sorted(seen), open(SEEN, "w"))
        except Exception as e:
            log(f"error {e}")
        time.sleep(int(P["interval_min"]) * 60)
