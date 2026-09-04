import re, pathlib
h = pathlib.Path("out/result.html").read_text(encoding="utf-8", errors="ignore")
out = []
for kw in ["houseCampSctin", "fn_fsfsRsrvtPssblGoodsList", "goodsClsscCampCdArr"]:
    pos = [m.start() for m in re.finditer(kw, h)]
    out.append("### %s count=%d" % (kw, len(pos)))
    for i in pos[:6]:
        out.append("--- @%d ---" % i)
        out.append(re.sub(r"\s+", " ", h[max(0, i-500):i+500]))
out.append("### FUNCTIONS")
out.append(str(sorted(set(re.findall(r'function\s+(fn_[A-Za-z0-9_]+)', h)))))
out.append("### CAMP-TAB MARKUP")
for m in list(re.finditer(r'name="camp"|id="cmpgr"|야영장', h))[:6]:
    out.append("--- ---")
    out.append(re.sub(r"\s+", " ", h[max(0, m.start()-350):m.start()+350]))
pathlib.Path("out/analyze3.txt").write_text("\n".join(out), encoding="utf-8")
print("saved")
