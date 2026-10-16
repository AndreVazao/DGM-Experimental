# Installs the packaged back-office and dashboard for all Windows users.
# Run this script deliberately; it requests UAC elevation because it writes under Program Files,
# the machine environment, the common Startup folder and the Public Desktop.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $scriptPath = $MyInvocation.MyCommand.Path
    $quotedScript = '"' + $scriptPath + '"'
    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File $quotedScript"
    exit
}

$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceEngine = Join-Path $packageRoot "engine"
$sourceDashboard = Join-Path $packageRoot "dashboard"
$exeName = "DGM-MAT-BackOffice.exe"
if (-not (Test-Path (Join-Path $sourceEngine $exeName))) { throw "Package missing engine/DGM-MAT-BackOffice.exe." }
foreach ($file in @("index.html", "app.js", "styles.css")) {
    if (-not (Test-Path (Join-Path $sourceDashboard $file))) { throw "Package missing dashboard/$file." }
}

$installRoot = Join-Path $env:ProgramFiles "DGM-MAT"
$engineRoot = Join-Path $installRoot "engine"
$dashboardRoot = Join-Path $installRoot "dashboard"
$startupFolder = [Environment]::GetFolderPath("CommonStartup")
$publicDesktop = [Environment]::GetFolderPath("CommonDesktopDirectory")
New-Item -ItemType Directory -Force -Path $installRoot, $engineRoot, $dashboardRoot | Out-Null

# Preserve the currently installed binaries before replacing them; user data is never removed.
$backupRoot = Join-Path $installRoot ("backups/pre-update-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$existingFiles = Get-ChildItem $engineRoot -Force -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingFiles) {
    New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    Copy-Item (Join-Path $engineRoot "*") $backupRoot -Recurse -Force
}
Copy-Item (Join-Path $sourceEngine "*") $engineRoot -Recurse -Force
Copy-Item (Join-Path $sourceDashboard "*") $dashboardRoot -Recurse -Force

[Environment]::SetEnvironmentVariable("DGM_MOBILE_UI_PATH", $dashboardRoot, "Machine")
$env:DGM_MOBILE_UI_PATH = $dashboardRoot

# Hidden launcher checks health first, preventing duplicate back-office processes at later logons.
$vbsPath = Join-Path $installRoot "Start-BackOffice-Hidden.vbs"
$vbs = @'
On Error Resume Next
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
http.setTimeouts 1000, 1000, 1000, 1000
http.Open "GET", "http://127.0.0.1:8181/health", False
http.Send
If Err.Number = 0 Then
  If http.Status = 200 Then WScript.Quit 0
End If
Err.Clear
shell.CurrentDirectory = base & "\engine"
shell.Run """" & base & "\engine\DGM-MAT-BackOffice.exe"" --headless --profile HEADLESS", 0, False
'@
Set-Content -Path $vbsPath -Value $vbs -Encoding ascii

$wscript = Join-Path $env:SystemRoot "System32/wscript.exe"
$startupShortcut = Join-Path $startupFolder "DGM-MAT Back-office.lnk"
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startupShortcut)
$shortcut.TargetPath = $wscript
$shortcut.Arguments = '"' + $vbsPath + '"'
$shortcut.WorkingDirectory = $installRoot
$shortcut.Description = "Arranca o back-office DGM-MAT em segundo plano ao iniciar sessão."
$shortcut.WindowStyle = 7
$shortcut.Save()

$dashboardUrl = Join-Path $publicDesktop "DGM-MAT Dashboard.url"
@("[InternetShortcut]", "URL=http://127.0.0.1:8181/app/", "IconFile=$env:SystemRoot\System32\shell32.dll", "IconIndex=220") |
    Set-Content -Path $dashboardUrl -Encoding ascii

Write-Host "Instalação preparada."
Write-Host "Back-office: $engineRoot/$exeName"
Write-Host "Arranque: pasta Startup comum (qualquer utilizador que inicie sessão)."
Write-Host "Dashboard: atalho no Ambiente de Trabalho Público; abre apenas quando clicado."
Write-Host "API local esperada: http://127.0.0.1:8181/health"
Write-Host "Nota: o pacote ainda requer validação no PC real antes de ser considerado operacional."
