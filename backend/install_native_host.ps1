param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-p]{32}$')]
    [string]$ExtensionId
)

$ErrorActionPreference = 'Stop'
$hostName = 'dev.andy.authorized_web_archiver'
$launcher = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'launch_host.cmd')).Path
$installDirectory = Join-Path $env:LOCALAPPDATA 'AuthorizedWebArchiver'
$manifestPath = Join-Path $installDirectory 'native-host.json'

New-Item -ItemType Directory -Force -Path $installDirectory | Out-Null
$manifest = [ordered]@{
    name = $hostName
    description = 'Local storage host for the Authorized Web Archiver demo'
    path = $launcher
    type = 'stdio'
    allowed_origins = @("chrome-extension://$ExtensionId/")
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $manifestPath -Encoding utf8NoBOM

$registryPath = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$hostName"
New-Item -Force -Path $registryPath | Out-Null
Set-Item -LiteralPath $registryPath -Value $manifestPath
Write-Output "Registered $hostName for extension $ExtensionId"
