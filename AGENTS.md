# GestorCursos — Contexto para Agentes

## Projeto
Sistema de gestão de cursos e instrutores com envio de e-mails.

## Stack
- Python 3.13 + PyQt5 (interface desktop)
- SQLite (banco local, network path: `\\srvsql\Banco Cursos\instrutores.db`)
- reportlab (geração de PDF)
- cx_Freeze (empacotamento .exe)
- Inno Setup (instalador)

## Entry Points
- `main.py` → `MainWindow` (janela principal)
- `setup.py` → build com cx_Freeze
- `Gestão de Cursos.iss` → instalador Inno Setup

## Estrutura
| Arquivo | Função |
|---|---|
| `main.py` | Tudo: MainWindow, DetalhesProgramacaoWindow, ConfigEmailWindow, EmailEditor, SendEmailThread, auto-update |
| `dialog_windows.py` | CadastroInstrutorWindow, EditarInstrutorWindow, CadastroCursoWindow, AssociarCursoWindow, ExcluirInstrutorWindow |
| `database_utils.py` | Conexão e migrações do banco |

## Atualização Automática
- `version.txt` na raiz → versão atual
- `verificar_atualizacao()` em `main.py` → check no startup
- Busca `version.txt` no raw.githubusercontent.com
- Compara com `packaging.version.Version`
- Se nova → baixa asset `GestaoDeCursos_Setup*` do Latest Release
- Executa instalador com `ShellExecuteW(runas)` e sai

## Config de E-mail
- SMTP: ConfigEmailWindow em main.py
- Editor HTML 3 seções (cabeçalho/corpo/rodapé)
- Templates salvos no banco (`email_templates`)
- Imagens CID, botões, variáveis: `{{nome_curso}}`, `{{data_curso}}`, `{{hora_curso}}`, `{{nome_instrutor}}`, `{{carga_horaria}}`, `{{tema_curso}}`

## Database
- Network: `\\srvsql\Banco Cursos\instrutores.db`
- Tabela de templates: `email_templates` (corpo_cabecario, corpo_principal, corpo_rodape)
- Funções: `criar_banco()`, `atualizar_banco()` em database_utils.py
