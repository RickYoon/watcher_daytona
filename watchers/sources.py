"""Three watch sources. Each returns a list of {id, title, text, url}. No API keys."""
import hashlib, json, re, urllib.parse
import feedparser, requests

UA = {"User-Agent": "Mozilla/5.0 WatchBox/0.1"}

def news_rss(query, limit=10):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(requests.get(url, headers=UA, timeout=20).content)
    out = []
    for e in feed.entries[:limit]:
        out.append({"id": e.get("id") or e.link, "title": e.title, "text": re.sub("<[^>]+>", "", e.get("summary", ""))[:400], "url": e.link})
    return out

def page_text(url):
    raw = requests.get(url, headers=UA, timeout=20).text
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return [{"id": hashlib.md5(text.encode()).hexdigest(), "title": url, "text": text[:3000], "url": url}]

def price(symbol):
    """symbol: 'KRW-BTC' (Upbit) or 'USD' (KRW per USD via open.er-api)."""
    if "-" in symbol:
        v = requests.get(f"https://api.upbit.com/v1/ticker?markets={symbol}", headers=UA, timeout=15).json()[0]["trade_price"]
    else:
        v = requests.get("https://open.er-api.com/v6/latest/USD", headers=UA, timeout=15).json()["rates"]["KRW"] if symbol.upper() == "USD" else None
    return [{"id": f"{symbol}:{v}", "title": symbol, "text": str(v), "url": "", "value": v}]
