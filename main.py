#!/usr/bin/env python3
"""Aggiorna record DynHost OVH con l'IP pubblico corrente.

Uso: python main.py host1.esempio.ch [host2.esempio.ch ...]

Variabili richieste nel .env (o nell'ambiente):
    OVH-USERNAME, OVH-PASSWORD
Opzionale:
    HEALTHCHECK-URL   es. https://hc-ping.com/<uuid>

Dipendenze: pip install requests dnspython python-decouple
"""
import sys

import dns.exception
import dns.resolver
import requests
from decouple import config

TIMEOUT = 10  # secondi


def get_ip():
    r = requests.get("https://api.ipify.org", timeout=TIMEOUT)
    r.raise_for_status()
    return r.text.strip()


def get_current(host):
    """Legge il record A direttamente dal nameserver autoritativo (niente cache).

    Restituisce None se il record non esiste o la query fallisce:
    in quel caso si procede comunque con l'aggiornamento.
    """
    try:
        zone = dns.resolver.zone_for_name(host)
        ns_name = dns.resolver.resolve(zone, "NS")[0].target
        ns_ip = dns.resolver.resolve(ns_name, "A")[0].to_text()

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [ns_ip]
        resolver.lifetime = TIMEOUT
        return resolver.resolve(host, "A")[0].to_text()
    except dns.exception.DNSException:
        return None


def update_host(host, ip, username, password):
    current = get_current(host)
    if current == ip:
        print(f"[OK] {host} già aggiornato ({ip})")
        return True

    r = requests.get(
        "https://www.ovh.com/nic/update",
        params={"system": "dyndns", "hostname": host, "myip": ip},
        auth=(username, password),
        timeout=TIMEOUT,
    )
    body = r.text.strip()

    # Il protocollo DynDNS indica l'esito nel corpo, non solo nello status HTTP
    if r.ok and body.startswith(("good", "nochg")):
        print(f"[UPDATED] {host}: {current} -> {ip} ({body})")
        return True

    print(f"[ERRORE] {host}: HTTP {r.status_code} - {body}", file=sys.stderr)
    return False


def ping_healthchecks(url, success):
    if not url:
        return
    try:
        requests.post(url if success else f"{url}/fail", timeout=TIMEOUT)
    except requests.RequestException as e:
        print(f"[WARN] ping Healthchecks fallito: {e}", file=sys.stderr)


def main():
    hosts = sys.argv[1:]
    if not hosts:
        print("Uso: python main.py host1 [host2 ...]", file=sys.stderr)
        return 2

    username = config("OVH-USERNAME")
    password = config("OVH-PASSWORD")
    hc_url = config("HEALTHCHECK-URL", default="")

    try:
        ip = get_ip()
        # lista (non generatore) così tutti gli host vengono processati
        results = [update_host(h, ip, username, password) for h in hosts]
        success = all(results)
    except requests.RequestException as e:
        print(f"[ERRORE] rete: {e}", file=sys.stderr)
        success = False

    ping_healthchecks(hc_url, success)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
