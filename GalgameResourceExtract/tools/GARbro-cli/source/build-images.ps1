$ErrorActionPreference = 'Stop'
$toolDirectory = Split-Path -Parent $PSScriptRoot
$frameworkDirectory = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319'
$compiler = Join-Path $frameworkDirectory 'csc.exe'
$arguments = @('/nologo','/warn:0',('/out:' + (Join-Path $toolDirectory 'GalImageExport.exe')),
    ('/r:' + (Join-Path $toolDirectory 'GameRes.dll')), '/r:System.Web.Extensions.dll')
foreach ($assembly in @('PresentationCore','WindowsBase','PresentationFramework')) {
    $arguments += '/r:' + (Join-Path $frameworkDirectory ('WPF\' + $assembly + '.dll'))
}
$arguments += Join-Path $PSScriptRoot 'GalImageExport.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw 'Image CLI compilation failed' }
Copy-Item -LiteralPath (Join-Path $toolDirectory 'GARbro.Console.exe.config') -Destination (Join-Path $toolDirectory 'GalImageExport.exe.config') -Force
