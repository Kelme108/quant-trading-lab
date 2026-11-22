# Creates the weekday 08:40 start tasks for the demo robots added on 2026-11-18 (owner): P-030 on WIN (replaces P-004
# on WDO) and P-026 on WDO. Each is a copy of the P-029 task with its own config. Run by the owner (the assistant may
# not create scheduled tasks).
$t = Get-ScheduledTask TradeInitial-DemoB3-P029
foreach ($pair in @(@('TradeInitial-DemoB3-P030', 'demo-b3-p030-win'), @('TradeInitial-DemoB3-P026-WDO', 'demo-b3-p026-wdo'))) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -WindowStyle Hidden -Wait -FilePath cmd.exe -ArgumentList '/c $PSScriptRoot\demo-b3.cmd $($pair[1])'`""
    Register-ScheduledTask -TaskName $pair[0] -Action $a -Trigger $t.Triggers -Settings $t.Settings -Principal $t.Principal -Force | Out-Null
    Get-ScheduledTask $pair[0] | Get-ScheduledTaskInfo | Format-List TaskName, NextRunTime
}
