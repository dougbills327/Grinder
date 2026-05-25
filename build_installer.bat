@echo off
SET VERSION=0.0.1
cd /d D:\Grinder
echo Building GRINDER installer v%VERSION%...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GRINDER_setup.iss
echo Done.
pause
