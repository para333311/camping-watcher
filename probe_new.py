import re, pathlib
from playwright.sync_api import sync_playwright

T = [("향남오토캠핑장", "https://yeyak.hscity.go.kr/1098/3058/campCalendarList.do?campIdx=2"),
     ("병목안캠핑장", "https://www.auc.or.kr/bmacamp/contents/view?contentsNo=316&menuLevel=2&menuNo=133"),
     ("병목안메인", "https://www.auc.or.kr/bmacamp/main/view")]

out = []
with sync_playwright() as p:
    br = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
    ctx = br.new_context(ignore_https_errors=True)
    for nm, u in T:
        pg = ctx.new_page()
        out.append("\n\n######## %s\n%s" % (nm, u))
        try:
            pg.goto(u, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(5000)
            out.append("[TITLE] " + pg.title())
            out.append("[URL] " + pg.url)
            fr = pg.frames
            out.append("[FRAMES] %d" % len(fr))
            for f in fr:
                if f.url and f.url != pg.url:
                    out.append("   iframe: " + f.url)
            t = re.sub(r"\n{3,}", "\n\n", pg.inner_text("body"))
            out.append("[TEXT %d자]" % len(t))
            out.append(t[:4000])
            h = pg.content()
            for kw in ("잔여", "예약가능", "마감", "campIdx", "Calendar", "reserv"):
                n = h.count(kw)
                if n:
                    i = h.index(kw)
                    out.append("[HTML %s x%d] %s" % (kw, n, re.sub(r"\s+", " ", h[max(0, i - 300):i + 300])))
        except Exception as e:
            out.append("[ERROR] %s %s" % (type(e).__name__, str(e)[:200]))
        pg.close()
    br.close()

pathlib.Path("out").mkdir(exist_ok=True)
pathlib.Path("out/probe_new.txt").write_text("\n".join(out), encoding="utf-8")
print("saved")