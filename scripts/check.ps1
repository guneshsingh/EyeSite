# EyeSite quality check script for Windows (PowerShell)
# Runs pytest then ruff

Write-Host "=== Running pytest ===" -ForegroundColor Cyan
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=== Running ruff check ===" -ForegroundColor Cyan
ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ruff check failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[SUCCESS] All checks passed!" -ForegroundColor Green
exit 0
