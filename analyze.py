import re, pathlib, collections
h = pathlib.Path("out/result.html").read_text(encoding="utf-8", errors="ignore")
out = []
out.append("LEN %d" % len(h))
cls = collections.Counter(c for m in re.findall(r'class="([^"]+)"', h) for c in m.split())
out.append("TOPCLASS " + str(cls.most_common(30)))
for kw in ["야영", "데크", "예약가능", "예약하기", "잔여", "마감", "검색결과", "건"]:
    out.append("KW %s %d" % (kw, h.count(kw)))
for kw in ["야영", "예약"]:
    i = h.find(kw)
    out.append("---CTX %s---" % kw)
    out.append(re.sub(r"\s+", " ", h[max(0, i-1200):i+1200]) if i >= 0 else "NOT FOUND")
pathlib.Path("out/analyze.txt").write_text("\n".join(out), encoding="utf-8")
print("saved")
