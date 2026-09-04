import pathlib, ast, urllib.parse, urllib.request

P = pathlib.Path("watch.py")
L = P.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
log = []

def one(sub, new, tag):
    for n, l in enumerate(L):
        if sub in l:
            L[n] = new
            log.append(tag + " OK")
            return True
    log.append(tag + " FAIL")
    return False

one('[name="houseCampSctin"]',
    """    document.querySelectorAll('[name="houseCampSctin"]').forEach(h=>h.value=a.sc);""",
    "1 houseCampSctin")

one('"area": acd})',
    '                                         "pick": fmt(sat) + " - " + fmt(sun), "area": acd, "sc": sc})',
    "2 sc 파라미터")

one('cur["%s|%s" % (sat.strftime',
    '                            cur["%s|%s|%s" % (sat.strftime("%Y%m%d"), sc, iid)] = (sat, nm, cnt, snm)',
    "3 키 분리")

one('sat, nm, cnt, anm = cur[k]',
    '                    sat, nm, cnt, snm = cur[k]',
    "4 언패킹")

one('빈자리 발견 [%s]',
    '                    tg("%s 빈자리\\n%d/%d(\\ud1a0) ~ %d/%d(\\uc77c)\\n%s\\n\\uc608\\uc57d\\uac00\\ub2a5 %d"',
    "5 제목 분리")

one('(sat + dt.timedelta(days=1)).day, nm, cnt, MAIN))',
    '                          (sat + dt.timedelta(days=1)).day, nm, cnt))',
    "6 링크줄 제거")

one('% (anm, sat.month, sat.day',
    '                       % (snm, sat.month, sat.day, (sat + dt.timedelta(days=1)).month,',
    "7 인자 교체")

one('감시 시작 ·',
    '    tg("\\uac10\\uc2dc \\uc2dc\\uc791 \\u00b7 \\uc219\\uc18c+\\ub370\\ud06c / \\ub2e4\\uc74c %d\\uc8fc \\ud1a0~\\uc77c / %d\\ubd84 \\uac04\\uaca9"',
    "8 시작문구")

st = nx = -1
for n, l in enumerate(L):
    if "for acd, anm in AREAS:" in l:
        st = n
    if st >= 0 and n > st and "time.sleep(1)" in l:
        nx = n
        break
if st < 0 or nx < 0:
    log.append("9 루프 FAIL")
else:
    ind = L[st][:len(L[st]) - len(L[st].lstrip())]
    inner = ind + '    for sc, snm in (("01", "\U0001F3E0 \uc219\uc18c"), ("02", "\u26FA \ub370\ud06c")):'
    L[st + 1:nx + 1] = [inner] + ["    " + b for b in L[st + 1:nx + 1]]
    log.append("9 이중루프 OK")

s = "\n".join(L) + "\n"
try:
    ast.parse(s)
    P.write_text(s, encoding="utf-8")
    log.append("10 문법정상 · 저장완료")
except SyntaxError as e:
    log.append("10 문법오류 FAIL line %s: %s" % (e.lineno, e.text))
    print("\n".join(log)); raise SystemExit

E = pathlib.Path(".env")
E.write_text("\n".join(("INTERVAL_SEC=120" if x.startswith("INTERVAL_SEC") else x)
                       for x in E.read_text(encoding="utf-8").splitlines()), encoding="utf-8")
log.append("11 간격 120초 OK")

env = {}
for ln in E.read_text(encoding="utf-8").splitlines():
    if "=" in ln:
        k, v = ln.split("=", 1); env[k.strip()] = v.strip()
i = s.index("_DIST = {"); j = s.index("\ndef ", s.index("def _fmt"))
ns = {}; exec(s[i:j], ns)
for t in ("\U0001F3E0 \uc219\uc18c \ube48\uc790\ub9ac\n8/22(\ud1a0) ~ 8/23(\uc77c)\n[\uacf5\ub9bd](\uc6a9\uc778\uc2dc)\uc6a9\uc778\uc790\uc5f0\ud734\uc591\ub9bc\n\uc608\uc57d\uac00\ub2a5 3",
          "\u26FA \ub370\ud06c \ube48\uc790\ub9ac\n8/22(\ud1a0) ~ 8/23(\uc77c)\n[\uacf5\ub9bd](\uc548\uc131\uc2dc)\uc11c\uc6b4\uc0b0\uc790\uc5f0\ud734\uc591\ub9bc\n\uc608\uc57d\uac00\ub2a5 2"):
    d = urllib.parse.urlencode({"chat_id": env["TELEGRAM_CHAT_ID"], "text": ns["_fmt"](t),
                                "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
    r = urllib.request.urlopen("https://api.telegram.org/bot" + env["TELEGRAM_BOT_TOKEN"] + "/sendMessage", d, timeout=20).read()
    log.append("12 테스트발송 " + ("OK" if b'"ok":true' in r else "FAIL"))
print("\n".join(log))