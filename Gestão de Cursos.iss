; Instalador para o Gestão de Cursos

#define AppVersion Trim(FileRead(FileOpen("version.txt")))
#define BuildDir "build\exe.win-amd64-3.13"

[Setup]
; Informações básicas do aplicativo
AppName=Gestão de Cursos
AppVersion={#AppVersion}
AppPublisher=Gestor Cursos
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=
DefaultDirName={autopf}\Gestao de Cursos
DefaultGroupName=Gestão de Cursos
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=GestaoDeCursos_Setup
SetupIconFile=crc.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

UsePreviousAppDir=yes
DisableProgramGroupPage=yes

CloseApplications=yes
CloseApplicationsFilter=Gestão De Cursos.exe
RestartApplications=no

; Informações de novidades da versão
InfoBeforeFile=novidades_v1.2.1.txt

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Ícones adicionais:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Criar ícone na Barra de Inicialização Rápida"; GroupDescription: "Ícones adicionais:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Executável principal
Source: "build\exe.win-amd64-3.13\Gestão De Cursos.exe"; DestDir: "{app}"; Flags: ignoreversion

; Todos os arquivos e pastas da build
Source: "build\exe.win-amd64-3.13\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; NOTA: Ajuste "exe.win-amd64-3.12" para o nome correto da sua pasta de build
; Se estiver usando Python 3.11, será "exe.win-amd64-3.11", etc.

[Icons]
; Ícone no Menu Iniciar
Name: "{group}\Gestão de Cursos"; Filename: "{app}\Gestão De Cursos.exe"; IconFilename: "{app}\crc.ico"
Name: "{group}\Desinstalar Gestão de Cursos"; Filename: "{uninstallexe}"

; Ícone na Área de Trabalho
Name: "{autodesktop}\Gestão de Cursos"; Filename: "{app}\Gestão De Cursos.exe"; IconFilename: "{app}\crc.ico"; Tasks: desktopicon

; Ícone na Barra de Inicialização Rápida
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Gestão de Cursos"; Filename: "{app}\Gestão De Cursos.exe"; IconFilename: "{app}\crc.ico"; Tasks: quicklaunchicon

[Run]
; Executar o programa após a instalação
Filename: "{app}\Gestão De Cursos.exe"; Description: "Executar Gestão de Cursos"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Deletar banco de dados e arquivos gerados (opcional - remova se quiser manter os dados do usuário)
Type: files; Name: "{app}\*.db"
Type: files; Name: "{app}\*.log"