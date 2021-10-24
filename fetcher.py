import requests
import re


request_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
}
hashReg = re.compile(r"[a-fA-F0-9]{40}")
entitiesReg = re.compile(r"<a href=\"([^\"]+)\" rel=\"bookmark\">")
urlReg = re.compile(r"当前域名是：<a[^>]+href=\"(https?://[\w/\.]+)#?\"[^>]*>")
collReg = re.compile(
    r"<h1 class=\"entry-title\">[^<]*\d+\s*年\s*\d+\s*月[^<]*合集[^<]*</h1>")


def fetch_hashes(url, coll_only=False):
    r = requests.get(url, headers=request_headers)
    r.raise_for_status()
    if coll_only:
        is_coll = re.search(collReg, r.text)
        if not is_coll:
            return []
    m = re.findall(hashReg, r.text)
    return m


def fetch_eneities_on_page(url):
    r = requests.get(url, headers=request_headers)
    if r.status_code == requests.codes.not_found:
        return None
    r.raise_for_status()
    m = re.findall(entitiesReg, r.text)
    return m


def fetch_new_url(url):
    r = requests.get(url, headers=request_headers)
    r.raise_for_status()
    m = re.search(urlReg, r.text)
    if not m:
        return None
    u = m.group(1)
    if not u.endswith("/"):
        r = u + "/"
    return u
