import re, pathlib

P = pathlib.Path("watch.py")
L = P.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
key = ("빈자리 발견", "houseCampSctin", "goodsClsscCampCdArr", "goodsClsscHouseCdArr",
       "seen", "def loop", "def main", "for acd", "srchRsrvtBgDt", "02002")
show = set()
for n, l in enumerate(L):
    if any(k in l for k in key):
        for x in range(max(0, n - 14), min(len(L), n + 8)):
            show.add(x)
print("TOTAL", len(L))
prev = 0
for n in sorted(show):
    if n - prev > 1:
        print("   ...")
    print(str(n + 1).rjust(4), L[n][:160])
    prev = n