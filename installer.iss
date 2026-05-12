; Desktop Pet — Inno Setup Script
; Builds a proper Windows installer (.exe) with:
;   - Start Menu shortcut
;   - Desktop shortcut (optional)
;   - Startup registry entry (optional)
;   - Uninstaller
;
; Requirements: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Usage: Open this file in Inno Setup Compiler and click Build

#define AppName      "Desktop Pet"
#define AppVersion   "1.0.0"
#define AppPublisher "Your Name"
#define AppExeName   "desktop-pet.exe"
#define DistDir      "dist"

[Setup]
AppId={{8F3A2B1C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL=https://github.com/yourusername/ascii-pet
AppSupportURL=https://github.com/yourusername/ascii-pet/issues
AppUpdatesURL=https://github.com/yourusername/ascii-pet/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=DesktopPet-Setup-{#AppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupentry";   Description: "Start Desktop Pet when Windows starts"; GroupDescription: "Startup"

[Files]
Source: "{#DistDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#DistDir}\*";             DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";   Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run";
    ValueType: string; ValueName: "{#AppName}";
    ValueData: """{app}\{#AppExeName}""";
    Flags: uninsdeletevalue; Tasks: startupentry

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
