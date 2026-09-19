"""LLM calls. Primary: Nosana-hosted Ollama (OpenAI-compatible). Fallback: Anthropic API."""
import json, os, re, requests

NOSANA_URL = os.environ.get("NOSANA_LLM_URL", "").rstrip("/")
NOSANA_MODEL = os.environ.get("NOSANA_MODEL", "qwen3.5:9b")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def _nosana(system, user, timeout=120):
    # Ollama native chat: think=False skips the reasoning pass (Qwen 3.6 is a thinking model)
    r = requests.post(f"{NOSANA_URL}/api/chat", timeout=timeout, json={
        "model": NOSANA_MODEL, "stream": False, "think": False, "options": {"temperature": 0},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    r.raise_for_status()
    return r.json()["message"]["content"], f"nosana/{NOSANA_MODEL}"

def _anthropic(system, user, timeout=60):
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=timeout,
        headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 400, "system": system,
              "messages": [{"role": "user", "content": user}]})
    r.raise_for_status()
    return r.json()["content"][0]["text"], "anthropic/haiku-4.5"

def ask(system, user):
    errs = []
    if NOSANA_URL:
        try: return _nosana(system, user)
        except Exception as e: errs.append(f"nosana:{e}")
    if ANTHROPIC_KEY:
        try: return _anthropic(system, user)
        except Exception as e: errs.append(f"anthropic:{e}")
    raise RuntimeError("no LLM available: " + "; ".join(errs))

def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}

# 1) intent: natural language -> watch spec
INTENT_SYS = """You convert a Korean/English request into a watch spec. Reply ONLY JSON:
{"type":"news"|"page"|"price","query":<news search keywords or URL or symbol>,"condition":<what makes an item worth alerting, in the user's language>,"interval_min":<int, default 10>,"op":<for price only: "<" or ">">,"threshold":<for price only: number>}
Rules: news = 뉴스/기사/소식 → query is 2-4 search keywords. page = a URL is given. price = coin/exchange rate; symbol like KRW-BTC, KRW-ETH, or USD. If unsure, type=news."""

def parse_intent(text):
    out, model = ask(INTENT_SYS, text)
    spec = _json(out)
    spec.setdefault("interval_min", 10)
    spec["_model"] = model
    return spec

# 2) judge: does this item satisfy the condition?
JUDGE_SYS = """You are a strict filter. Given a watch condition and an item (title/text), decide if the item satisfies the condition. Reply ONLY JSON: {"match":true|false,"reason":"<one short sentence in the user's language>"}"""

def judge(condition, item):
    user = f"조건: {condition}\n\n제목: {item['title']}\n내용: {item.get('text','')[:1500]}"
    out, model = ask(JUDGE_SYS, user)
    j = _json(out)
    return bool(j.get("match")), j.get("reason", out[:120]), model
