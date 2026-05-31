@echo off
SET VERSION=1.1.2
cd /d D:\Grinder
echo Building GRINDER installer v%VERSION%...
"D:\Inno Setup 6\ISCC.exe" GRINDER_setup.iss
echo Done.
pause
