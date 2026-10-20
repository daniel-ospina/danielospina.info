#!/usr/bin/env python3
"""Cloudflare setup for danielospina.info — step 1: account, zone, nameservers.

Reads the API token from ~/.cf-token (never prints it). Idempotent: if the zone
already exists it just reports the nameservers.
"""
import json, os, sys, urllib.request, urllib.error

TOKEN_FILE = os.path.expanduser("~/.cf-token")
DOMAIN = "danielospina.info"
API = "https://api.cloudflare.com/client/v4"

def token():
    t = open(TOKEN_FILE).read().strip()
    if not t:
        sys.exit("~/.cf-token is empty — create the API token first.")
    return t

def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": "Bearer " + token(),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def main():
    acc = call("GET", "/accounts?per_page=50")
    if not acc.get("success"):
        sys.exit("token cannot list accounts: %s" % json.dumps(acc.get("errors"))[:300])
    accounts = acc["result"]
    for a in accounts:
        print("account:", a["name"], a["id"])

    # reuse the zone if it is already there
    z = call("GET", "/zones?name=" + DOMAIN)
    if z.get("success") and z["result"]:
        zone = z["result"][0]
        print("\nZONE ALREADY EXISTS in account", zone["account"]["id"])
    else:
        account = accounts[0]
        if len(accounts) > 1:
            print("\n(using the first account; edit the script if that is wrong)")
        created = call("POST", "/zones", {
            "name": DOMAIN, "account": {"id": account["id"]},
            "type": "full", "jump_start": False})
        if not created.get("success"):
            sys.exit("zone create failed: %s" % json.dumps(created.get("errors"))[:400])
        zone = created["result"]
        print("\nZONE CREATED:", zone["name"])

    ns = zone.get("name_servers") or []
    print("\n" + "=" * 58)
    print("  NAMESERVERS TO SET AT GODADDY")
    for s in ns:
        print("   ", s)
    print("=" * 58)
    json.dump({"id": zone["id"], "account": zone["account"]["id"],
               "nameservers": ns, "status": zone.get("status")},
              open("/tmp/cf-zone.json", "w"), indent=1)
    print("\nstatus:", zone.get("status"), " id:", zone["id"])
    print("saved to /tmp/cf-zone.json")

    # what is currently in the zone (Squarespace leftovers)
    dns = call("GET", f"/zones/{zone['id']}/dns_records?per_page=100")
    if dns.get("success"):
        print("\nDNS records Cloudflare imported (", len(dns["result"]), "):")
        for r in dns["result"]:
            print(f"  {r['type']:6} {r['name']:32} -> {str(r['content'])[:45]}  proxied={r.get('proxied')}")
        json.dump(dns["result"], open("/tmp/cf-dns.json", "w"), indent=1)

if __name__ == "__main__":
    main()
