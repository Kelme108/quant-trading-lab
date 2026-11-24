# Instalação completa num Windows novo, a partir de um `git clone` (equivale a ops/linux/install.sh). Na raiz do repositório:
#
#   ops\windows\install.cmd                 # tudo: fim de linha, Python, .venv + testes, live\.venv, MT5 da Clear e normal
#   ops\windows\install.cmd -SemTestes      # pula a suíte de sanidade
#   ops\windows\install.cmd -SemMT5         # não baixa nem instala os terminais MetaTrader 5
#   ops\windows\install.cmd -Claude         # instala também o CLI do Claude Code (esteira e pipeline de agentes)
#
# (install.cmd só chama este arquivo com -ExecutionPolicy Bypass, para não precisar mudar a política do PowerShell.)
#
# O que este script NUNCA faz: digitar senha de corretora, logar em conta, ligar robô, criar tarefa agendada, ligar a
# esteira ou mexer em gates/splits. As tarefas agendadas têm instaladores próprios (ops\windows\install-*-task.ps1),
# rodados pelo dono. Guia: docs\cerebro\Como-rodar-em-outro-ambiente.md
param([switch]$SemTestes, [switch]$SemMT5, [switch]$Claude)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
function Say($m) { Write-Host ""; Write-Host "==> $m" -ForegroundColor Cyan }
function Has($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# ---------------------------------------------------------------------------------------------- fim de linha
# O hash de identidade de cada regra (b3/strategy.py, b3/markets.py, b3/freqtrade_adapter.py) é calculado sobre os BYTES
# do arquivo-fonte, e os ledgers foram gravados com o checkout CRLF do Git para Windows (core.autocrlf=true, o padrão do
# instalador do Git). Com autocrlf=false o checkout sai LF e toda regra muda de hash.
Say "Fim de linha (core.autocrlf=true, para os hashes das regras baterem com os ledgers)"
if (-not (Has git)) { throw "git não encontrado. Instale o Git para Windows (https://git-scm.com/download/win) e rode de novo." }
$crlf = (git -C $Root config core.autocrlf) 2>$null
if ($crlf -ne 'true') {
    $dirty = git -C $Root status --porcelain --untracked-files=no
    if ($dirty) {
        throw "O clone tem arquivos alterados; não vou refazer o checkout por cima deles. Faça commit/stash, ou clone de novo com: git clone -c core.autocrlf=true <url>"
    }
    git -C $Root config core.autocrlf true
    git -C $Root rm -rq --cached .
    git -C $Root reset -q --hard
    Write-Host "ok: checkout refeito com CRLF"
} else { Write-Host "ok (já era true)" }

# ---------------------------------------------------------------------------------------------- Python
Say "Python 3.13 ou mais novo"
function Find-Python {
    $cands = @()
    if (Has py) { $cands += ,@('py', '-3.14'); $cands += ,@('py', '-3.13') }
    if (Test-Path 'C:\Python314\python.exe') { $cands += ,@('C:\Python314\python.exe') }
    $cands += ,@("$env:LOCALAPPDATA\Programs\Python\Python314\python.exe")
    $cands += ,@("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe")
    if (Has python) { $cands += ,@('python') }
    foreach ($c in $cands) {
        $exe = $c[0]; $extra = @(); if ($c.Count -gt 1) { $extra = $c[1..($c.Count - 1)] }
        if (($exe -like '*\*') -and -not (Test-Path $exe)) { continue }
        try {
            & $exe @extra -c "import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) { return ,@($exe) + $extra }
        } catch { }
    }
    return $null
}
$py = Find-Python
if (-not $py) {
    if (-not (Has winget)) { throw "Python >= 3.13 não encontrado e sem winget. Instale o Python 3.14 de https://www.python.org/downloads/windows/ e rode de novo." }
    Write-Host "Instalando o Python 3.14 pelo winget (pode pedir confirmação)"
    winget install -e --id Python.Python.3.14 --scope user --accept-package-agreements --accept-source-agreements
    $py = Find-Python
    if (-not $py) { throw "O Python foi instalado, mas este terminal ainda não o enxerga. Feche, abra outro e rode de novo." }
}
$pyExe = $py[0]; $pyArgs = @(); if ($py.Count -gt 1) { $pyArgs = $py[1..($py.Count - 1)] }
Write-Host ("Usando: " + ($py -join ' ') + "  (" + (& $pyExe @pyArgs --version) + ")")

# ---------------------------------------------------------------------------------------------- .venv (pesquisa, portal)
Say ".venv da raiz (pesquisa, esteira, portal, testes)"
$bargs = @('bootstrap.py', '--research'); if (-not $SemTestes) { $bargs += '--test' }
& $pyExe @pyArgs @bargs
$testFail = ($LASTEXITCODE -ne 0)
if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) { throw "Falha ao criar o .venv (veja acima)." }

