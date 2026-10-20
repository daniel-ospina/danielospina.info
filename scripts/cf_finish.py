#!/usr/bin/env python3
"""Put danielospina.info in front of the Cloudflare Pages project.

Run it in the order the domain actually has to move:

    python3 scripts/cf_finish.py --status     # what is true right now (read-only)
    python3 scripts/cf_finish.py --apply      # create zone, clear conflicts, attach domains

Needs an API token in ~/.cf-token with:

    Zone        Zone    Edit     (resource: All zones from an account)
    Zone        DNS     Edit
    Account     Cloudflare Pages  Edit

`--apply` is idempotent: re-running it converges rather than duplicating. It
never deletes a DNS record that is not on the list it can explain (an A/AAAA/
CNAME at the apex or at www that does not already point at this Pages project),
and it never touches MX or TXT, so mail configuration survives the cutover.

The one thing it cannot do is change the registrar's nameservers. It prints the
nameservers to set at GoDaddy and, until they are set, reports the zone as
pending.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

DOMAIN = "danielospina.info"
WWW = f"www.{DOMAIN}"
PROJECT = "danielspina-info"
PAGES_TARGET = f"{PROJECT}.pages.dev"
TOKEN_FILE = pathlib.Path.home() / ".cf-token"
API = "https://api.cloudflare.com/client/v4"


def load_token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit(f"no token at {TOKEN_FILE} — see the docstring for the permissions it needs")
    token = TOKEN_FILE.read_text().strip()
    if not token:
        sys.exit(f"{TOKEN_FILE} is empty")
    return token


class APIError(RuntimeError):
    pass


def call(method: str, path: str, token: str, body: dict | None = None):
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        payload = json.loads(exc.read() or b"{}")
        errors = payload.get("errors") or [{"message": str(exc)}]
        raise APIError(f"{method} {path} -> " + "; ".join(
            f"[{e.get('code')}] {e.get('message')}" for e in errors)) from None
    if not payload.get("success", False):
        errors = payload.get("errors") or [{"message": "unknown"}]
        raise APIError(f"{method} {path} -> " + "; ".join(
            f"[{e.get('code')}] {e.get('message')}" for e in errors))
    return payload.get("result")


def account_id(token: str) -> str:
    accounts = call("GET", "/accounts?per_page=50", token)
    if not accounts:
        sys.exit("this token cannot see any account")
    if len(accounts) > 1:
        print("multiple accounts visible; using the first — verify this is the right one:")
        for a in accounts:
            print(f"  {a['id']}  {a['name']}")
    return accounts[0]["id"]


def find_zone(token: str):
    zones = call("GET", f"/zones?name={DOMAIN}", token)
    return zones[0] if zones else None


def registry_nameservers() -> list[str]:
    try:
        out = subprocess.run(["dig", "+short", "NS", DOMAIN], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted(n.strip().rstrip(".") for n in out.split() if n.strip())


def status(token: str) -> int:
    zone = find_zone(token)
    if not zone:
        print(f"zone      : absent — {DOMAIN} is not in this Cloudflare account yet")
        print(f"registrar : {', '.join(registry_nameservers()) or 'unknown'}")
        print("next      : run --apply to create the zone, then set its nameservers at GoDaddy")
        return 0

    print(f"zone      : {zone['name']}  id={zone['id']}  status={zone['status']}")
    print(f"cloudflare: {', '.join(zone.get('name_servers') or [])}")
    print(f"registrar : {', '.join(registry_nameservers()) or 'unknown'}")
    live = {n.rstrip(".") for n in registry_nameservers()}
    assigned = set(zone.get("name_servers") or [])
    if live and assigned:
        verdict = "MATCHES — the zone is in the registrar's hands" if live == assigned else "DOES NOT MATCH — still pending at the registrar"
        print(f"delegation: {verdict}")

    acc = zone["account"]["id"]
    try:
        domains = call("GET", f"/accounts/{acc}/pages/projects/{PROJECT}/domains", token)
    except APIError as exc:
        print(f"pages     : {exc}")
        domains = []
    if domains:
        for d in domains:
            print(f"pages dom : {d.get('name')}  status={d.get('status')}  verification={d.get('verification_data', {}).get('status')}")
    else:
        print(f"pages dom : none attached to {PROJECT}")
    return 0


def apply(token: str) -> int:
    acc = account_id(token)

    zone = find_zone(token)
    if not zone:
        print(f"creating zone {DOMAIN} (jump_start disabled: import nothing, start clean)")
        zone = call("POST", "/zones", token, {
            "name": DOMAIN,
            "account": {"id": acc},
            "type": "full",
            "jump_start": False,
        })
        print(f"  created id={zone['id']}  status={zone['status']}")
        print(f"  nameservers to set at GoDaddy: {', '.join(zone.get('name_servers') or [])}")
    else:
        print(f"zone already present id={zone['id']} status={zone['status']} — reusing")

    zone_id = zone["id"]

    # Conflicting records: the apex and www can only resolve one way. Anything
    # there that is not already this Pages project blocks the custom domain.
    records = call("GET", f"/zones/{zone_id}/dns_records?per_page=200", token) or []
    blocked = 0
    for r in records:
        if r["type"] not in ("A", "AAAA", "CNAME"):
            continue  # never touch MX / TXT / NS — mail and verification live there
        if r["name"] not in (DOMAIN, WWW):
            continue
        if r["type"] == "CNAME" and r.get("content", "").rstrip(".") == PAGES_TARGET:
            print(f"  keep  {r['type']:5} {r['name']} -> {r['content']}")
            continue
        print(f"  delete {r['type']:5} {r['name']} -> {r['content']}  (conflicts with Pages)")
        call("DELETE", f"/zones/{zone_id}/dns_records/{r['id']}", token)
        blocked += 1
    if not blocked and not records:
        print("  no DNS records yet — Pages will create them when the domains attach")

    for name in (DOMAIN, WWW):
        try:
            d = call("POST", f"/accounts/{acc}/pages/projects/{PROJECT}/domains", token, {"name": name})
            print(f"  attach {name} -> status={d.get('status')}")
        except APIError as exc:
            print(f"  attach {name} -> {exc}")

    print()
    print(status(token))
    print()
    print("remaining manual step: at GoDaddy, point the nameservers at the pair above.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="report current state, change nothing")
    ap.add_argument("--apply", action="store_true", help="create the zone, clear conflicts, attach the domains")
    args = ap.parse_args()
    if not (args.status or args.apply):
        ap.error("choose --status or --apply")
    token = load_token()
    try:
        return status(token) if args.status and not args.apply else apply(token)
    except APIError as exc:
        sys.exit(f"cloudflare said: {exc}")


if __name__ == "__main__":
    sys.exit(main())
