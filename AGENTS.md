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

## Estrutura de Arquivos
| Arquivo | Função |
|---|---|
| `main.py` | Tudo: MainWindow, DetalhesProgramacaoWindow, ConfigEmailWindow, EmailEditor, SendEmailThread, auto-update |
| `dialog_windows.py` | CadastroInstrutorWindow, EditarInstrutorWindow, CadastroCursoWindow, AssociarCursoWindow, ExcluirInstrutorWindow |
| `database_utils.py` | Conexão e migrações do banco |
| `setup.py` | Build cx_Freeze (gera `build/exe.win-amd64-3.13/`) |
| `Gestão de Cursos.iss` | Inno Setup (gera `installer_output/GestaoDeCursos_Setup.exe`) |
| `version.txt` | Versão atual (lida pelo .iss e pelo auto-update) |
| `novidades_v1.1.txt` | Changelog exibido no instalador |
| `AGENTS.md` | Este arquivo — contexto para agentes |
| `README.md` | Documentação do GitHub |

## MainWindow (janela principal)
- `main.py` linha ~3800–4083
- Menu lateral com: Cursos, Instrutores, Programação, Histórico, Config, Sair
- Calendário para seleção de data
- Botão "Programar" em cada data abre `ProgramarCursoWindow`
- Clique duplo em curso programado abre `DetalhesProgramacaoWindow`
- Botão "Informações" no canto inferior direito

### Tabelas na MainWindow
- `self.tabela` (QTableWidget) — cursos programados no mês selecionado
- Colunas: Data, Horário, Curso, Instrutor, Carga Horária

## ProgramarCursoWindow
- `main.py` linha ~38
- Seleciona curso, instrutor, horário, tema
- Salva na tabela `programacao` do banco

## DetalhesProgramacaoWindow
- `main.py` linha ~2000
- Abre ao clicar duas vezes num curso programado
- Exibe dados do curso, instrutor, carga horária
- Aba "E-mail" com o sistema completo de e-mail
- Aba "Logs" para acompanhamento de envio

## Sistema de E-mail (DetalhesProgramacaoWindow)
### Editor HTML (3 seções)
- `self.email_cabecalho` — QTextEdit personalizado (Cabeçalho)
- `self.email_corpo` — QTextEdit personalizado (Corpo Principal)
- `self.email_rodape` — QTextEdit personalizado (Rodapé)
- Cada um usa a classe `EmailEditor` (herda de QTextEdit)
- Abas no painel esquerdo para alternar entre as 3 seções

### Toolbar (idêntica para cada seção)
- Botões: B (negrito), I (itálico), U (sublinhado)
- Headings: H1, H2, H3
- Alinhamento: esquerda, centro, direita
- Listas: ordenada, não ordenada
- Hiperlink
- Imagem (abre diálogo de inserção com redimensionamento 25-100% e alinhamento)
- Botão (diálogo: texto, URL, cor, border-radius, padding vertical/horizontal, alinhamento)
- Cor da fonte (QColorDialog)
- Cor de fundo (QColorDialog — aplica `blockFormat.setBackground()`)
- Combo "Inserir Variável" com: `{{nome_curso}}`, `{{data_curso}}`, `{{hora_curso}}`, `{{nome_instrutor}}`, `{{carga_horaria}}`, `{{tema_curso}}`
- HTML source editor (`</> HTML`)

### Variáveis Disponíveis
| Variável | Descrição | Fonte |
|---|---|---|
| `{{nome_curso}}` | Nome do curso | Banco (`cursos.nome`) |
| `{{data_curso}}` | Data formatada (dd/MM/yyyy) | Campo `self.data` |
| `{{hora_curso}}` | Horário do curso | Banco (`programacao.hora`) |
| `{{nome_instrutor}}` | Nome do instrutor | Banco (`instrutores.nome`) |
| `{{carga_horaria}}` | Carga horária (ex: 40h) | Banco (`cursos.carga_horaria`) |
| `{{tema_curso}}` | Tema do curso | Banco (`cursos.tema`) |

### Preview
- `self.email_previa` (QTextEdit readonly)
- Card com: De/Para/Assunto, corpo do email, rodapé de aviso
- Estrutura HTML: `<table>` com 3 rows (header, corpo, footer)
- Preview atualiza em tempo real
- `_secao_html_isolada(editor)` — extrai HTML de cada editor, envolve em `<table width="100%">` para isolar CSS do background-color
- `atualizar_previa()` — junta as 3 seções com `<hr>` entre elas

### Imagens (CID)
- `self._imagens` dict — armazena base64, width, alignment
- Placeholder no editor: `_IMG_{id}_{px}_{align}_`
- Conversão em `_converter_imagens_para_html(html, imagens, usar_cid)` (função module-level)
- Envio real usa `MIMEImage` com `Content-ID: <img_N@gestorcursos>`
- Preview usa base64 data URI

### Botões
- Placeholder: `<a href="btn://data?...">texto</a>`
- Conversão em `_converter_botoes_para_html(html, imagens)` (função module-level)
- Vira `<table>` com `<td>` estilizado (cor, border-radius, padding)

