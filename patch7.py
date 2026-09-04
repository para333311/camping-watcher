import pathlib, ast, re, datetime as dt

P = pathlib.Path("watch.py")
L = P.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
log = []

i = next((n for n, l in enumerate(L) if "if _off(n)" in l), -1)
if i < 0:
    log.append("1 조건줄 못찾음 FAIL")
else:
    ind = L[i][:len(L[i]) - len(L[i].lstrip())]
    L[i] = ind + "if _off(d) and _off(n):"
    log.append("1 조건 변경 OK")

s = "\n".join(L) + "\n"
try:
    ast.parse(s)
    P.write_text(s, encoding="utf-8")
    log.append("2 문법정상 · 저장완료")
except SyntaxError as e:
    log.append("2 문법오류 FAIL line %s: %s" % (e.lineno, e.text))
    print("\n".join(log)); raise SystemExit

w = 8
for ln in pathlib.Path(".env").read_text(encoding="utf-8").splitlines():
    if ln.startswith("WEEKS"):
        w = int(ln.split("=", 1)[1].strip())
a = next(n for n, l in enumerate(L) if l.startswith("def rng"))
b = next(n for n, l in enumerate(L) if l.startswith("def targets"))
c = next((n for n in range(b + 1, len(L)) if L[n].startswith("def ")), len(L))
ns = {"dt": dt, "WEEKS": w}
exec(re.search(r'^WD\s*=.*$', s, re.M).group(0), ns)
exec("\n".join(L[a:c]), ns)
d = ns["targets"]()
print("\n".join(log))
print("3 감시할 밤 %d개" % len(d))
for x in d:
    print("   " + ns["rng"](x))