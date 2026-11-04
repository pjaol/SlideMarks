# SlideMarks for Windows: installs the font, and the Office add-in for Word and PowerPoint.
#
#   Install (PowerShell):    irm {{BASE_URL}}/install.ps1 | iex
#   Uninstall (PowerShell):  & ([scriptblock]::Create((irm {{BASE_URL}}/install.ps1))) -Uninstall
#
# Everything is installed for the current user only, so no administrator rights are needed:
#   the font:      %LOCALAPPDATA%\Microsoft\Windows\Fonts\SlideMarks-Regular.ttf (registered under HKCU)
#   the manifest:  %LOCALAPPDATA%\SlideMarks\manifest.xml, registered with Office under
#                  HKCU\Software\Microsoft\Office\16.0\WEF\Developer, the same way Microsoft's
#                  office-addin-dev-settings tool sideloads add-ins.
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$BaseUrl = '{{BASE_URL}}'
$AddinId = '{{ADDIN_ID}}'
$Dir = Join-Path $env:LOCALAPPDATA 'SlideMarks'
$Manifest = Join-Path $Dir 'manifest.xml'
$Font = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts\SlideMarks-Regular.ttf'
$FontKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$FontName = 'SlideMarks Regular (TrueType)'
$WefKey = 'HKCU:\Software\Microsoft\Office\16.0\WEF\Developer'

# Office keeps the font file open, so it can't be replaced or removed while Word or PowerPoint runs.
$running = Get-Process -Name WINWORD, POWERPNT -ErrorAction SilentlyContinue
if ($running) {
    Write-Host 'Please close Word and PowerPoint (save your work first), then run this again.' -ForegroundColor Yellow
    return
}

if ($Uninstall) {
    if (Get-ItemProperty -Path $WefKey -Name $AddinId -ErrorAction Ignore) { Remove-ItemProperty -Path $WefKey -Name $AddinId }
    if (Get-ItemProperty -Path $FontKey -Name $FontName -ErrorAction Ignore) { Remove-ItemProperty -Path $FontKey -Name $FontName }
    foreach ($path in $Font, $Dir) { if (Test-Path $path) { Remove-Item -Path $path -Recurse -Force } }
    Write-Host 'SlideMarks removed.'
    return
}

Write-Host "Downloading SlideMarks from $BaseUrl"
New-Item -ItemType Directory -Force -Path $Dir, (Split-Path $Font) | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/download/SlideMarks-Regular.ttf" -OutFile $Font
# Never New-Item -Force on a registry key that exists: it would replace the key and drop its other values.
if (-not (Test-Path $FontKey)) { New-Item -Path $FontKey | Out-Null }
New-ItemProperty -Path $FontKey -Name $FontName -Value $Font -PropertyType String -Force | Out-Null
Write-Host 'Font installed' -ForegroundColor Green

Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/office/manifest.xml" -OutFile $Manifest
if (-not (Test-Path $WefKey)) { New-Item -Path $WefKey -Force | Out-Null }  # -Force creates missing parents here
New-ItemProperty -Path $WefKey -Name $AddinId -Value $Manifest -PropertyType String -Force | Out-Null
Write-Host 'Add-in added to Word and PowerPoint' -ForegroundColor Green

Write-Host ''
Write-Host 'Next: open Word or PowerPoint, click Add-ins on the Home tab, then SlideMarks.'
