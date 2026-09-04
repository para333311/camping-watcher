Set-Location $PSScriptRoot
Set-Content -Path guard.pid -Value $PID
$next = Get-Date
while ($true) {
  try {
    if ((Get-Content guard.pid -ErrorAction SilentlyContinue) -ne "$PID") { exit }
    if ((Get-Date) -ge $next) {
      $w = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*watch.py*' }
        # watch.py 는 07시 전에는 10분씩 자며 로그를 안 쓴다(야간 휴식).
      # 그걸 모르고 "25분 무응답 = 죽음" 으로 보다가, 밤새 15분마다 죽였다 켜기를
      # 반복했다. 재시작할 때마다 "감시 시작" 알림이 나가 2026-08-24 새벽에만
      # 수십 건이 쌓였다. 야간에는 재시작 판정에서 로그 신선도를 빼고
      # 프로세스 생존만 본다.
      $night = (Get-Date).Hour -lt 7
      $ws = (-not $night) -and (Test-Path watch.log) -and (((Get-Date) - (Get-Item watch.log).LastWriteTime).TotalMinutes -gt 25)
      if ((-not $w) -or $ws) {
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*watch.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object { $_.CommandLine -like '*run.bat*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        Start-Sleep 3
        Start-Process cmd -WindowStyle Hidden -ArgumentList '/c','run.bat'
        Add-Content guard.log ((Get-Date -Format 'MM-dd HH:mm:ss') + " watch start")
        $next = (Get-Date).AddMinutes(15)
      }
      $l = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*local.py*' }
      $ls = (Test-Path local.log) -and (((Get-Date) - (Get-Item local.log).LastWriteTime).TotalMinutes -gt 25)
      if ((-not $l) -or $ls) {
        Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*local.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        Start-Sleep 3
        Start-Process -WindowStyle Hidden -FilePath ".\.venv\Scripts\python.exe" -ArgumentList 'local.py'
        Add-Content guard.log ((Get-Date -Format 'MM-dd HH:mm:ss') + " local start")
        $next = (Get-Date).AddMinutes(15)
      }
    }
  } catch {}
  Start-Sleep 60
}