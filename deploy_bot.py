"""Move the bot itself into a Daytona sandbox so the laptop can be closed.
Usage: python deploy_bot.py        -> prints sandbox id; bot runs there with nohup
       python deploy_bot.py logs   -> tail bot log inside the sandbox
       python deploy_bot.py stop   -> delete the bot sandbox
"""
import json, os, sys
from dotenv import load_dotenv
load_dotenv()
from daytona import Daytona, DaytonaConfig, CreateSandboxFromImageParams, Resources

STATE = ".bot_sandbox"
d = Daytona(DaytonaConfig(api_key=os.environ["DAYTONA_API_KEY"]))
ENV_KEYS = ("DAYTONA_API_KEY", "TG_BOT_TOKEN", "NOSANA_LLM_URL", "NOSANA_MODEL", "ANTHROPIC_API_KEY")

if len(sys.argv) > 1 and sys.argv[1] in ("logs", "stop"):
    sb = d.get(open(STATE).read().strip())
    if sys.argv[1] == "logs":
        print(sb.process.exec("tail -n 40 /home/daytona/watchbox/bot.log", timeout=20).result)
    else:
        d.delete(sb); os.remove(STATE); print("bot sandbox deleted")
    sys.exit()

sb = d.create(CreateSandboxFromImageParams(
    image="python:3.12-slim", labels={"app": "watchbox", "role": "bot"},
    env_vars={k: os.environ.get(k, "") for k in ENV_KEYS},
    resources=Resources(cpu=1, memory=1, disk=2), auto_stop_interval=0))
R = "/home/daytona/watchbox"
for sub in ("bot", "watchers"):
    sb.fs.create_folder(f"{R}/{sub}", "755")
    for f in os.listdir(sub):
        if f.endswith(".py"):
            sb.fs.upload_file(open(f"{sub}/{f}", "rb").read(), f"{R}/{sub}/{f}")
sb.fs.upload_file(b"", f"{R}/.env")  # env comes from sandbox env_vars
r = sb.process.exec("pip install -q python-telegram-bot python-dotenv requests feedparser certifi daytona", timeout=300)
assert r.exit_code == 0, r.result[-500:]
sb.process.exec(f"cd {R} && nohup python bot/main.py > bot.log 2>&1 &")
open(STATE, "w").write(sb.id)
print("bot sandbox", sb.id)
print(sb.process.exec(f"sleep 5; tail -n 5 {R}/bot.log", timeout=30).result)
