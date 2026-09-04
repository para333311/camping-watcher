import re, ast, pathlib

P = pathlib.Path("watch.py")
src = P.read_text(encoding="utf-8").lstrip("\ufeff")
L = src.splitlines()

HOUSE = "01001,01002,01003,01004,01005,01006,01007,01008,01009,01010,01011"
CAMP  = "02001,02002,02003,02005,02007,02011"

cnt = 0
for i, l in enumerate(L):
    if "희리산" in l and "EXCLUDE" not in l:
        n = re.sub(r"['\"]희리산[^'\"]*['\"]\s*,?\s*", "", l)
        if n != l:
            L[i] = n
            cnt += 1
print("1 희리산 목록에서 제거:", cnt, "줄")
print("2 EXCLUDE 희리산:", "있음" if any(("EXCLUDE" in l and "희리산" in l) for l in L) else "없음")

if CAMP in src:
    print("3 이미 적용되어 있음 - 건너뜀")
else:
    cand = [i for i, l in enumerate(L) if "houseCampSctin" in l]
    if not cand:
        pathlib.Path("ctx.txt").write_text("houseCampSctin 을 watch.py 에서 찾지 못했습니다.", encoding="utf-8")
        print("3 FAIL houseCampSctin 없음")
        raise SystemExit
    i = cand[-1]
    line = L[i]
    if not any(k in line for k in ("document.", "getElementsByName", "querySelector")):
        s = max(0, i - 12); e = min(len(L), i + 12)
        pathlib.Path("ctx.txt").write_text("\n".join(str(n+1).rjust(4) + " " + L[n] for n in range(s, e)), encoding="utf-8")
        print("3 FAIL 위치가 JS가 아님 - ctx.txt 확인")
        raise SystemExit
    q = "'" if "'" in line else '"'
    ind = re.match(r"\s*", line).group(0)
    js = ("var _s=document.getElementsByName(QhouseCampSctinQ)[0],_v=_s?_s.value:QQ,"
          "_cb=document.getElementsByName(QcampQ),_hb=document.getElementsByName(QhouseQ),_i=0,_j=0;"
          "for(_i=0;_i<_cb.length;_i++)_cb[_i].checked=(_v==Q02Q&&Q," + CAMP + ",Q.indexOf(Q,Q+_cb[_i].value+Q,Q)>=0);"
          "for(_j=0;_j<_hb.length;_j++)_hb[_j].checked=(_v==Q01Q);"
          "var _h=document.getElementsByName(QgoodsClsscHouseCdArrQ)[0],_c=document.getElementsByName(QgoodsClsscCampCdArrQ)[0];"
          "if(_h)_h.value=(_v==Q01Q)?Q" + HOUSE + "Q:QQ;"
          "if(_c)_c.value=(_v==Q02Q)?Q" + CAMP + "Q:QQ;").replace("Q", q)
    L.insert(i + 1, ind + js)
    print("3 시설종류 필터 삽입 OK (", i + 2, "번째 줄 )")

new = "\n".join(L) + "\n"
try:
    ast.parse(new)
    print("4 문법검사 OK")
except SyntaxError as e:
    pathlib.Path("ctx.txt").write_text("문법오류 " + str(e), encoding="utf-8")
    print("4 FAIL 문법오류 - 원본 유지")
    raise SystemExit
P.write_text(new, encoding="utf-8")
print("5 저장 OK")