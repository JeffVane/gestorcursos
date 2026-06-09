# Gestão de Cursos

Sistema desktop para gestão de cursos e instrutores, com envio de e-mails, relatórios em PDF e atualização automática.

## Funcionalidades

- 📅 **Programação de Cursos** — calendário com agendamento de turmas
- 👨‍🏫 **Cadastro de Instrutores** — dados, documentos, níveis de formação, modalidades
- 📚 **Cadastro de Cursos** — informações, carga horária, temas
- 📧 **Envio de E-mails** — editor HTML com 3 seções (cabeçalho/corpo/rodapé), imagens CID, botões, templates, preview em tempo real
- 📄 **Relatórios em PDF** — histórico, certificados
- 🔄 **Atualização Automática** — detecta nova versão no GitHub e baixa/instala automaticamente

## Requisitos

- Python 3.13+
- PyQt5
- reportlab
- cx_Freeze
- requests

## Instalação para Desenvolvimento

```powershell
pip install PyQt5 reportlab cx_Freeze requests packaging
python main.py
```

## Build

```powershell
python setup.py build
```

## Instalador

Compilar `Gestão de Cursos.iss` com Inno Setup.

## Repositório

GitHub: [JeffVane/gestorcursos](https://github.com/JeffVane/gestorcursos)
