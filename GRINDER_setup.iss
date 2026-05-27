[Setup]
AppName=GRINDER
AppVersion=1.0.1
AppPublisher=dougbills327
DefaultDirName=D:\Grinder_1.0.1
DefaultGroupName=GRINDER
OutputDir=installer_output
OutputBaseFilename=GRINDER_setup_v1.0.1
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\Grinder\GRINDER.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Grinder\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Grinder\run_GRINDER.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Grinder\run_GRINDER.vbs"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\Grinder\merida\*"; DestDir: "{app}\merida"; Flags: ignoreversion recursesubdirs
Source: "D:\Grinder\sounds\*"; DestDir: "{app}\sounds"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\GRINDER"; Filename: "{app}\run_GRINDER.vbs"
Name: "{autodesktop}\GRINDER"; Filename: "{app}\run_GRINDER.vbs"; Tasks: desktopicon

[Run]
Filename: "{app}\run_GRINDER.vbs"; Description: "{cm:LaunchProgram,GRINDER}"; Flags: nowait postinstall skipifsilent
