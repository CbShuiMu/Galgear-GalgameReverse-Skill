$ErrorActionPreference = 'Stop'
$toolDirectory = Split-Path -Parent $PSScriptRoot
$frameworkDirectory = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319'
$compiler = Join-Path $frameworkDirectory 'csc.exe'
$arguments = @(
    '/nologo'
    ('/out:' + (Join-Path $toolDirectory 'GalArchiveExport.exe'))
    ('/r:' + (Join-Path $toolDirectory 'GameRes.dll'))
    ('/r:' + (Join-Path $toolDirectory 'ArcFormats.dll'))
    '/r:System.Web.Extensions.dll'
)
foreach ($assembly in @('PresentationCore', 'WindowsBase', 'PresentationFramework')) {
    $arguments += '/r:' + (Join-Path $frameworkDirectory ('WPF\' + $assembly + '.dll'))
}
$arguments += Join-Path $PSScriptRoot 'GalArchiveExport.cs'
& $compiler @arguments
if ($LASTEXITCODE -ne 0) { throw 'Archive CLI compilation failed' }
