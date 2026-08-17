[Setup]
AppName=RN Scanner and Digital Print House
AppVersion=1.0.1
DefaultDirName={autopf}\K_Dynamics_System
DefaultGroupName=RN Scanner
OutputDir=Output
OutputBaseFilename=K_Dynamics_System_Setup_v1.0.1
SetupIconFile=assets\k_dynamics_logo.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\K_Dynamics_System.exe
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\K_Dynamics_System\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\RN Scanner"; Filename: "{app}\K_Dynamics_System.exe"
Name: "{group}\{cm:UninstallProgram,RN Scanner}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\RN Scanner"; Filename: "{app}\K_Dynamics_System.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\K_Dynamics_System.exe"; Description: "{cm:LaunchProgram,RN Scanner}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // We intentionally DO NOT delete the LocalAppData folder here to protect user data.
    // The user's database and logs remain safely in %LOCALAPPDATA%\K_Dynamics_System.
    Log('Uninstallation finished. User data in LocalAppData was kept intentionally.');
  end;
end;
