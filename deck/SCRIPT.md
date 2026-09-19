# WatchBox — 3-minute stage script

**[Slide 1 — 0:00]**
Hi, I'm Rick. Solo build. This is WatchBox: you tell Telegram what to watch, and it spawns a dedicated Daytona sandbox that watches 24/7. An LLM on Nosana GPUs decides whether what it found actually matters.

**[Slide 2 — 0:20]**
Today, "tell me when X happens" is still a coding task. Three things break. Your laptop has to stay on. Google Alerts and IFTTT only match keywords — they can't tell you whether news is *bad* news. And watchers die silently — my own conference crawler was dead for 18 days before I noticed.

**[Slide 3 — 0:50]**
Here's the flow. One sentence in Telegram. Nosana's LLM turns it into a spec: type, query, condition, interval. Then the Daytona SDK creates a sandbox, uploads the watcher, starts the loop. One watch, one isolated computer. It fetches — news RSS, page diff, price API — sends every new item back to Nosana with the question "does this match?", and pings you on Telegram with the reason. `/stop` deletes the box. The bot itself is designed to live in a sandbox too, so the laptop can close.

**[Slide 4 — 1:30]**
This ran today at 15:28. First watch in Korean: "alert me on negative Nvidia news." Sandbox born in 1.2 seconds, ready in 7.6. Second watch, a BTC price trigger — 0.67 seconds. `/list` shows two boxes and their cost. And the alert at the bottom is a real headline: "Huawei overtakes Nvidia in China." Qwen 3.6 on Nosana judged it as competitive loss, therefore negative. It rejected five other headlines correctly, including one that *sounded* negative but was actually favorable.

**[Slide 5 — 2:10]**
Why these sponsors, not a VPS? Daytona is a computer per watch — born from one sentence, stateful while alive, gone on stop; a hundred watches never touch each other. Nosana makes meaning cheap enough to run around the clock — without it this is Google Alerts. DNSimple I did not integrate — I'm saying that plainly rather than pretending.

**[Slide 6 — 2:35]**
What's honestly missing. Login sites like KTX seats need cookies — next is Daytona Secrets so even the bot never sees them. Cost: an always-on box is $1.60 a day; auto-stop between checks brings it down ~50×. And one blocker I hit: this org is Daytona Tier 1, so sandbox egress is allow-listed — the loop starts inside the box but can't reach Telegram or Google. The identical code ran on my laptop for the live alert; on Tier 3 nothing changes. First user is me: conference deadlines, price triggers, pool schedules.

Repo: github.com/RickYoon/watcher_daytona. Bot: @Daytonakorea_bot. Thank you.
