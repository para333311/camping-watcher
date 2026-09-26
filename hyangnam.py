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
SEEN = D / "seen_hyangnam.json"
LOG = D / "hyangnam.log"
INTERVAL = 360   # 2026-09-26 파라님 「반으로 줄여 텔 덜 오도록」

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
        log("전송실패 " + str(e))
        return False

HOL = {"20260815","20260817","20260924","20260925","20260926","20260927",
       "20261003","20261005","20261009","20261225"}
def off(d):
    return d.weekday() >= 5 or d.strftime("%Y%m%d") in HOL

WD = "월화수목금토일"
def rng(d):
    n = d + datetime.timedelta(days=1)
    a = "%d/%d(%s)" % (d.month, d.day, WD[d.weekday()])
    if d.month == n.month:
        b = "%d(%s)" % (n.day, WD[n.weekday()])
    else:
        b = "%d/%d(%s)" % (n.month, n.day, WD[n.weekday()])
    return a + " ~ " + b

CAL = "https://yeyak.hscity.go.kr/1098/3058/campCalendarList.do?campIdx=2&searchYear=%d&searchMonth=%02d"
RSV = "https://yeyak.hscity.go.kr/1098/3058/campCalendarList.do?campIdx=2"
NAV = "https://map.naver.com/p/search/" + urllib.parse.quote("향남오토캠핑장")

def scan(pg):
    out = {}
    today = datetime.date.today()
    for k in range(3):
        y = today.year + (today.month - 1 + k) // 12
        m = (today.month - 1 + k) % 12 + 1
        try:
            pg.goto(CAL % (y, m), timeout=40000)
            pg.wait_for_timeout(1200)
        except Exception as e:
            log("조회실패 %d-%02d %s" % (y, m, str(e)[:80]))
            continue
        for td in pg.query_selector_all("td"):
            try:
                t = (td.inner_text() or "").strip()
            except Exception:
                continue
            mm = re.match(r"(\d{1,2})\b", t)
            if not mm:
                continue
            d = int(mm.group(1))
            if not 1 <= d <= 31:
                continue
            det = [(int(c), n) for c, n in re.findall(r"(\d+)\s*([AB]구역\([^)]*\))", t) if int(c) > 0]
            if not det:
                continue
            try:
                dt = datetime.date(y, m, d)
            except ValueError:
                continue
            if dt < today or not (off(dt) and off(dt + datetime.timedelta(days=1))):
                continue
            out["%04d%02d%02d" % (y, m, d)] = det
    return out

def probe_bma(pg):
    u = "https://www.auc.or.kr/bmacamp/contents/view?contentsNo=316&menuLevel=2&menuNo=133"
    found = []
    try:
        pg.goto(u, timeout=45000)
        pg.wait_for_timeout(3000)
        for f in pg.frames:
            if f.url and f.url != u:
                found.append("[frame] " + f.url)
        for a in pg.query_selector_all("a"):
            h = a.get_attribute("href") or ""
            oc = a.get_attribute("onclick") or ""
            s = h + " " + oc
            if re.search(r"camp|reserv|예약|calendar", s, re.I) and "#" != h:
                found.append("[a] " + (a.inner_text() or "").strip()[:20] + " :: " + s[:120])
        html = pg.content()
        for m in re.findall(r"[\"'](/[A-Za-z0-9_/\-]*(?:camp|reserv)[A-Za-z0-9_/\-]*(?:\.do)?[^\"']{0,60})[\"']", html, re.I):
            found.append("[url] " + m)
        (D / "bma_probe.html").write_text(html, encoding="utf-8")
    except Exception as e:
        found.append("[err] " + str(e)[:150])
    uniq = []
    for x in found:
        if x not in uniq:
            uniq.append(x)
    (D / "bma_probe.txt").write_text("\n".join(uniq), encoding="utf-8")
    return uniq[:12]

def main():
    seen = {}
    if SEEN.exists():
        try:
            seen = json.loads(SEEN.read_text(encoding="utf-8"))
        except Exception:
            seen = {}
    send("향남오토캠핑장 감시 시작 · 3분 간격")
    first = True
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        ctx = br.new_context(ignore_https_errors=True,
                             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        pg = ctx.new_page()
        while True:
            try:
                cur = scan(pg)
                new = []
                for k in sorted(cur):
                    sig = ",".join("%d%s" % (c, n) for c, n in cur[k])
                    if seen.get(k) != sig:
                        seen[k] = sig
                        new.append(k)
                for k in list(seen):
                    if k not in cur:
                        del seen[k]
                SEEN.write_text(json.dumps(seen, ensure_ascii=False), encoding="utf-8")
                for k in new:
                    dt = datetime.date(int(k[:4]), int(k[4:6]), int(k[6:]))
                    det = " / ".join("%s %d" % (n, c) for c, n in cur[k])
                    msg = ("⛺ 데크 빈자리 발견\n" + rng(dt) + "\n향남오토캠핑장\n" + det +
                           "\n🟢 집에서 50km\n\n" +
                           '<a href="' + NAV + '">📍 네이버지도</a> <a href="' + RSV + '">🌲 예약하기</a>')
                    send(msg)
                log("확인 %d일치 / 신규 %d건" % (len(cur), len(new)))
                if first:
                    first = False
                    r = probe_bma(pg)
                    send("병목안 구조조사 결과 " + str(len(r)) + "건\n" + ("\n".join(r) if r else "후보 없음"))
            except Exception as e:
                log("루프오류 " + str(e)[:150])
            time.sleep(INTERVAL)

main()