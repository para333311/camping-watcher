#!/bin/bash
# 캠핑 감시 — 맥 상주 등록 (2026-09-23, 윈도 guard.ps1·guard.vbs·run.bat 대체)
#   bash ~/camping-watcher/install-mac.sh          # 등록·기동 (여러 번 쳐도 안전)
#   bash ~/camping-watcher/install-mac.sh --off    # 둘 다 끄기
#
# 두 감시를 launchd 에이전트로 띄운다. KeepAlive 가 guard.ps1 의 "죽으면 되살림" 을 한다.
# guard 가 하던 "로그가 25분 안 바뀌면 죽인다" 는 안 옮겼다 — watch.py 는 07시 전 10분씩 자서
# 로그가 안 바뀌는 게 정상이고, 그 오판으로 2026-08-24 새벽에 「감시 시작」 알림 수십 건이 쌓였다.
# 이제는 프로세스 생사만 본다. ThrottleInterval 300 — 시작하자마자 죽는 고장이 나도
# 「감시 시작」 알림이 5분에 한 통을 넘지 않게.
# paracano 리포와 섞지 않는다(기획 paracano/기획/20260922-캠핑감시-맥-이사.md): 자기 리포·자기 launchd.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
PY="$D/.venv/bin/python"
AG="$HOME/Library/LaunchAgents"

if [ "${1:-}" = "--off" ]; then
  for n in watch local; do launchctl unload "$AG/kr.paracano.camping.$n.plist" 2>/dev/null; done
  echo "캠핑 감시 둘 다 껐다"; exit 0
fi

[ -f "$D/.env" ] || { echo "✋ $D/.env 가 없다 — paracano 비밀값 꾸러미를 먼저 풀어라"; exit 1; }
if [ ! -x "$PY" ]; then
  echo "가상환경 만든다…"
  /opt/homebrew/bin/python3 -m venv "$D/.venv" && "$PY" -m pip install -q playwright==1.63.0 && "$D/.venv/bin/playwright" install chromium
fi
mkdir -p "$AG"

for n in watch local; do
  P="$AG/kr.paracano.camping.$n.plist"
  cat > "$P" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>kr.paracano.camping.$n</string>
<key>ProgramArguments</key><array><string>$PY</string><string>$D/$n.py</string></array>
<key>WorkingDirectory</key><string>$D</string>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string><key>PYTHONUNBUFFERED</key><string>1</string></dict>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><true/>
<key>ThrottleInterval</key><integer>300</integer>
<key>StandardOutPath</key><string>$D/$n.out.log</string>
<key>StandardErrorPath</key><string>$D/$n.err.log</string>
</dict></plist>
EOF
  launchctl unload "$P" 2>/dev/null
  launchctl load "$P" && echo "✓ kr.paracano.camping.$n"
done