### Template Management
- Botão "Carregar Template" → `carregar_template()` abre QDialog com lista
- Ações: Carregar, Renomear, Excluir
- "Salvar Como Novo Template" → salva como novo
- "Sobrescrever/Salvar Alterações" → aparece quando template carregado e modificado
- Banco: tabela `email_templates` (id, nome, assunto, corpo_html, corpo_cabecario, corpo_principal, corpo_rodape)
- Backward compatibility: templates antigos (só `corpo_html`) carregam no corpo e deixam header/footer vazios

### HTML Source Editor
- Botão `</> HTML` abre QDialog com QPlainTextEdit
- Mostra HTML combinado com marcadores: `<!-- CABECALHO -->`, `<!-- CORPO -->`, `<!-- RODAPE -->`
- Ao aplicar, reparseia os marcadores e distribui para cada editor

### Configuração SMTP
- `ConfigEmailWindow` — host, port, user, password, from name, TLS toggle
- "Testar Envio" → envia e-mail de teste
- Config salva em `smtp_config` (provavelmente no banco ou arquivo)

### Envio (SendEmailThread)
- `SendEmailThread(QThread)` — roda em background, não trava a UI
- Sinais: `log_message(str)`, `progress(atual, total)`, `error_smtp(str)`, `finished_send()`
- `enviar_emails()` coleta dados, cria thread, conecta sinais, desabilita botão
- `_envio_finalizado()` reabilita botão e mostra resultado
- Atraso configurável via `QSpinBox` (1-60s, padrão 5s)
- Logs vão pra aba "Logs"

## Instrutores (dialog_windows.py)
### CadastroInstrutorWindow
- Nome, CPF, CNPJ, Empresa, Nº Processo SEI, E-mail, Telefone
- Nível de Formação (multi-select: Doutor, Especialista, Graduação, Mestre)
- Modalidade (multi-select: Presencial, On-line, Conteudista)
- Cursos Associados (multi-select)
- Documentos (upload com extensão verificada)

### EditarInstrutorWindow
- Mesmos campos do cadastro, com QScrollArea
- Seleciona instrutor por combo, carrega dados
- Documentos: lista com ícones de "Adicionar" e "Excluir"

### ExcluirInstrutorWindow
- Seleciona instrutor por combo, confirma exclusão

## Cursos (dialog_windows.py)
### CadastroCursoWindow
- Nome, Descrição (QTextEdit), Carga Horária (só números), Tema (QTextEdit)
- Instrutores associados (multi-select)

### AssociarCursoWindow
- Relaciona cursos a instrutores

## Database
- Caminho: `\\srvsql\Banco Cursos\instrutores.db` (network path)
- Funções em `database_utils.py`:
  - `criar_banco()` — cria tabelas se não existirem
  - `atualizar_banco()` — migrações (ex: add coluna corpo_cabecario/corpo_rodape)

### Tabelas
- `instrutores` — id, nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades
- `instrutores_documentos` — id, instrutor_id, nome_arquivo, extensao, mime_type, data_upload
- `instrutores_cursos` — instrutor_id, curso_id
- `cursos` — id, nome, descricao, carga_horaria, tema
- `programacao` — id, curso_id, instrutor_id, data, hora, tema
- `email_templates` — id, nome, assunto, corpo_html, corpo_cabecario, corpo_principal, corpo_rodape

## Atualização Automática
- `version.txt` na raiz → versão atual (ex: `1.1`)
- `verificar_atualizacao()` em `main.py` (~linha 4156) — chamada no startup
- Busca `version.txt` em `https://raw.githubusercontent.com/JeffVane/gestorcursos/main/version.txt`
- Compara com `packaging.version.Version`
- Se remota > local → QMessageBox pergunta se quer atualizar
- Busca Latest Release na API do GitHub, procura asset contendo `GestaoDeCursos_Setup`
- `DownloadThread` baixa em chunks de 2MB com progresso
- `ShellExecuteW(runas, caminho)` executa instalador com admin
- `sys.exit(0)` — app fecha, instalador substitui os arquivos

## Build e Instalação
### Build .exe
```powershell
python setup.py build
```
Gera pasta `build/exe.win-amd64-3.13/`

### Instalador
Compilar `Gestão de Cursos.iss` com Inno Setup
- Lê versão do `version.txt` automaticamente
- Gera `installer_output/GestaoDeCursos_Setup.exe`

### Release no GitHub
1. Atualizar `version.txt`
2. Build + Inno Setup
3. Criar Release com tag e asset anexado

## Observações Técnicas
- `QTextEdit.toHtml()` coloca `background-color` no `<body>` tag, não nos `<p>` — `_secao_html_isolada` captura o body style
- `<table>` wrapper é usado em vez de `<div>` porque Qt não respeita `overflow: hidden` para bg-color
- Toolbar buttons têm `setFixedSize(26,26)` porque stylesheet global força `min-height:40px`
- `from urllib.parse import urlencode, parse_qs` para CID de botões
- `from email.mime.image import MIMEImage` para CID de imagens
- `DetalhesProgramacaoWindow` é recriada toda vez que abre — `self._imagens` não persiste entre aberturas
