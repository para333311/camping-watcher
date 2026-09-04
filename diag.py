import re, json, traceback, pathlib, datetime as dt, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).parent
env = {}
for ln in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1); env[k.strip()] = v.strip()
print("ENV keys:", sorted(env.keys()), "PW len:", len(env.get("FOREST_PW","")))
TOKEN, CHAT = env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]
try:
    d = urllib.parse.urlencode({"chat_id": CHAT, "text": "테스트: 연결 확인"}).encode()
    r = urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % TOKEN, d, timeout=20).read()
    print("TELEGRAM OK", r[:80])
except Exception as e:
    print("TELEGRAM FAIL", type(e).__name__, str(e)[:200])
WD = "월화수목금토일"
t = dt.date.today(); sat = t + dt.timedelta((5 - t.weekday()) % 7); sun = sat + dt.timedelta(days=1)
f = lambda x: "%02d/%02d/%02d(%s)" % (x.year % 100, x.month, x.day, WD[x.weekday()])
JS = """(a) => {
  const set=(id,v)=>{const e=document.getElementById(id); if(e) e.value=v;};
  set('srchInsttArcd','1'); set('srchInsttId','');
  set('rsrvtBgDt',a.bg); set('rsrvtEdDt',a.ed); set('calPicker',a.pick);
  const sn=document.getElementById('stng_nofpr'); if(sn) sn.innerHTML='2';
  const fix=()=>{
    document.querySelectorAll('[name="houseCampSctin"]').forEach(h=>h.value='02');
    document.querySelectorAll('[name="goodsClsscCampCdArr"]').forEach(h=>h.value=a.cd);
    document.querySelectorAll('[name="goodsClsscHouseCdArr"]').forEach(h=>h.value='');
  };
  for(const q of document.forms){ q.addEventListener('submit',fix,true);
    const os=q.submit.bind(q); q.submit=function(){fix(); os();}; }
  fn_top_goSearch();
}"""
try:
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        ctx = br.new_context(); pg = ctx.new_page()
        pg.goto("https://www.foresttrip.go.kr/com/login.do", timeout=60000)
        print("STEP1 login page ok")
        pg.fill("#mmberId", env["FOREST_ID"]); pg.fill("#gnrlMmberPssrd", env["FOREST_PW"])
        pg.evaluate("fn_goLogin()"); pg.wait_for_timeout(7000)
        print("STEP2 login:", "/com/logout" in pg.content())
        pg.goto("https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=FRIP&menuId=001001", timeout=60000)
        pg.wait_for_timeout(2500)
        pg.evaluate(JS, {"bg": sat.strftime("%Y%m%d"), "ed": sun.strftime("%Y%m%d"),
                         "pick": f(sat)+" - "+f(sun), "cd": "02002"})
        pg.wait_for_timeout(9000)
        print("STEP3 url:", pg.url[:200])
        h = pg.content(); print("STEP4 html len:", len(h), "cards:", h.count('class="rc_item"'))
        for b in re.split(r'(?=<div class="rc_item">)', h)[1:]:
            nm = re.search(r"<b>(.*?)</b>", b); rc = re.search(r"예약가능 객실 수\s*:\s*(\d+)", b)
            iid = re.search(r"fn_fsfsRsrvtPssblGoodsList\('([^']+)'", b)
            if nm and rc and int(rc.group(1)) > 0:
                print("  AVAIL", re.sub(r"<[^>]+>","",nm.group(1)).strip(), rc.group(1), iid.group(1) if iid else "-")
        pathlib.Path("out").mkdir(exist_ok=True)
        pathlib.Path("out/diag.html").write_text(h, encoding="utf-8")
        br.close()
except Exception:
    traceback.print_exc()
print("=== 진단 끝 ===")
