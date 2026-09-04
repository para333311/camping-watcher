import re, pathlib, ast, urllib.parse, urllib.request

FMT = r"""_DIST = {"의왕바라산":30,"무봉산":55,"신암저수지":55,"용인":60,"서운산":85,"영인산":95,"태학산":105,"봉수산":120,"오서산":135,"용현":140,"칠갑산":145,"성주산":165,"원산도":185}


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
    return body + '\n\n<a href="' + nav + '">📍 네이버지도 바로가기</a>\n<a href="' + fst + '">🌲 숲나들e 바로가기</a>'
"""

P = pathlib.Path("watch.py")
s = P.read_text(encoding="utf-8").lstrip("\ufeff")
log = []

i = s.find("_DIST = {")
if i != -1:
    m = re.search(r'^def (?!_fmt)\w+', s[i:], re.M)
    s = s[:i] + (s[i + m.start():] if m else "")
    log.append("1 기존 표시코드 제거 OK")
else:
    log.append("1 기존 표시코드 없음")

funcs = list(re.finditer(r'^def\s+(\w+)\s*\(([^)]*)\)\s*:', s, re.M))
ti = None
for k, f in enumerate(funcs):
    end = funcs[k + 1].start() if k + 1 < len(funcs) else len(s)
    if "api.telegram.org" in s[f.start():end]:
        ti = (f, end)
        break

if ti is None:
    log.append("2 텔레그램 함수 못찾음 FAIL")
else:
    f, end = ti
    he = s.index("\n", f.end()) + 1
    body = s[he:end]
    arg = (f.group(2).split(",")[0].strip().split("=")[0].strip() or "msg")
    body = re.sub(r'^\s*' + arg + r'\s*=\s*_fmt\(' + arg + r'\)\s*\n', '', body, flags=re.M)
    if '"parse_mode"' not in body and "'parse_mode'" not in body:
        body, n1 = re.subn(r'(["\'])text\1(\s*:\s*)([^,}\n]+)',
                           r'"text"\2\3, "parse_mode": "HTML", "disable_web_page_preview": "true"',
                           body, count=1)
        log.append("2 parse_mode " + ("OK" if n1 else "FAIL"))
    else:
        log.append("2 parse_mode 이미적용")
    body = "    " + arg + " = _fmt(" + arg + ")\n" + body
    s = s[:he] + body + s[end:]
    s = s[:f.start()] + FMT + "\n\n" + s[f.start():]
    log.append("3 색깔+링크 적용 OK")

try:
    ast.parse(s)
    P.write_text(s, encoding="utf-8")
    log.append("4 문법정상 · 저장완료")
except SyntaxError as e:
    log.append("4 문법오류 FAIL " + str(e))
    print("\n".join(log))
    raise SystemExit

env = {}
for ln in pathlib.Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in ln:
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()
ns = {}
exec(FMT, ns)
d = urllib.parse.urlencode({
    "chat_id": env["TELEGRAM_CHAT_ID"],
    "text": ns["_fmt"]("빈자리 발견 [수도권]\n8/22(토) ~ 8/23(일)\n[공립](용인시)용인자연휴양림\n예약가능 3"),
    "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
r = urllib.request.urlopen("https://api.telegram.org/bot" + env["TELEGRAM_BOT_TOKEN"] + "/sendMessage", d, timeout=20).read()
log.append("5 테스트발송 " + ("OK" if b'"ok":true' in r else "FAIL " + r.decode()[:200]))

print("\n".join(log))
print("=== DUMP (아래 전부 복사해서 보내주세요) ===")
L = s.splitlines()
hit = [n for n, l in enumerate(L) if ("빈자리 발견" in l) or ("houseCampSctin" in l) or ("goodsClsscCampCdArr" in l)]
show = set()
for n in hit:
    for x in range(max(0, n - 12), min(len(L), n + 6)):
        show.add(x)
for n in sorted(show):
    print(str(n + 1).rjust(4), L[n][:150])