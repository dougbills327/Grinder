@echo off
SET VERSION=0.0.1
cd /d D:\Grinder
git add -A
git commit -m "GRINDER v%VERSION%"
git push origin main
echo Pushed v%VERSION% to GitHub.
pause
