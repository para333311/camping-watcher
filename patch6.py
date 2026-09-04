import pathlib, ast, re, datetime as dt

P = pathlib.Path("watch.py")
L = P.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
log = []

var = "snm" if any("for sc, snm in" in l for l in L) else "anm"
log.append("0 숙소/데크 분리 " + ("적용됨" if var == "snm" else "미적용"))

NEW = '''def rng(a):
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
        if _off(n) and (_off(d) or n.strftime("%Y%m%d") in HOL):
            out.append(d)
    return out
'''

st = next((n for n, l in enumerate(L) if l.startswith("def targets")), -1)
if st < 0:
    log.append("1 targets FAIL")
else:
    en = next((n for n in range(st + 1, len(L)) if L[n].startswith("def ")), len(L))
    L[st:en] = NEW.splitlines() + [""]
    log.append("1 연휴계산 교체 OK")


def block(cond, mk, tag):
    i = next((n for n, l in enumerate(L) if cond(l)), -1)
    if i < 0:
        log.append(tag + " FAIL")
        return
    j, bal = i, 0
    while j < len(L):
        bal += L[j].count("(") - L[j].count(")")
        if bal <= 0:
            break
        j += 1
    ind = L[i][:len(L[i]) - len(L[i].lstrip())]
    L[i:j + 1] = [ind + mk]
    log.append(tag + " OK")


block(lambda l: "tg(" in l and "빈자리" in l,
      'tg("%s \\ube48\\uc790\\ub9ac\\n%s\\n%s\\n\\uc608\\uc57d\\uac00\\ub2a5 %d" % ('
      + var + ', rng(sat), nm, cnt))', "2 날짜표기")

block(lambda l: "tg(" in l and "감시 시작" in l,
      'tg("\\uac10\\uc2dc \\uc2dc\\uc791 \\u00b7 \\uc219\\uc18c+\\ub370\\ud06c / %d\\uc8fc\\uac04 '
      '\\uc8fc\\ub9d0\\u00b7\\uc5f0\\ud734 %d\\ubc15 / %d\\ubd84 \\uac04\\uaca9" '
      '% (WEEKS, len(targets()), INTERVAL // 60), silent=True)', "3 시작문구")

i = next((n for n, l in enumerate(L) if "wait_for_timeout(7000)" in l), -1)
if i < 0:
    log.append("4 대기시간 SKIP")
else:
    ind = L[i][:len(L[i]) - len(L[i].lstrip())]
    L[i:i + 1] = [ind + "try:", ind + '    pg.wait_for_selector(".rc_item", timeout=12000)',
                  ind + "    pg.wait_for_timeout(600)", ind + "except Exception:",
                  ind + "    pg.wait_for_timeout(4000)"]
    log.append("4 조회속도 개선 OK")

s = "\n".join(L) + "\n"
try:
    ast.parse(s)
    P.write_text(s, encoding="utf-8")
    log.append("5 문법정상 · 저장완료")
except SyntaxError as e:
    log.append("5 문법오류 FAIL line %s: %s" % (e.lineno, e.text))
    print("\n".join(log)); raise SystemExit

ns = {"dt": dt, "WEEKS": int(re.search(r'WEEKS.*?int\(env\.get\("WEEKS",\s*"(\d+)"', s).group(1))}
exec(re.search(r'^WD\s*=.*$', s, re.M).group(0), ns)
exec(NEW, ns)
d = ns["targets"]()
print("\n".join(log))
print("6 감시할 밤 %d개" % len(d))
for x in d:
    print("   " + ns["rng"](x))