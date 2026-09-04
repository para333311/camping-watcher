import re, pathlib, ast, urllib.parse, urllib.request

P = pathlib.Path("watch.py")
s = P.read_text(encoding="utf-8").lstrip("\ufeff")
log = []

old = re.search(r"    return body \+ '\\n\\n<a href=\"' \+ nav.*?\n", s)
new = ("    return body + '\\n\\n<a href=\"' + nav + '\">\\U0001F4CD \\uB124\\uC774\\uBC84\\uC9C0\\uB3C4</a>"
       "      <a href=\"' + fst + '\">\\U0001F332 \\uC232\\uB098\\uB4E4e</a>'\n")
if old:
    s = s[:old.start()] + new + s[old.end():]
    log.append("1 가운데점 제거 OK")
else:
    log.append("1 대상줄 못찾음 FAIL")

try:
    ast.parse(s)
    P.write_text(s, encoding="utf-8")
    log.append("2 문법정상 · 저장완료")
except SyntaxError as e:
    log.append("2 문법오류 FAIL " + str(e))
    print("\n".join(log)); raise SystemExit

env = {}
for ln in pathlib.Path(".env").read_text(encoding="utf-8").splitlines():
    if "=" in ln:
        k, v = ln.split("=", 1); env[k.strip()] = v.strip()
i = s.index("_DIST = {"); j = s.index("\ndef ", s.index("def _fmt"))
ns = {}; exec(s[i:j], ns)
d = urllib.parse.urlencode({
    "chat_id": env["TELEGRAM_CHAT_ID"],
    "text": ns["_fmt"]("빈자리 발견 [수도권]\n8/22(토) ~ 8/23(일)\n[공립](용인시)용인자연휴양림\n예약가능 3"),
    "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
r = urllib.request.urlopen("https://api.telegram.org/bot" + env["TELEGRAM_BOT_TOKEN"] + "/sendMessage", d, timeout=20).read()
log.append("3 테스트발송 " + ("OK" if b'"ok":true' in r else "FAIL " + r.decode()[:200]))
print("\n".join(log))