import re, pathlib
h = pathlib.Path("out/result.html").read_text(encoding="utf-8", errors="ignore")
out = []
idxs = [m.start() for m in re.finditer(r'class="[^"]*rc_item[^"]*"', h)]
out.append("RCITEM %d" % len(idxs))
for i in idxs[:2]:
    s = h.rfind("<", 0, i)
    out.append("=====ITEM=====")
    out.append(re.sub(r"\s+", " ", h[s:s+3000]))
for m in list(re.finditer("예약가능", h))[:2]:
    out.append("=====AVAIL=====")
    out.append(re.sub(r"\s+", " ", h[max(0, m.start()-700):m.start()+300]))
for kw in ["houseCampSctin", "rsrvtPssblYn", "ut_roomcount"]:
    for i in [m.start() for m in re.finditer(kw, h)][:2]:
        out.append("=====%s=====" % kw)
        out.append(re.sub(r"\s+", " ", h[max(0, i-400):i+400]))
pathlib.Path("out/analyze2.txt").write_text("\n".join(out), encoding="utf-8")
print("saved")
