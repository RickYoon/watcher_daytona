# WatchBox — 말로 만드는 감시봇 공장

> Telegram에 `/watch 삼성전자 HBM 관련 부정적 뉴스 뜨면 알려줘` 라고 치면,
> 그 조건 전용 감시 봇이 **Daytona 샌드박스 하나**로 태어나 24시간 돌고,
> 조건은 **Nosana GPU 위 LLM**이 의미로 판정해, 맞으면 Telegram으로 알려준다.

Built at Daytona HackSprint Seoul, 2026-09-19 (2 hours).

## Why
- 밖에서 "○○ 되면 알려줘"를 시키려면 집 컴퓨터를 켜두고 감시마다 스크립트를 짜야 했다
- IFTTT/Google Alerts는 키워드만 본다 — "악재인가?"는 못 판정한다
- 감시 1개 = 격리된 컴퓨터 1개. 말 한 줄로 태어나고, 상태를 갖고 상주하고, `/stop`이면 사라진다

## Architecture
```
Telegram ──/watch──▶ bot/main.py ──▶ watchers/brain.py (Nosana LLM: intent → spec JSON)
                        │
                        └──▶ bot/factory.py ──▶ Daytona sandbox #N  (one per watch)
                                                  └── watchers/run.py loop:
                                                        fetch (news RSS / page diff / price)
                                                        → brain.judge (Nosana LLM: does it match?)
                                                        → Telegram sendMessage
bot itself also lives in a Daytona sandbox (deploy_bot.py) — laptop can be closed.
```

## Sponsor integration (code-level)
| Sponsor | Where | What |
|---|---|---|
| **Daytona** | `bot/factory.py` `spawn()` `logs()` `stop()` `test()` | `daytona.create(CreateSandboxFromImageParams)`, `fs.upload_file`, `process.exec`, labels per user/watch, `delete` |
| **Daytona** | `deploy_bot.py` | bot process itself hosted in a sandbox |
| **Nosana** | `watchers/brain.py` `_nosana()` | Ollama OpenAI-compatible `/v1/chat/completions` on a Nosana GPU deployment (Qwen 3.6) — used for intent parsing and semantic judging |
| DNSimple | `dns.py` | (optional) CNAME for a status page |

## Commands
`/watch <natural language>` · `/list` · `/test <id>` (judge latest 5 items now) · `/logs <id>` · `/stop <id>`

## Run
```
cp .env.example .env   # DAYTONA_API_KEY, TG_BOT_TOKEN, NOSANA_LLM_URL, NOSANA_MODEL
pip install -r requirements.txt
python bot/main.py          # local
python deploy_bot.py        # or: move the bot into Daytona
```

## What ran today (measured, 2026-09-19)
- Daytona sandbox cold create: **1.06–1.86 s**; upload + pip + loop start: **5.6 s** (`bot/factory.py spawn()`)
- Nosana Qwen 3.6 35B-A3B on RTX 6000 Ada: intent parse **4.5 s**, judge **3.6–4.3 s** per item, `think:false`
- Live judge on 6 real headlines: 2 matched with correct reasons (patent suit ✅, "de-spec is actually favorable" ❌)
- **Blocker hit:** this Daytona org is Tier 1 → sandbox egress is allow-listed (PyPI/GitHub/OpenAI ok; Telegram, Google News, Nosana blocked) and `domain_allow_list` is rejected at this tier. The watcher loop therefore starts inside the sandbox but cannot fetch. The identical loop was run on the laptop for the live alert; on a Tier 3 org no code change is needed. Tier bump requested from Daytona staff on site.

## Honest limits
- Watch templates are 3 (news / page / price). Sites needing login (KTX seats, Naver real-estate) work via the `page` template only if the user supplies cookies — not implemented today.
- Cost: 1 vCPU + 1 GiB sandbox ≈ $1.6/day per watch at list price. Next step: auto-stop between checks and wake on schedule.
- LLM: Nosana primary, Anthropic fallback if `ANTHROPIC_API_KEY` set.
