import pathlib, py_compile, sys
p = pathlib.Path("watch.py")
s = p.read_text(encoding="utf-8")
if '"원산도", "칠갑산",' not in s:
    print("이미 빠져 있거나 코드 형태가 다릅니다. 현재 상태:")
    for l in s.splitlines():
        if "ALLOW_CN" in l or "칠갑산" in l:
            print("  ", l)
    sys.exit(0)
p.with_name("watch.py.bak").write_text(s, encoding="utf-8")
p.write_text(s.replace('"원산도", "칠갑산",', '"원산도",'), encoding="utf-8")
try:
    py_compile.compile("watch.py", doraise=True)
except Exception as e:
    p.write_text(s, encoding="utf-8")
    print("문법 오류가 생겨 원래대로 되돌렸습니다:", e)
    sys.exit(1)
print("수정 완료: 충남 허용목록에서 칠갑산 제거 (백업: watch.py.bak)")