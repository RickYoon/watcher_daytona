"""Sponsor check 3/3 — DNSimple: create a CNAME record via API (sandbox by default)."""
import os, sys, requests
from dotenv import load_dotenv
load_dotenv()
BASE = "https://api.sandbox.dnsimple.com/v2" if os.environ.get("DNSIMPLE_SANDBOX", "1") == "1" else "https://api.dnsimple.com/v2"
H = {"Authorization": f"Bearer {os.environ['DNSIMPLE_TOKEN']}", "Content-Type": "application/json"}
acct = os.environ.get("DNSIMPLE_ACCOUNT_ID") or requests.get(f"{BASE}/whoami", headers=H).json()["data"]["account"]["id"]
domain = os.environ["DNSIMPLE_DOMAIN"]
name, target = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("hello", "example.com")
r = requests.post(f"{BASE}/{acct}/zones/{domain}/records", headers=H,
                  json={"name": name, "type": "CNAME", "content": target, "ttl": 300})
print(r.status_code, r.json())
