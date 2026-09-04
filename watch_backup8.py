import re, json, time, pathlib, datetime as dt, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
STATE = ROOT / "state.json"; SEEN = ROOT / "seen.json"; LOG = ROOT / "watch.log"
env = {}
for ln in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1); env[k.strip()] = v.strip()
TOKEN, CHAT = env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]
FID, FPW = env["FOREST_ID"], env["FOREST_PW"]
WEEKS, INTERVAL = int(env.get("WEEKS", "8")), int(env.get("INTERVAL_SEC", "300"))
HEADLESS = env.get("HEADLESS", "1") == "1"
AREAS = [("1", "수도권"), ("4", "충남")]
EXCLUDE = ["설매재", "고대산", "백운봉", "중미산", "유명산", "산음", "덕적도",
           "강화", "석모도", "무의도", "가평", "청평", "칼봉산", "강씨봉",
           "포천", "천보산", "운악산", "연천", "동두천", "양주", "아세안",
           "축령산", "양평", "수락산", "쉬자파크"]
ALLOW_CN = ["오서산", "봉수산", "용현", "성주산", "원산도", "칠갑산",
            "희리산", "영인산", "태학산"]
MAIN = "https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=FRIP&menuId=001001"
WD = "월화수목금토일"

def log(m):
    s = "%s %s" % (dt.datetime.now().strftime("%m-%d %H:%M:%S"), m)
    print(s, flush=True)
    with LOG.open("a", encoding="utf-8") as f: f.write(s + "\n")

_DIST = {"의왕바라산":30,"무봉산":55,"신암저수지":55,"용인":60,"서운산":85,"영인산":95,"태학산":105,"봉수산":120,"오서산":135,"용현":140,"칠갑산":145,"성주산":165,"원산도":185}


def _fmt(t):
    import html as _h, re as _r, urllib.parse as _up
    t = _r.sub(r'https?://\S+', '', str(t)).strip()
    place = ''
    out = []
    for l in [x.rstrip() for x in t.splitlines() if x.strip()]:
        if not place and ('휴양림' in l or '야영장' in l):
            place = _r.sub(r'[\[\]()]', ' ', l.split(')')[-1]).strip()
            km = 0
            for k, v in _DIST.items():
                if k in place:
                    km = v
                    break
            mk = '⚪' if km == 0 else ('🟢' if km <= 60 else ('🟡' if km <= 100 else '🔴'))
            out.append(mk + ' ' + l)
        else:
            out.append(l)
    body = _h.escape('\n'.join(out))
    if not place:
        return body
    nav = 'https://map.naver.com/p/search/' + _up.quote(place)
    fst = 'https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=FRIP&menuId=001001'
    return body + '\n\n<a href="' + nav + '">\U0001F4CD \uB124\uC774\uBC84\uC9C0\uB3C4</a> <a href="' + fst + '">\U0001F332 \uC232\uB098\uB4E4e</a>'


def tg(text, silent=False):
    text = _fmt(text)
    d = urllib.parse.urlencode({"chat_id": CHAT, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true",
        "disable_notification": "true" if silent else "false"}).encode()
    try:
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % TOKEN, d, timeout=20).read()
    except Exception as e:
        log("TG FAIL %s %s" % (type(e).__name__, str(e)[:80]))

JS = """(a) => {
  const set=(id,v)=>{const e=document.getElementById(id); if(e) e.value=v;};
  set('srchInsttArcd',a.area); set('srchInsttId','');
  set('rsrvtBgDt',a.bg); set('rsrvtEdDt',a.ed); set('calPicker',a.pick);
  const sn=document.getElementById('stng_nofpr'); if(sn) sn.innerHTML='2';
  const fix=()=>{
    document.querySelectorAll('[name="houseCampSctin"]').forEach(h=>h.value=a.sc);
    document.querySelectorAll('[name="goodsClsscCampCdArr"]').forEach(h=>h.value='');
    document.querySelectorAll('[name="goodsClsscHouseCdArr"]').forEach(h=>h.value='');
  };
  for(const q of document.forms){ q.addEventListener('submit',fix,true);
    const os=q.submit.bind(q); q.submit=function(){fix(); os();}; }
  fn_top_goSearch();
}"""

def fmt(x): return "%02d/%02d/%02d(%s)" % (x.year % 100, x.month, x.day, WD[x.weekday()])

def rng(a):
    b = a + dt.timedelta(days=1)
    s = "%d/%d(%s) ~ " % (a.month, a.day, WD[a.weekday()])
    if a.month == b.month:
        return s + "%d(%s)" % (b.day, WD[b.weekday()])
    return s + "%d/%d(%s)" % (b.month, b.day, WD[b.weekday()])


