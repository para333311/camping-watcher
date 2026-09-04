import datetime, getpass, pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
KOR = ["월","화","수","목","금","토","일"]

d = datetime.date.today()
sat = d + datetime.timedelta(days=(5 - d.weekday()) % 7) + datetime.timedelta(weeks=4)
sun = sat + datetime.timedelta(days=1)
bg, ed = sat.strftime("%Y%m%d"), sun.strftime("%Y%m%d")
pick = "%s(%s) - %s(%s)" % (sat.strftime("%y/%m/%d"), KOR[sat.weekday()],
                            sun.strftime("%y/%m/%d"), KOR[sun.weekday()])
print("조회 날짜:", pick)

uid = input("숲나들e 아이디: ").strip()
pw = getpass.getpass("비밀번호(화면에 안 보입니다): ")

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    pg = b.new_page()
    pg.goto("https://www.foresttrip.go.kr/com/login.do", timeout=60000)
    pg.fill("#mmberId", uid)
    pg.fill("#gnrlMmberPssrd", pw)
    pg.evaluate("fn_goLogin()")
    pg.wait_for_timeout(7000)
    ok = "/com/logout" in pg.content()
    print("로그인:", "성공" if ok else "실패")
    pg.screenshot(path=str(OUT / "login.png"), full_page=True)
    if not ok:
        (OUT / "login.html").write_text(pg.content(), encoding="utf-8")
        input("로그인 실패. out 폴더 확인 후 엔터")
        b.close()
        raise SystemExit

    pg.goto("https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=FRIP&menuId=001001", timeout=60000)
    pg.wait_for_timeout(4000)
    pg.evaluate("""(a) => {
        const f = "form[name='srch_frm']";
        window.$("#srchInsttArcd", f).val("1");
        window.$("#srchInsttId", f).val("");
        window.$("#rsrvtBgDt", f).val(a[0]);
        window.$("#rsrvtEdDt", f).val(a[1]);
        window.$("#calPicker", f).val(a[2]);
        window.$("#srchUseDt", f).val(a[2]);
        window.$("#srchSthngCnt", f).val("1");
        window.$("#srchStngNofpr", f).val("2");
        window.$("#stng_nofpr").html("2");
    }""", [bg, ed, pick])
    print("설정 확인:", pg.evaluate("""() => {
        const f = "form[name='srch_frm']";
        return [window.$("#rsrvtBgDt", f).val(), window.$("#calPicker", f).val()].join(" | ");
    }"""))
    try:
        with pg.expect_navigation(timeout=45000):
            pg.evaluate("fn_top_goSearch()")
    except Exception as e:
        print("이동 대기 예외(계속 진행):", type(e).__name__)
    pg.wait_for_timeout(6000)
    print("결과 URL:", pg.url)
    (OUT / "result.html").write_text(pg.content(), encoding="utf-8")
    pg.screenshot(path=str(OUT / "result.png"), full_page=True)
    print("저장 완료:", OUT)
    input("엔터 누르면 브라우저가 닫힙니다")
    b.close()
