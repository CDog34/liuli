import shutil
import re
import sys
import os
import time
import urllib.parse
import json
from fetcher import fetch_hashes, fetch_eneities_on_page, fetch_new_url
from transmission_rpc import Client

magnet_link = "magnet:?xt=urn:btih:{hash}"
idRegexp = re.compile(r"^https?://.*/(\d+)\.html$")
confPath = os.path.join(os.path.split(
    os.path.realpath(__file__))[0], "config.json")


def processPage(url, stopId, c, conf):
    max = 0
    min = 0
    entities = withRetry(lambda: fetch_eneities_on_page(
        url), 10)
    if entities is None:
        print("Got no entities, probably reach the end.")
        return max, min, True
    print("Got entities: ", entities)
    for entity in entities:
        m = re.match(idRegexp, entity)
        if not m:
            continue
        id = int(m.group(1))
        if max == 0 or id > max:
            max = id
        if min == 0 or id < min:
            min = id
        if id <= stopId:
            print("skip: {id} / {entity}".format(id=id, entity=entity))
            continue
        print("processing: {id} / {entity}".format(id=id, entity=entity))
        hs = withRetry(lambda: fetch_hashes(entity, True), 10)
        for hash_item in hs:
            magnet = magnet_link.format(hash=hash_item)
            print("got hashes: {hashes}".format(hashes=magnet))
            t = c.add_torrent(
                magnet, download_dir=conf["transmissionDir"])
            c.change_torrent(t.id, seedIdleLimit=10, seedRatioLimit=0,
                             seedIdleMode=1, seedRatioMode=1)
            print("Added: {torrent}".format(torrent=t.id))
    return max, min, False


def withRetry(cbk, tryLimit):
    tried = 0
    err = None
    while tried < tryLimit:
        try:
            return cbk()
        except Exception as e:
            err = e
            print("Error Occor retrying {tried}/{tryLimit}. Detail:".format(
                tried=tried+1, tryLimit=tryLimit), e)
            tried = tried + 1
    raise err


def getconfig():
    f = open(confPath, mode="r")
    config = json.load(f)
    f.close()
    return config


def setconfig(conf):
    f = open(confPath, mode="w")
    config = json.dump(conf, f)
    f.close()


def main():
    print("Task started at:", time.asctime(time.localtime(time.time())))
    conf = getconfig()
    if conf["processing"]:
        print("Task is in processing.")
        return
    conf["processing"] = True
    setconfig(conf)
    try:
        print("Updating site url with old value: ", conf["siteUrl"])
        u = fetch_new_url(conf["siteUrl"])
        if not u:
            print("Empty site url.")
        else:
            print("New site url: ", u)
            conf["siteUrl"] = u
        print("Creating Transmission Client.")
        c = Client(host=conf["transmissionHost"], port=conf["transmissionPort"],
                   username=conf["transmissionUsername"], password=conf["transmissionPass"])
        curPage, stopId, max, min = 1, conf["lastId"], 0, sys.maxsize
        print("Current last id is: ", stopId)
        while (min > stopId):
            bmax, bmin, isEnd = processPage(urllib.parse.urljoin(
                conf["siteUrl"], "anime.html/page/{page}".format(page=curPage)), stopId, c, conf)
            if isEnd:
                break
            if bmax > max:
                max = bmax
            if bmin < min:
                min = bmin
            curPage = curPage + 1
        conf["lastId"] = max
        print("Next last id is:", max)
    except Exception as e:
        print("Error: ", e)
    conf["processing"] = False
    setconfig(conf)
    print("Done.")


if __name__ == "__main__":
    main()
