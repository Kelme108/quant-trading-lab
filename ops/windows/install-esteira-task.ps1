# Creates the Windows task "TradeInitial-EsteiraCycle": one conveyor cycle (ops\windows\esteira-cycle.cmd) every
# hour for 28 days, waking the PC from sleep. Run by the owner (the assistant may not create scheduled tasks).
# Remove: Unregister-ScheduledTask -TaskName TradeInitial-EsteiraCycle -Confirm:$false
# Pause without removing: create ops\state\STOP_ESTEIRA
$a  = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c D:\Trade-Initial\ops\windows\esteira-cycle.cmd'
$tr = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 28)
$s  = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -StartWhenAvailable -WakeToRun
$p  = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'TradeInitial-EsteiraCycle' -Action $a -Trigger $tr -Settings $s -Principal $p -Force | Out-Null
Get-ScheduledTask TradeInitial-EsteiraCycle | Get-ScheduledTaskInfo | Format-List TaskName, NextRunTime
