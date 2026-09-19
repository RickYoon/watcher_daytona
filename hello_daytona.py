"""Sponsor check 1/3 — Daytona: spin up a sandbox, run code, tear down."""
import os, time
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()
t0 = time.time()
d = Daytona(DaytonaConfig(api_key=os.environ["DAYTONA_API_KEY"]))
sb = d.create()
print(f"sandbox {sb.id} up in {time.time()-t0:.2f}s")
r = sb.process.code_run('import platform; print("hello from", platform.node())')
print(r.exit_code, r.result)
sb.delete()
print("deleted")
