# Tag current commit as Version 2.0.0 (run from repo root after reviewing changes).
$ErrorActionPreference = "Stop"
git tag -a v2.0.0 -m "Version 2.0.0 freeze — gateway + web + gui_v2 (see docs/VERSION2_FREEZE.md)"
Write-Host "Created tag v2.0.0. Push with: git push origin v2.0.0"
