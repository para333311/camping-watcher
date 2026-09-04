import os, re, json, time, datetime, pathlib, urllib.parse, urllib.request
from playwright.sync_api import sync_playwright

D = pathlib.Path(__file__).parent
ENV = {}
for ln in (D / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in ln and not ln.strip().startswith("#"):
        k, v = ln.split("=", 1)
        ENV[k.strip()] = v.strip().strip('"')
TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
CHAT = ENV.get("TELEGRAM_CHAT_ID", "")
SEEN = D / "seen_local.json"
LOG = D / "local.log"
INTERVAL = 180

def log(s):
    t = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(t + " " + s + "\n")
    except Exception:
        pass
    print(t, s, flush=True)

def send(msg):
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": msg, "parse_mode": "HTML",
                                   "disable_web_page_preview": "true"}).encode()
    try:
        with urllib.request.urlopen("https://api.telegram.org/bot" + TOKEN + "/sendMessage",
                                    data=data, timeout=20) as r:
            return b'"ok":true' in r.read()
    except Exception as e:
        log("전송실패 " + str(e)[:80])
        return False

HOL = {"20260815","20260817","20260924","20260925","20260926",
       "20261003","20261005","20261009","20261225","20270101","20270301"}
def off(d):
    return d.weekday() >= 5 or d.strftime("%Y%m%d") in HOL

WD = "월화수목금토일"
def rng(d):
    n = d + datetime.timedelta(days=1)
    a = "%d/%d(%s)" % (d.month, d.day, WD[d.weekday()])
    b = ("%d(%s)" % (n.day, WD[n.weekday()])) if d.month == n.month else ("%d/%d(%s)" % (n.month, n.day, WD[n.weekday()]))
    return a + " ~ " + b

def months(k):
    t = datetime.date.today()
    y = t.year + (t.month - 1 + k) // 12
    m = (t.month - 1 + k) % 12 + 1
    return y, m

HN_CAL = "https://yeyak.hscity.go.kr/1098/3058/campCalendarList.do?campIdx=2&searchYear=%d&searchMonth=%02d"
HN_RSV = "https://yeyak.hscity.go.kr/1098/3058/campCalendarList.do?campIdx=2"
DD_CAL = "https://reserve.gmuc.co.kr/user/camp/campReservation.do?menu=d&menuFlag=C&schl_yyyymm=%d%02d"
DD_RSV = "https://reserve.gmuc.co.kr/user/camp/campReservation.do?menu=d&menuFlag=C"

SITES = [
    {"key": "HN", "name": "향남오토캠핑장", "km": 50, "cal": HN_CAL, "rsv": HN_RSV},
    {"key": "DD", "name": "도덕산캠핑장", "km": 13, "cal": DD_CAL, "rsv": DD_RSV},
]

def parse_hn(pg):
    res = {}
    for td in pg.query_selector_all("td"):
        try:
            t = (td.inner_text() or "").strip()
        except Exception:
            continue
        mm = re.match(r"(\d{1,2})\b", t)
        if not mm:
            continue
        det = [(n, int(c)) for c, n in re.findall(r"(\d+)\s*([AB]구역\([^)]*\))", t) if int(c) > 0]
        if det:
            res[int(mm.group(1))] = det
    return res

def parse_dd(pg):
    res = {}
    try:
        txt = pg.inner_text("body")
    except Exception:
        return res
    day = None
    for ln in txt.splitlines():
        s = ln.strip()
        if re.fullmatch(r"\d{1,2}", s):
            day = int(s)
            continue
        m = re.search(r"([AB])구역\s*잔여\s*데크\s*:\s*(\d+)", s)
        if m and day:
            c = int(m.group(2))
            if c > 0:
                res.setdefault(day, []).append((m.group(1) + "구역", c))
    return res

def scan(pg, site):
    out = {}
    today = datetime.date.today()
    for k in range(3):
        y, m = months(k)
        try:
            pg.goto(site["cal"] % (y, m), timeout=45000)
            pg.wait_for_timeout(1500)
        except Exception as e:
            log(site["name"] + " 조회실패 %d-%02d %s" % (y, m, str(e)[:60]))
            continue
        got = parse_hn(pg) if site["key"] == "HN" else parse_dd(pg)
        for d, det in got.items():
            try:
                dt = datetime.date(y, m, d)
            except ValueError:
                continue
            if dt < today or not (off(dt) and off(dt + datetime.timedelta(days=1))):
                continue
            out["%s|%04d%02d%02d" % (site["key"], y, m, d)] = det
    return out

def main():
    seen = {}
    if SEEN.exists():
        try:
            seen = json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception:
            seen = {}
    send("근처 캠핑장 감시 시작\n향남오토캠핑장 · 도덕산캠핑장 / 3분 간격")
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        ctx = br.new_context(ignore_https_errors=True,
                             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        pg = ctx.new_page()
        while True:
            try:
                cur = {}
                for st in SITES:
                    cur.update(scan(pg, st))
                new = []
                for k in sorted(cur):
                    sig = ",".join("%s%d" % (n, c) for n, c in cur[k])
                    if seen.get(k) != sig:
                        seen[k] = sig
                        new.append(k)
                for k in list(seen):
                    if k not in cur:
                        del seen[k]
                SEEN.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
                for k in new:
                    sk, ds = k.split("|")
                    st = [x for x in SITES if x["key"] == sk][0]
                    dt = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:]))
                    det = " / ".join("%s %d" % (n, c) for n, c in cur[k])
                    nav = "https://map.naver.com/p/search/" + urllib.parse.quote(st["name"])
                    send("⛺ 데크 빈자리 발견\n" + rng(dt) + "\n" + st["name"] + "\n" + det +
                         "\n🟢\n\n" % st["km"] +
                         '<a href="' + nav + '">📍 네이버지도</a> <a href="' + st["rsv"] + '">🌲 예약하기</a>')
                log("확인 %d일치 / 신규 %d건" % (len(cur), len(new)))
            except Exception as e:
                log("루프오류 " + str(e)[:120])
            time.sleep(INTERVAL)

main()