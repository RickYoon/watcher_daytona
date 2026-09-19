"""Daytona factory: one watch = one sandbox. Uploads watchers/, writes params.json, starts the loop."""
import json, os, time
from daytona import Daytona, DaytonaConfig, CreateSandboxFromImageParams, Resources, SessionExecuteRequest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.path.join(ROOT, "watchers")
REMOTE = "/home/daytona/watch"
_d = None

def client():
    global _d
    if _d is None:
        _d = Daytona(DaytonaConfig(api_key=os.environ["DAYTONA_API_KEY"]))
    return _d

def spawn(spec: dict) -> dict:
    """spec must contain id, type, query, condition, interval_min, chat_id, tg_token (+op/threshold)."""
    t0 = time.time()
    sb = client().create(CreateSandboxFromImageParams(
        image="python:3.12-slim",
        labels={"app": "watchbox", "watch_id": str(spec["id"]), "user": str(spec["chat_id"])},
        env_vars={k: os.environ.get(k, "") for k in ("NOSANA_LLM_URL", "NOSANA_MODEL", "ANTHROPIC_API_KEY")},
        resources=Resources(cpu=1, memory=1, disk=1),
        auto_stop_interval=0,  # watchers live until /stop
    ))
    t_create = time.time() - t0
    sb.fs.create_folder(REMOTE, "755")
    for f in ("sources.py", "brain.py", "run.py"):
        sb.fs.upload_file(open(os.path.join(WDIR, f), "rb").read(), f"{REMOTE}/{f}")
    sb.fs.upload_file(json.dumps(spec, ensure_ascii=False).encode(), f"{REMOTE}/params.json")
    r = sb.process.exec("pip install -q requests feedparser certifi", timeout=180)
    if r.exit_code != 0:
        raise RuntimeError(f"pip failed: {r.result[-300:]}")
    # detached: a session command with run_async returns immediately, the loop keeps running
    sb.process.create_session("watch")
    sb.process.execute_session_command("watch", SessionExecuteRequest(
        command=f"cd {REMOTE} && python run.py > out.log 2>&1", run_async=True))
    return {"sandbox_id": sb.id, "create_s": round(t_create, 2), "total_s": round(time.time() - t0, 1)}

def logs(sandbox_id: str, n=15) -> str:
    sb = client().get(sandbox_id)
    r = sb.process.exec(f"tail -n {n} {REMOTE}/watch.log {REMOTE}/out.log 2>/dev/null", timeout=20)
    return r.result or "(no logs yet)"

def stop(sandbox_id: str):
    client().delete(client().get(sandbox_id))

def test(sandbox_id: str) -> str:
    """Run one immediate check inside the sandbox against the latest items (first_run=False)."""
    sb = client().get(sandbox_id)
    code = ("import json,run,sources,brain\n"
            "items=run.fetch()[:5]\n"
            "out=[]\n"
            "for it in items:\n"
            "    if run.P['type']=='price': out.append(f\"{it['title']} = {it['value']:,.0f}\"); continue\n"
            "    m,r,model=brain.judge(run.P['condition'],it); out.append(('✅ ' if m else '❌ ')+it['title'][:60]+'\\n   — '+r)\n"
            "print('\\n'.join(out))")
    r = sb.process.exec(f"cd {REMOTE} && python -c {json.dumps(code)}", timeout=180)
    return r.result[-1500:] if r.result else f"exit {r.exit_code}"
