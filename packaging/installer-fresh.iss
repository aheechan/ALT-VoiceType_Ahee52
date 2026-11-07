; ALT-VoiceType full offline installer with the five-model / four-tier set.
; Build the app first, then compile with the ModelsDir define pointing at the
; installed model directory. DiskSpanning splits the output into <2 GB slices
; so the files can be uploaded to GitHub Releases individually.

#define MyAppName "ALT-VoiceType"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "ALT-VoiceType contributors"
#define MyAppExeName "ALT-VoiceType.exe"

#ifndef SourceDir
#define SourceDir "..\dist\ALT-VoiceType"
#endif
#ifndef ModelsDir
#define ModelsDir "C:\Users\72157\AppData\Local\ALT-VoiceType\models"
#endif

[Setup]
AppId={{8E4E3F6A-2B7A-4E1B-9C1A-000000000003}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ALT-VoiceType
DefaultGroupName={#MyAppName}
DisableDirPage=no
UsePreviousAppDir=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer2
OutputBaseFilename=ALT-VoiceType-Setup-{#MyAppVersion}
Compression=lzma2/fast
SolidCompression=no
DiskSpanning=yes
DiskSliceSize=1900000000
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
Name: "autostart"; Description: "Start ALT-VoiceType when I sign in"; GroupDescription: "Startup:"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#ModelsDir}\qwen3_asr_0_6b\*"; DestDir: "{app}\models\qwen3_asr_0_6b"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#ModelsDir}\qwen3_1_7b_abliterated_q4\*"; DestDir: "{app}\models\qwen3_1_7b_abliterated_q4"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{#ModelsDir}\index_translate_2b_q4\*"; DestDir: "{app}\models\index_translate_2b_q4"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ALT-VoiceType"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ALT-VoiceType"; Flags: nowait postinstall skipifsilent

