# Creates the weekday 08:40 start tasks for the demo robots added on 2026-11-18 night (owner: "agora e com vc, deixe
# tudo ligado... teste tudo, stop loss, take profit, novas estrategias"): P-032 (the P-026 study pick) and five conveyor
# families with exit-menu exits. Each is a copy of the P-029 task with its own config. Run by the owner (the assistant
# may not create scheduled tasks).
$t = Get-ScheduledTask TradeInitial-DemoB3-P029
$robots = @(
    @('TradeInitial-DemoB3-P032', 'demo-b3-p032-win'),
    @('TradeInitial-DemoB3-E156', 'demo-b3-e156-win'),
    @('TradeInitial-DemoB3-E118', 'demo-b3-e118-win'),
    @('TradeInitial-DemoB3-E040', 'demo-b3-e040-win'),
    @('TradeInitial-DemoB3-E102', 'demo-b3-e102-win'),
    @('TradeInitial-DemoB3-E062', 'demo-b3-e062-win'),
    @('TradeInitial-DemoB3-E209', 'demo-b3-e209-win'),
    @('TradeInitial-DemoB3-E164', 'demo-b3-e164-win'),
    @('TradeInitial-DemoB3-E193', 'demo-b3-e193-win'),
    @('TradeInitial-DemoB3-E160', 'demo-b3-e160-win'),
    @('TradeInitial-DemoB3-E225', 'demo-b3-e225-win'),
    @('TradeInitial-DemoB3-E217', 'demo-b3-e217-win')
)
foreach ($pair in $robots) {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -Command `"Start-Process -WindowStyle Hidden -Wait -FilePath cmd.exe -ArgumentList '/c $PSScriptRoot\demo-b3.cmd $($pair[1])'`""
    Register-ScheduledTask -TaskName $pair[0] -Action $a -Trigger $t.Triggers -Settings $t.Settings -Principal $t.Principal -Force | Out-Null
    Get-ScheduledTask $pair[0] | Get-ScheduledTaskInfo | Format-List TaskName, NextRunTime
}
