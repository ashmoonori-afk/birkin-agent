param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
)

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$SrcDir = Join-Path $RootDir "src"

if ($env:PYTHONPATH) {
  $env:PYTHONPATH = "$SrcDir;$env:PYTHONPATH"
} else {
  $env:PYTHONPATH = $SrcDir
}

py -m birkin_agent @RemainingArgs
exit $LASTEXITCODE
