# Push Backend to GitHub
# Run this in PowerShell as Administrator

$repoUrl = "https://github.com/cosmofolio23/archportfolio-backend.git"
$backendPath = "E:\Projects\My Product\BUILDING APP\ArchPortfolio_Generator\backend"

Write-Host "Pushing backend to GitHub..." -ForegroundColor Green

# Change to backend directory
cd $backendPath

# Initialize git
git init
git add .
git commit -m "Initial backend commit - FastAPI + Supabase setup"
git branch -M main
git remote add origin $repoUrl
git push -u origin main

Write-Host "`nSuccess! Backend pushed to GitHub" -ForegroundColor Green
Write-Host "Repo URL: $repoUrl" -ForegroundColor Cyan
