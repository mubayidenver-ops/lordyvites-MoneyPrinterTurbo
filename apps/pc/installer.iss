[Setup]
AppId={{8F967711-69E9-4B85-865B-893A9972CE04}
AppName=Lordyvites Money Printer Turbo
AppVersion=0.1.0
AppPublisher=Lordyvites
AppPublisherURL=https://github.com/mubayidenver-ops/lordyvites-MoneyPrinterTurbo
DefaultDirName={localappdata}\Programs\Lordyvites Money Printer Turbo
DefaultGroupName=Lordyvites Money Printer Turbo
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist
OutputBaseFilename=Lordyvites-Money-Printer-Turbo-Windows-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\python\pythonw.exe
LicenseFile=..\..\LICENSE
DiskSpanning=no

[Files]
Source: "..\..\build\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lordyvites Money Printer Turbo"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\backend\apps\pc\launcher.pyw"""; WorkingDir: "{app}\backend"
Name: "{autodesktop}\Lordyvites Money Printer Turbo"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\backend\apps\pc\launcher.pyw"""; WorkingDir: "{app}\backend"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\backend\apps\pc\launcher.pyw"""; WorkingDir: "{app}\backend"; Description: "Open Lordyvites"; Flags: nowait postinstall skipifsilent