# ---------------------------------------------------------------------------------------------- live\.venv (robôs)
Say "live\.venv (robôs e dados da B3: pacote MetaTrader5)"
if (-not (Test-Path "$Root\live\.venv\Scripts\python.exe")) { & $pyExe @pyArgs -m venv "$Root\live\.venv" }
& "$Root\live\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r "$Root\live\requirements.txt"
& "$Root\live\.venv\Scripts\python.exe" -c "import MetaTrader5, numpy, pandas, zoneinfo; zoneinfo.ZoneInfo('America/Sao_Paulo'); print('ok  live\.venv:', MetaTrader5.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)"

# ---------------------------------------------------------------------------------------------- MT5
if (-not $SemMT5) {
    Say "MetaTrader 5 da Clear e MT5 normal"
    $dl = "$Root\ops\windows\downloads"; New-Item -ItemType Directory -Force $dl | Out-Null
    $terms = @(
        @{ Name = 'Clear'; Url = 'https://download.mql5.com/cdn/web/xp.investimentos.cctvm/mt5/clearinvestimentos5setup.exe';
           File = 'clearinvestimentos5setup.exe'; Exe = 'C:\Program Files\Clear Investimentos MT5 Terminal\terminal64.exe' },
        @{ Name = 'normal (MetaQuotes)'; Url = 'https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe';
           File = 'mt5setup.exe'; Exe = 'C:\Program Files\MetaTrader 5\terminal64.exe' }
    )
    foreach ($t in $terms) {
        if (Test-Path $t.Exe) { Write-Host "ok  MT5 $($t.Name): $($t.Exe)"; continue }
        $f = Join-Path $dl $t.File
        if (-not (Test-Path $f)) {
            Write-Host "  baixando $($t.File)"
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $t.Url -OutFile $f -UseBasicParsing
        }
        $sig = Get-AuthenticodeSignature $f
        if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'MetaQuotes') {
            Remove-Item -LiteralPath $f -Force
            throw "$($t.File): assinatura inválida ou não é da MetaQuotes ($($sig.Status)). Apaguei o arquivo; rode de novo."
        }
        Write-Host "  assinatura ok (MetaQuotes). Instalando MT5 $($t.Name) (o instalador baixa o terminal; leva alguns minutos)"
        Start-Process -FilePath $f -ArgumentList '/auto' -Wait
        if (Test-Path $t.Exe) { Write-Host "ok  MT5 $($t.Name): $($t.Exe)" }
        else { Write-Warning "MT5 $($t.Name) não apareceu em $($t.Exe). Rode o instalador à mão: $f" }
    }
}

# ---------------------------------------------------------------------------------------------- Claude Code (opcional)
if ($Claude) {
    Say "Claude Code (CLI dos agentes)"
    if (Has claude) { Write-Host "claude já instalado" }
    else { Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression; Write-Host "Depois rode 'claude' uma vez para entrar na sua conta." }
}

Say "Fim"
& "$Root\.venv\Scripts\python.exe" bootstrap.py --check
if ($testFail) { Write-Warning "Houve falha na suíte de sanidade; leia a saída antes de ligar qualquer robô." }
Write-Host @"

Próximos passos:
  1. Abrir o MT5 da Clear e entrar na conta DEMO (servidor ClearInvestimentos-DEMO, marcar 'salvar senha').
  2. Portal:                 .venv\Scripts\python -m lab.dashboard serve --open      (http://127.0.0.1:8765)
  3. Ligar um robô de demo:  ops\windows\demo-b3.cmd demo-b3-p032-win
  4. Baixar histórico:       live\.venv\Scripts\python -m b3.data.mt5_history download --attach b3\config\broker_mt5.json --symbols WIN`$N WDO`$N --timeframes M1 M5 M15
"@
