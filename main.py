#!/usr/bin/python3
import sys
import requests
from decouple import config
import base64
import dns
import dns.resolver




def update(hosts, username, password):
    ip = get_ip()
    for host in hosts:
        if get_current(host) == ip:
            print(f"[OK] {host} already up to date")
            ping_healthchecks()
            continue
        res = requests.get(f"https://www.ovh.com/nic/update?system=dyndns&hostname={host}&myip={ip}", headers={"Authorization": auth_header(username, password)})
        if res.status_code == 200:
            ping_healthchecks()

def get_ip():
    return requests.get('https://api.ipify.org').text

def auth_header(username, password):
    raw = f"{username}:{password}"
    bytes = raw.encode('ascii')
    return "Basic " + base64.b64encode(bytes).decode('ascii')

def get_current(host):   
    result = dns.resolver.resolve(host, 'A')
    #print("CURR")
    return result[0].to_text()

def ping_healthchecks():
    url = "YOUR_URL"
    requests.post(url)


if __name__ == '__main__':
    hosts = sys.argv[1:]
    username = config("OVH-USERNAME")
    password = config("OVH-PASSWORD")
    update(hosts, username, password)
