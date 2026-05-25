Set WShell = CreateObject("WScript.Shell")
WShell.Run "cmd /c D:\Grinder\run_GRINDER.bat", 0, False
Set WShell = Nothing
