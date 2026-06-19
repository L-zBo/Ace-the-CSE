param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$packRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $packRoot "../..")
$filesRoot = Join-Path $packRoot "files"

$filesRootResolved = (Resolve-Path $filesRoot).Path
$targets = Get-ChildItem -LiteralPath $filesRoot -Recurse -File | ForEach-Object {
  $_.FullName.Substring($filesRootResolved.Length).TrimStart([char[]]@("\", "/")).Replace("\", "/")
}

foreach ($rel in $targets) {
  $src = Join-Path $filesRoot $rel
  $dst = Join-Path $projectRoot $rel
  if (!(Test-Path -LiteralPath $src)) {
    throw "Missing source file in rescue pack: $rel"
  }
  $dstDir = Split-Path -Parent $dst
  if (!(Test-Path -LiteralPath $dstDir)) {
    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
  }
  if ($DryRun) {
    Write-Host "[dry-run] copy $rel"
  } else {
    Copy-Item -LiteralPath $src -Destination $dst -Force
    Write-Host "copied $rel"
  }
}

Write-Host "Done. Run: python scripts/d17_list_unanswerable.py"