HOL = {"20260815", "20260817", "20260924", "20260925", "20260926",
       "20261003", "20261005", "20261009", "20261225",
       "20270101", "20270301"}


def _off(d):
    return d.weekday() >= 5 or d.strftime("%Y%m%d") in HOL


def targets():
    t0 = dt.date.today()
    out = []
    for i in range(0, WEEKS * 7 + 1):
        d = t0 + dt.timedelta(days=i)
        n = d + dt.timedelta(days=1)
        if _off(d) and _off(n):
            out.append(d)
    return out

def parse(html, acd):
    r = []
    for b in re.split(r'(?=<div class="rc_item">)', html)[1:]:
        nm = re.search(r"<b>(.*?)</b>", b)
        rc = re.search(r"예약가능 객실 수\s*:\s*(\d+)", b)
        iid = re.search(r"fn_fsfsRsrvtPssblGoodsList\('([^']+)'", b)
        if not (nm and rc and iid and int(rc.group(1)) > 0):
            continue
        name = re.sub(r"<[^>]+>", "", nm.group(1)).strip()
        if acd == "4":
            if not any(w in name for w in ALLOW_CN):
                continue
        elif any(x in name for x in EXCLUDE):
            continue
        r.append((iid.group(1), name, int(rc.group(1))))
    return r

def login(pg):
    pg.goto("https://www.foresttrip.go.kr/com/login.do", timeout=60000)
    if "/com/logout" in pg.content(): return True
    pg.fill("#mmberId", FID); pg.fill("#gnrlMmberPssrd", FPW)
    pg.evaluate("fn_goLogin()"); pg.wait_for_timeout(6000)
    return "/com/logout" in pg.content()

def main():
    seen = set(json.loads(SEEN.read_text(encoding="utf-8"))) if SEEN.exists() else set()
    fails = 0; warned = False; beat = None
    tg("\uac10\uc2dc \uc2dc\uc791 \u00b7 \uc219\uc18c+\ub370\ud06c / \ub2e4\uc74c %d\uc8fc \ud1a0~\uc77c / %d\ubd84 \uac04\uaca9"
       % (WEEKS, INTERVAL // 60), silent=True)
    with sync_playwright() as p:
        br = p.chromium.launch(headless=HEADLESS)
        ctx = br.new_context(storage_state=str(STATE)) if STATE.exists() else br.new_context()
        pg = ctx.new_page()
        while True:
            now = dt.datetime.now()
            if now.hour < 7:
                time.sleep(600); continue
            try:
                if not login(pg):
                    raise RuntimeError("login failed")
                ctx.storage_state(path=str(STATE))
                cur = {}
                for sat in targets():
                    sun = sat + dt.timedelta(days=1)
                    for acd, anm in AREAS:
                        for sc, snm in (("01", "🏠 숙소"), ("02", "⛺ 데크")):
                            pg.goto(MAIN, timeout=60000); pg.wait_for_timeout(1500)
                            pg.evaluate(JS, {"bg": sat.strftime("%Y%m%d"), "ed": sun.strftime("%Y%m%d"),
                                             "pick": fmt(sat) + " - " + fmt(sun), "area": acd, "sc": sc})
                            try:
                                pg.wait_for_selector(".rc_item", timeout=12000)
                                pg.wait_for_timeout(600)
                            except Exception:
                                pg.wait_for_timeout(4000)
                            for iid, nm, cnt in parse(pg.content(), acd):
                                cur["%s|%s|%s" % (sat.strftime("%Y%m%d"), sc, iid)] = (sat, nm, cnt, snm)
                            time.sleep(1)
                new = [k for k in cur if k not in seen]
                for k in new:
                    sat, nm, cnt, snm = cur[k]
                    tg("%s \ube48\uc790\ub9ac\n%s\n%s\n\uc608\uc57d\uac00\ub2a5 %d" % (snm, rng(sat), nm, cnt))
                seen = set(cur)
                SEEN.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")
                log("ok dates=%d areas=%d avail=%d new=%d" % (WEEKS, len(AREAS), len(cur), len(new)))
                fails = 0; warned = False
                if beat != now.date() and now.hour >= 8:
                    beat = now.date()
                    tg("감시 정상 작동중 · 현재 빈자리 %d건" % len(cur), silent=True)
            except Exception as e:
                fails += 1
                log("ERR(%d) %s %s" % (fails, type(e).__name__, str(e)[:120]))
                if fails >= 5 and not warned:
                    warned = True
                    tg("감시봇 오류 5회 연속: %s / %s" % (type(e).__name__, str(e)[:120]))
                try:
                    pg.close(); ctx.close()
                    ctx = br.new_context(storage_state=str(STATE)) if STATE.exists() else br.new_context()
                    pg = ctx.new_page()
                except Exception: pass
                time.sleep(60)
            time.sleep(INTERVAL)

main()
