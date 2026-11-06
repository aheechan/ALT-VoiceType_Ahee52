; AltVoice Inno Setup script (per-user install).
; Build the app first with packaging/altvoice.spec, then compile this file.

#define MyAppName "ALT-VoiceType_Ahee52"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "ALT-VoiceType contributors"
#define MyAppExeName "AltVoice.exe"

#ifndef SourceDir
#define SourceDir "..\dist\AltVoice"
#endif

[Setup]
AppId={{8E4E3F6A-2B7A-4E1B-9C1A-000000000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ALT-VoiceType_Ahee52
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=ALT-VoiceType_Ahee52-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardImageFile=..\packaging\wizard-large.bmp
WizardSmallImageFile=..\packaging\wizard-small.bmp
SetupIconFile=..\altvoice\assets\icon.ico
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "Start AltVoice when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "AltVoice"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch AltVoice"; Flags: nowait postinstall skipifsilent
