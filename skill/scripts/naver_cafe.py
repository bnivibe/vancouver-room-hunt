#!/usr/bin/env python3
"""Read Naver cafe room boards without a browser.

Browsers (the in-app pane and the Chrome extension) refuse cafe.naver.com, but
the cafe JSON API answers plain HTTP. Article lists need no login. Article
bodies need your own Naver session and membership of the cafe: export
NAVER_COOKIE="NID_AUT=...; NID_SES=..." (or point NAVER_COOKIE_FILE at a
chmod 600 dotenv file holding that line). Without it, `read` says so and exits 0.
Never commit the cookie; it is a login.

  python3 naver_cafe.py list [--cafe gocan|yoehang|all] [--pages 2] [--grep REGEX|none]
  python3 naver_cafe.py read gocan 999490

The default --grep keeps titles that name a Metro Vancouver place, written in
Korean the way posters write them (several spellings each).
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

CAFES = {  # url slug -> (clubid, room board menuid, board name)
    "gocan": (14223577, 219, "Canada Working Holiday cafe, housing board"),
    "yoehang": (20907486, 130, "HelloVan cafe, rent and sale board"),
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
# Korean spellings of Vancouver, Burnaby, Downtown, Metrotown, Coquitlam, New West, Zone 1/2,
# Joyce, Lougheed, Yaletown, Coal Harbour, Kitsilano, East Van, Richmond, North Van, Surrey,
# Langley, Brentwood, Patterson, Edmonds, King George, West End, Hornby, Burrard, Olympic Village,
# Science World. Kept as escapes so the source stays ASCII.
VANCOUVER_PLACES = (
    "\uBC34\uCFE0\uBC84|\uBCA4\uCFE0\uBC84|\uBC84\uB098\uBE44|\uB2E4\uC6B4\uD0C0\uC6B4|"
    "\uB2E8\uD0C4|\uBA54\uD2B8\uB85C\uD0C0\uC6B4|\uCF54\uD034\uD2C0\uB78C|\uCF54\uD034|"
    "\uB274\uC6E8|\uB274\uC6E8\uC2A4\uD2B8|1\uC874|2\uC874|\uC870\uC774\uC2A4|\uB85C\uD788\uB4DC|"
    "\uC608\uC77C\uD0C0\uC6B4|\uCF5C\uD558\uBC84|\uD0A4\uCE60\uB77C\uB178|"
    "\uC774\uC2A4\uD2B8\uBC34|\uC774\uC2A4\uD2B8\uBCA4|\uB9AC\uCE58\uBAAC\uB4DC|"
    "\uB178\uC2A4\uBC34|\uB180\uBC34|\uC368\uB9AC|\uB7AD\uB9AC|\uBE0C\uB80C\uD2B8\uC6B0\uB4DC|"
    "\uD328\uD130\uC2A8|\uC5D0\uB4DC\uBA3C\uC988|\uBC84\uD034\uD2C0\uB78C|\uD0B9\uC870\uC9C0|"
    "\uC6E8\uC2A4\uD2B8\uC5D4\uB4DC|\uD63C\uBE44|\uBC84\uB77C\uB4DC|\uC62C\uB9BC\uD53D|"
    "\uC0AC\uC774\uC5B8\uC2A4"
)
DEFAULT_GREP = VANCOUVER_PLACES


def cookie():
    value = os.environ.get("NAVER_COOKIE", "").strip()
    if value:
        return value
    path = os.environ.get("NAVER_COOKIE_FILE")
    if not path or not os.path.exists(os.path.expanduser(path)):
        return ""
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"\s*(?:export\s+)?NAVER_COOKIE\s*=\s*\"?([^\"\n]+)\"?", line)
        if m:
            return m.group(1).strip()
    return ""


def get(url, referer, ck=""):
    headers = {"User-Agent": UA, "Referer": referer}
    if ck:
        headers["Cookie"] = ck
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def list_board(slug, pages, grep):
    clubid, menuid, name = CAFES[slug]
    out = []
    for page in range(1, pages + 1):
        url = ("https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json"
               f"?search.clubid={clubid}&search.menuid={menuid}&search.queryType=lastArticle"
               f"&search.page={page}&search.perPage=50")
        data = json.loads(get(url, f"https://cafe.naver.com/{slug}"))
        for a in data["message"]["result"].get("articleList", []):
            subject = html.unescape(a.get("subject", ""))
            if grep and not re.search(grep, subject):
                continue
            ts = a.get("writeDateTimestamp")
            when = datetime.datetime.fromtimestamp(ts / 1000).strftime("%m-%d %H:%M") if ts else "?"
            out.append((when, slug, a["articleId"], subject, bool(a.get("openArticle"))))
    return name, out


def read(slug, article_id):
    ck = cookie()
    if not ck:
        print("Bodies need a login: set NAVER_COOKIE (NID_AUT and NID_SES) to read them.")
        return 0
    clubid = CAFES[slug][0]
    url = (f"https://apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/{clubid}/articles/{article_id}"
           "?query=&useCafeId=true&requestFrom=A")
    try:
        data = json.loads(get(url, "https://m.cafe.naver.com/", ck))
    except urllib.error.HTTPError as e:
        # 401 means not logged in; 403 with code 4005 means the account's cafe level is too low.
        print("HTTP", e.code)
        return 1
    result = data.get("result", {})
    if result.get("errorCode"):
        print("error:", result.get("errorCode"))
        return 1
    art = result.get("article", {})
    print("title:", art.get("subject"))
    print("posted:", art.get("writeDate"))
    body = art.get("contentHtml") or art.get("content") or ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<br\s*/?>|</p>|</div>", "\n", body)))
    print(re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", text)).strip()[:4000])
    photos = [u for u in re.findall(r'src="([^"]+)"', body) if "pstatic.net" in u or "postfiles" in u]
    if photos:
        print("photos:", len(photos))
        for p in photos[:8]:
            print(" ", p.split("?")[0])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--cafe", default="all", choices=["all", *CAFES])
    ls.add_argument("--pages", type=int, default=2)
    ls.add_argument("--grep", default=DEFAULT_GREP, help="title regex, or 'none' for every post")
    rd = sub.add_parser("read")
    rd.add_argument("cafe", choices=list(CAFES))
    rd.add_argument("article")
    a = ap.parse_args(argv)
    if a.cmd == "read":
        return read(a.cafe, a.article)
    for slug in (CAFES if a.cafe == "all" else [a.cafe]):
        name, rows = list_board(slug, a.pages, None if a.grep == "none" else a.grep)
        print(f"== {name} ({len(rows)} posts)")
        for when, s, aid, subject, public in rows:
            print(f"  {when} | {subject[:80]} | https://cafe.naver.com/{s}/{aid}" + (" | public" if public else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
