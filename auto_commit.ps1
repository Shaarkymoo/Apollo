# auto_commit.ps1
git add .
git commit -m "Auto-commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git push origin main
