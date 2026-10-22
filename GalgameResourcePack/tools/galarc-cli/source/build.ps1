$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw '.NET Framework C# compiler is required.' }
$sourceRoot = $PSScriptRoot
$outputFile = Join-Path (Split-Path -Parent $sourceRoot) 'galarc.exe'
$sourceFiles = Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Filter '*.cs' | Select-Object -ExpandProperty FullName
& $compiler /nologo /target:exe /platform:anycpu /optimize+ /debug- /utf8output /reference:System.Web.Extensions.dll "/out:$outputFile" $sourceFiles
if ($LASTEXITCODE -ne 0) { throw "C# compiler exited with $LASTEXITCODE" }
