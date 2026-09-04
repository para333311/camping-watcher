import re, pathlib, getpass, datetime as dt
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
STATE = ROOT / "state.json"
WD = "월화수목금토일"
today = dt.date.today()
sat = today + dt.timedelta((5 - today.weekday()) % 7) + dt.timedelta(weeks=4)
sun = sat + dt.timedelta(days=1)
d = lambda x: "%02d/%02d/%02d(%s)" % (x.year % 100, x.month, x.day, WD[x.weekday()])
BG, ED, PICK = sat.strftime("%Y%m%d"), sun.strftime("%Y%m%d"), d(sat) + " - " + d(sun)
MAIN = "https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=FRIP&menuId=001001"

JS = """(a) => {
  const set=(id,v)=>{const e=document.getElementById(id); if(e) e.value=v;};
  set('srchInsttArcd','1'); set('srchInsttId','');
  set('rsrvtBgDt',a.bg); set('rsrvtEdDt',a.ed); set('calPicker',a.pick);
  const sn=document.getElementById('stng_nofpr'); if(sn) sn.innerHTML='2';
  const fix=()=>document.querySelectorAll('[name="houseCampSctin"]').forEach(h=>h.value=a.hcs);
  for(const f of document.forms){ f.addEventListener('submit',fix,true);
    const os=f.submit.bind(f); f.submit=function(){fix(); os();}; }
  fn_top_goSearch();
}"""

def cards(html):
    r = []
    for b in re.split(r'(?=<div class="rc_item">)', html)[1:]:
        nm = re.search(r"<b>(.*?)</b>", b)
        fc = re.search(r"\[객실\][^<]*", b)
        rc = re.search(r"예약가능 객실 수\s*:\s*(\d+)", b)
        iid = re.search(r"fn_fsfsRsrvtPssblGoodsList\('([^']+)'", b)
        r.append({"nm": nm.group(1) if nm else "?", "fac": (fc.group(0) if fc else "?").strip(),
                  "cnt": int(rc.group(1)) if rc else -1, "id": iid.group(1) if iid else "",
                  "ok": "[예약가능]" in b})
    return r

log = ["DATE %s ~ %s / %s" % (BG, ED, PICK)]
with sync_playwright() as p:
    br = p.chromium.launch(headless=False)
    ctx = br.new_context(storage_state=str(STATE)) if STATE.exists() else br.new_context()
    pg = ctx.new_page()
    pg.goto("https://www.foresttrip.go.kr/com/login.do", timeout=60000)
    if "/com/logout" not in pg.content():
        pg.fill("#mmberId", input("숲나들e 아이디: ").strip())
        pg.fill("#gnrlMmberPssrd", getpass.getpass("비밀번호(안보임): "))
        pg.evaluate("fn_goLogin()"); pg.wait_for_timeout(5000)
    ok = "/com/logout" in pg.content()
    log.append("LOGIN %s" % ok)
    print("로그인:", "성공" if ok else "실패")
    if ok: ctx.storage_state(path=str(STATE))
    best = None
    for tag, hcs in [("A_01", "01"), ("B_02", "02"), ("C_blank", "")]:
        try:
            pg.goto(MAIN, timeout=60000); pg.wait_for_timeout(2500)
            pg.evaluate(JS, {"bg": BG, "ed": ED, "pick": PICK, "hcs": hcs})
            pg.wait_for_timeout(9000)
            h = pg.content(); (OUT / ("res_%s.html" % tag)).write_text(h, encoding="utf-8")
            cs = cards(h)
            log.append("=== %s (houseCampSctin=%r) cards=%d url_hcs=%s" %
                       (tag, hcs, len(cs), re.search(r"houseCampSctin=([^&]*)", pg.url).group(1)
                        if "houseCampSctin=" in pg.url else "none"))
            for c in cs[:25]:
                log.append("  %s | %s | 예약가능수=%d | %s | %s" % (c["nm"], c["fac"], c["cnt"], c["ok"], c["id"]))
            if best is None:
                for c in cs:
                    m = re.search(r"\[야영장\]\s*(\d+)", c["fac"])
                    if c["id"] and c["cnt"] > 0 and m and int(m.group(1)) > 0:
                        best = c; break
        except Exception as e:
            log.append("=== %s ERROR %s %s" % (tag, type(e).__name__, str(e)[:120]))
    if best:
        try:
            pg.goto(MAIN, timeout=60000); pg.wait_for_timeout(2500)
            pg.evaluate(JS, {"bg": BG, "ed": ED, "pick": PICK, "hcs": ""}); pg.wait_for_timeout(9000)
            pg.evaluate("fn_fsfsRsrvtPssblGoodsList('%s')" % best["id"]); pg.wait_for_timeout(9000)
            dh = pg.content(); (OUT / "detail.html").write_text(dh, encoding="utf-8")
            pg.screenshot(path=str(OUT / "detail.png"), full_page=True)
            log.append("=== DETAIL %s %s url=%s len=%d" % (best["nm"], best["id"], pg.url[:150], len(dh)))
            i = dh.find("야영")
            log.append(re.sub(r"\s+", " ", dh[max(0, i - 1500):i + 2500]) if i >= 0 else "야영 NOT FOUND")
        except Exception as e:
            log.append("=== DETAIL ERROR %s %s" % (type(e).__name__, str(e)[:120]))
    else:
        log.append("=== DETAIL SKIP (야영장 보유 + 예약가능 휴양림 없음)")
    input("엔터 누르면 브라우저 종료: ")
    br.close()
(OUT / "summary2.txt").write_text("\n".join(log), encoding="utf-8")
print("saved out/summary2.txt")
