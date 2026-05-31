@echo off
SET VERSION=1.1.2
cd /d D:\Grinder
git add -A
git commit -m "GRINDER v%VERSION%"
git push origin main
echo Pushed v%VERSION% to GitHub.
pause
