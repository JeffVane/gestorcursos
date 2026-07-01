from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QMessageBox, QListWidget, QListWidgetItem,
    QComboBox, QTimeEdit, QHBoxLayout, QCalendarWidget, QHeaderView, QFileDialog, QTextEdit,
    QScrollArea, QDateEdit, QCheckBox, QTabWidget, QProgressBar, QFrame
)
import sqlite3
import re
from PyQt5.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
from PyQt5.QtGui import QTextCharFormat, QColor, QIcon, QFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
import re
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
import os
import mimetypes
from PyQt5.QtWidgets import QMenu, QAction
import pandas as pd
import chardet
import codecs
import unicodedata
import traceback





def somente_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def cpf_valido(cpf: str) -> bool:
    cpf = somente_digitos(cpf)

    if len(cpf) != 11:
        return False

    # rejeita CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False

    # calcula dígito 1
    soma = 0
    for i, peso in enumerate(range(10, 1, -1)):
        soma += int(cpf[i]) * peso
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1

    # calcula dígito 2
    soma = 0
    for i, peso in enumerate(range(11, 1, -1)):
        soma += int(cpf[i]) * peso
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2

    return cpf[-2:] == f"{d1}{d2}"

def telefone_valido_br(telefone: str) -> bool:
    t = somente_digitos(telefone)

    # opcional: se estiver vazio, não valida (retorna True)
    if not t:
        return True

    # Esperado: DDD + número (10 ou 11 dígitos)
    if len(t) not in (10, 11):
        return False

    ddd = int(t[:2])
    if ddd < 11 or ddd > 99:
        return False

    # Se 11 dígitos (celular), no Brasil costuma começar com 9 após o DDD
    if len(t) == 11 and t[2] != "9":
        return False

    return True

def somente_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def cpf_valido(cpf: str) -> bool:
    cpf = somente_digitos(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2

    return cpf[-2:] == f"{d1}{d2}"

def telefone_valido_br(tel: str) -> bool:
    tel = somente_digitos(tel)
    if not tel:
        return True
    if len(tel) not in (10, 11):
        return False
    ddd = int(tel[:2])
    if ddd < 11 or ddd > 99:
        return False
    if len(tel) == 11 and tel[2] != "9":
        return False
    return True



# Janela de cadastro de instrutores
class CadastroInstrutorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Instrutor")
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setGeometry(200, 200, 700, 650)

        main_layout = QVBoxLayout()

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)

        layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        layout.addWidget(self.instrutor_input)

        # CPF e CNPJ lado a lado
        row_doc = QHBoxLayout()
        row_doc.addWidget(QLabel("CPF"))
        self.cpf_input = QLineEdit()
        self.cpf_input.setPlaceholderText("ex: 123.456.789-00")
        self.cpf_input.setClearButtonEnabled(True)
        self.cpf_input.editingFinished.connect(self.validar_cpf_campo)
        row_doc.addWidget(self.cpf_input)
        row_doc.addWidget(QLabel("CNPJ (se houver)"))
        self.cnpj_input = QLineEdit()
        row_doc.addWidget(self.cnpj_input)
        layout.addLayout(row_doc)

        # Empresa e Processo SEI lado a lado
        row_emp = QHBoxLayout()
        row_emp.addWidget(QLabel("Nome da Empresa"))
        self.empresa_input = QLineEdit()
        row_emp.addWidget(self.empresa_input)
        row_emp.addWidget(QLabel("Nº Processo SEI"))
        self.processo_sei_input = QLineEdit()
        self.processo_sei_input.setPlaceholderText("Ex: 00000.000000/2024-11")
        row_emp.addWidget(self.processo_sei_input)
        layout.addLayout(row_emp)

        # E-mail e Telefone lado a lado
        row_contato = QHBoxLayout()
        row_contato.addWidget(QLabel("E-mail"))
        self.email_input = QLineEdit()
        row_contato.addWidget(self.email_input)
        row_contato.addWidget(QLabel("Telefone"))
        self.telefone_input = QLineEdit()
        self.telefone_input.setInputMask("(00) 9 0000-0000;_")
        self.telefone_input.setClearButtonEnabled(True)
        self.telefone_input.editingFinished.connect(self.validar_telefone_campo)
        row_contato.addWidget(self.telefone_input)
        layout.addLayout(row_contato)

        # Datas lado a lado
        row_datas = QHBoxLayout()
        row_datas.addWidget(QLabel("Data Solicitação Credenciamento"))
        self.data_solicitacao_input = QDateEdit()
        self.data_solicitacao_input.setCalendarPopup(True)
        self.data_solicitacao_input.setDate(QDate.currentDate())
        self.data_solicitacao_input.setDisplayFormat("dd/MM/yyyy")
        row_datas.addWidget(self.data_solicitacao_input)
        row_datas.addWidget(QLabel("Validade do Contrato"))
        self.validade_contrato_input = QDateEdit()
        self.validade_contrato_input.setCalendarPopup(True)
        self.validade_contrato_input.setDate(QDate.currentDate())
        self.validade_contrato_input.setDisplayFormat("dd/MM/yyyy")
        row_datas.addWidget(self.validade_contrato_input)
        layout.addLayout(row_datas)

        # Convocado + Sugestões
        row_conv = QHBoxLayout()
        self.convocado_check = QCheckBox("Convocado para ministrar cursos no ano")
        row_conv.addWidget(self.convocado_check)
        row_conv.addStretch()
        layout.addLayout(row_conv)

        layout.addWidget(QLabel("Sugestões de Cursos"))
        self.sugestoes_cursos_input = QTextEdit()
        self.sugestoes_cursos_input.setMaximumHeight(60)
        layout.addWidget(self.sugestoes_cursos_input)

        layout.addWidget(QLabel("Temas que o Instrutor Ministra"))
        self.temas_instrutor_list = QListWidget()
        self.temas_instrutor_list.setSelectionMode(QListWidget.MultiSelection)
        self.temas_instrutor_list.setMaximumHeight(100)
        self.carregar_temas_para_instrutor()
        layout.addWidget(self.temas_instrutor_list)

        # Nível e Modalidade lado a lado
        row_perfis = QHBoxLayout()

        col_nivel = QVBoxLayout()
        col_nivel.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        self.niveis_formacao_list.setMaximumHeight(80)
        for nivel in ["Doutor", "Especialista", "Graduação", "Mestre"]:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        col_nivel.addWidget(self.niveis_formacao_list)
        row_perfis.addLayout(col_nivel)

        col_mod = QVBoxLayout()
        col_mod.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        self.modalidades_list.setMaximumHeight(80)
        for modalidade in ["Presencial", "On-line", "Conteudista"]:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        col_mod.addWidget(self.modalidades_list)
        row_perfis.addLayout(col_mod)

        layout.addLayout(row_perfis)

        # ===== Documentos anexos =====
        layout.addWidget(QLabel("Documentos do Instrutor"))
        self.docs_list = QListWidget()
        self.docs_list.setMaximumHeight(80)
        layout.addWidget(self.docs_list)

        btn_docs_layout = QHBoxLayout()
        self.btn_add_doc = QPushButton("Anexar documentos")
        self.btn_add_doc.clicked.connect(self.anexar_documentos)
        btn_docs_layout.addWidget(self.btn_add_doc)

        self.btn_rem_doc = QPushButton("Remover selecionado")
        self.btn_rem_doc.clicked.connect(self.remover_documento_selecionado)
        btn_docs_layout.addWidget(self.btn_rem_doc)

        layout.addLayout(btn_docs_layout)

        self.documentos_paths = []

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        self.add_button = QPushButton("Cadastrar")
        self.add_button.clicked.connect(self.cadastrar_instrutor)
        main_layout.addWidget(self.add_button)

        self.setLayout(main_layout)

    def anexar_documentos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar documentos do instrutor",
            "",
            "Todos os arquivos (*.*);;PDF (*.pdf);;Word (*.doc *.docx);;Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not arquivos:
            return

        for p in arquivos:
            if p not in self.documentos_paths:
                self.documentos_paths.append(p)
                item = QListWidgetItem(os.path.basename(p))
                item.setToolTip(p)               # mostra caminho ao passar o mouse
                item.setData(Qt.UserRole, p)     # guarda caminho
                self.docs_list.addItem(item)


    def remover_documento_selecionado(self):
        row = self.docs_list.currentRow()
        if row < 0:
            return
        item = self.docs_list.takeItem(row)
        p = item.data(Qt.UserRole)
        if p in self.documentos_paths:
            self.documentos_paths.remove(p)

    def carregar_temas_para_instrutor(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()

            self.temas_instrutor_list.clear()
            for tema in temas:
                item = QListWidgetItem(tema[1])
                item.setData(Qt.UserRole, tema[0])
                self.temas_instrutor_list.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def validar_cpf_campo(self):
        cpf_digits = re.sub(r"\D", "", self.cpf_input.text())

        if not cpf_digits:
            return  # campo vazio é permitido

        if len(cpf_digits) != 11 or not cpf_valido(cpf_digits):
            QMessageBox.warning(self, "CPF inválido", "O CPF informado é inválido.")
            self.cpf_input.setFocus()
            self.cpf_input.selectAll()

    def validar_telefone_campo(self):
        tel_digits = re.sub(r"\D", "", self.telefone_input.text())

        if not tel_digits:
            return  # campo vazio é permitido

        if len(tel_digits) < 10 or len(tel_digits) > 11:
            QMessageBox.warning(
                self,
                "Telefone inválido",
                "Informe um telefone válido com DDD + número (10 ou 11 dígitos)."
            )
            self.telefone_input.setFocus()
            self.telefone_input.selectAll()
            return

        ddd = int(tel_digits[:2])
        if ddd < 11 or ddd > 99:
            QMessageBox.warning(
                self,
                "Telefone inválido",
                "DDD inválido. Informe um DDD entre 11 e 99."
            )
            self.telefone_input.setFocus()
            self.telefone_input.selectAll()
            return

        if len(tel_digits) == 11 and tel_digits[2] != "9":
            QMessageBox.warning(
                self,
                "Telefone inválido",
                "Para celular com 11 dígitos, o número deve começar com 9 após o DDD."
            )
            self.telefone_input.setFocus()
            self.telefone_input.selectAll()


    def cadastrar_instrutor(self):
        nome = self.instrutor_input.text().strip()
        cpf_raw = self.cpf_input.text().strip()
        tel_raw = self.telefone_input.text().strip()

        niveis_selecionados = [item.text() for item in self.niveis_formacao_list.selectedItems()]
        modalidades_selecionadas = [item.text() for item in self.modalidades_list.selectedItems()]

        # Todos os campos são opcionais
        nome = nome or None
        niveis_selecionados = niveis_selecionados or []
        modalidades_selecionadas = modalidades_selecionadas or []

        # ===== CPF (opcional, mas se preencher tem que ser válido) =====
        cpf_digits = somente_digitos(cpf_raw)
        if cpf_raw and not cpf_valido(cpf_raw):
            QMessageBox.warning(self, "Erro", "CPF inválido. Verifique e tente novamente.")
            self.cpf_input.setFocus()
            self.cpf_input.selectAll()
            return

        # Se você quiser CPF obrigatório, descomente estas 3 linhas:
        # if not cpf_digits:
        #     QMessageBox.warning(self, "Erro", "CPF é obrigatório.")
        #     return

        # ===== Telefone (opcional, mas se preencher tem que ser válido) =====
        tel_digits = somente_digitos(tel_raw)
        if tel_raw and not telefone_valido_br(tel_raw):
            QMessageBox.warning(self, "Erro", "Telefone inválido. Informe DDD + número (10 ou 11 dígitos).")
            self.telefone_input.setFocus()
            self.telefone_input.selectAll()
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO instrutores 
                (nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades,
                 data_solicitacao_credenciamento, validade_contrato, convocado_ano, sugestoes_cursos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            nome,
            cpf_digits if cpf_digits else None,
            self.cnpj_input.text().strip() or None,
            self.empresa_input.text().strip() or None,
            self.processo_sei_input.text().strip() or None,
            self.email_input.text().strip() or None,
            tel_digits if tel_digits else None,
            ",".join(niveis_selecionados) if niveis_selecionados else None,
            ",".join(modalidades_selecionadas) if modalidades_selecionadas else None,
            self.data_solicitacao_input.date().toString("yyyy-MM-dd"),
            self.validade_contrato_input.date().toString("yyyy-MM-dd"),
            "Sim" if self.convocado_check.isChecked() else "Não",
            self.sugestoes_cursos_input.toPlainText().strip() or None
        ))

            instrutor_id = cursor.lastrowid

            # Salvar documentos no banco
            for path in self.documentos_paths:
                try:
                    with open(path, "rb") as f:
                        blob = f.read()

                    nome_arq = os.path.basename(path)
                    ext = os.path.splitext(nome_arq)[1].lower()
                    mime, _ = mimetypes.guess_type(path)
                    mime = mime or "application/octet-stream"

                    cursor.execute("""
                        INSERT INTO instrutores_documentos
                        (instrutor_id, nome_arquivo, extensao, mime_type, conteudo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (instrutor_id, nome_arq, ext, mime, blob))

                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"Não foi possível anexar o arquivo:\n{path}\n\nErro: {e}"
                    )

            # Salvar temas associados ao instrutor
            temas_selecionados = [item.data(Qt.UserRole) for item in self.temas_instrutor_list.selectedItems()]
            for tema_id in temas_selecionados:
                cursor.execute("INSERT OR IGNORE INTO temas_instrutores (tema_id, instrutor_id) VALUES (?, ?)",
                               (tema_id, instrutor_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", f'Instrutor "{nome}" cadastrado com sucesso!')

            self.instrutor_input.clear()
            self.cpf_input.clear()
            self.cnpj_input.clear()
            self.empresa_input.clear()
            self.email_input.clear()
            self.telefone_input.clear()
            self.niveis_formacao_list.clearSelection()
            self.modalidades_list.clearSelection()
            self.temas_instrutor_list.clearSelection()
            self.docs_list.clear()
            self.documentos_paths.clear()
            self.processo_sei_input.clear()
            self.data_solicitacao_input.setDate(QDate.currentDate())
            self.validade_contrato_input.setDate(QDate.currentDate())
            self.convocado_check.setChecked(False)
            self.sugestoes_cursos_input.clear()


        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um instrutor com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao cadastrar instrutor:\n{str(e)}")


# Janela para editar instrutor
class EditarInstrutorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("editar.png"))
        self.setWindowTitle("Editar Instrutor")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Selecione o Instrutor"))
        self.instrutor_combo = QComboBox()
        self.instrutor_combo.currentIndexChanged.connect(self.carregar_dados_instrutor)
        layout.addWidget(self.instrutor_combo)

        # ===== Abas =====
        self.tabs = QTabWidget()

        # --- Aba 1: Dados do Instrutor ---
        tab_dados = QWidget()
        tab_dados_layout = QVBoxLayout(tab_dados)

        scroll_dados = QScrollArea()
        scroll_dados.setWidgetResizable(True)
        scroll_dados_widget = QWidget()
        scroll_dados_layout = QVBoxLayout(scroll_dados_widget)

        scroll_dados_layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        scroll_dados_layout.addWidget(self.instrutor_input)
        scroll_dados_layout.addWidget(QLabel("CPF"))
        self.cpf_input = QLineEdit()
        scroll_dados_layout.addWidget(self.cpf_input)

        scroll_dados_layout.addWidget(QLabel("CNPJ (se houver)"))
        self.cnpj_input = QLineEdit()
        scroll_dados_layout.addWidget(self.cnpj_input)

        scroll_dados_layout.addWidget(QLabel("Nome da Empresa"))
        self.empresa_input = QLineEdit()
        scroll_dados_layout.addWidget(self.empresa_input)

        scroll_dados_layout.addWidget(QLabel("Nº Processo SEI"))
        self.processo_sei_input = QLineEdit()
        scroll_dados_layout.addWidget(self.processo_sei_input)

        scroll_dados_layout.addWidget(QLabel("E-mail"))
        self.email_input = QLineEdit()
        scroll_dados_layout.addWidget(self.email_input)

        scroll_dados_layout.addWidget(QLabel("Telefone"))
        self.telefone_input = QLineEdit()
        scroll_dados_layout.addWidget(self.telefone_input)

        scroll_dados_layout.addWidget(QLabel("Data de Solicitação de Credenciamento"))
        self.data_solicitacao_input = QDateEdit()
        self.data_solicitacao_input.setCalendarPopup(True)
        self.data_solicitacao_input.setDate(QDate.currentDate())
        self.data_solicitacao_input.setDisplayFormat("dd/MM/yyyy")
        scroll_dados_layout.addWidget(self.data_solicitacao_input)

        scroll_dados_layout.addWidget(QLabel("Validade do Contrato"))
        self.validade_contrato_input = QDateEdit()
        self.validade_contrato_input.setCalendarPopup(True)
        self.validade_contrato_input.setDate(QDate.currentDate())
        self.validade_contrato_input.setDisplayFormat("dd/MM/yyyy")
        scroll_dados_layout.addWidget(self.validade_contrato_input)

        self.convocado_check = QCheckBox("Convocado para ministrar cursos durante o ano")
        scroll_dados_layout.addWidget(self.convocado_check)

        scroll_dados_layout.addWidget(QLabel("Sugestões de Cursos"))
        self.sugestoes_cursos_input = QTextEdit()
        self.sugestoes_cursos_input.setMaximumHeight(80)
        scroll_dados_layout.addWidget(self.sugestoes_cursos_input)

        scroll_dados_layout.addWidget(QLabel("Temas que o Instrutor Ministra"))
        self.temas_instrutor_list = QListWidget()
        self.temas_instrutor_list.setSelectionMode(QListWidget.MultiSelection)
        self.temas_instrutor_list.setMaximumHeight(100)
        self.carregar_temas_para_instrutor()
        scroll_dados_layout.addWidget(self.temas_instrutor_list)

        scroll_dados_layout.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        niveis_formacao = ["Doutor", "Especialista", "Graduação", "Mestre"]
        for nivel in niveis_formacao:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        scroll_dados_layout.addWidget(self.niveis_formacao_list)

        scroll_dados_layout.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        modalidades = ["Presencial", "On-line", "Conteudista"]
        for modalidade in modalidades:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        scroll_dados_layout.addWidget(self.modalidades_list)

        scroll_dados_layout.addStretch()

        scroll_dados.setWidget(scroll_dados_widget)
        tab_dados_layout.addWidget(scroll_dados)

        self.tabs.addTab(tab_dados, "Dados do Instrutor")

        # --- Aba 2: Cursos e Documentos ---
        tab_cursos = QWidget()
        tab_cursos_layout = QVBoxLayout(tab_cursos)

        scroll_cursos = QScrollArea()
        scroll_cursos.setWidgetResizable(True)
        scroll_cursos_widget = QWidget()
        scroll_cursos_layout = QVBoxLayout(scroll_cursos_widget)

        scroll_cursos_layout.addWidget(QLabel("Cursos Associados"))
        self.cursos_list = QListWidget()
        self.cursos_list.setSelectionMode(QListWidget.MultiSelection)
        scroll_cursos_layout.addWidget(self.cursos_list)

        # ===== Documentos do Instrutor =====
        scroll_cursos_layout.addWidget(QLabel("Documentos do Instrutor"))

        self.docs_list = QListWidget()
        scroll_cursos_layout.addWidget(self.docs_list)

        docs_btns = QHBoxLayout()

        self.btn_add_doc = QPushButton("Adicionar documentos")
        self.btn_add_doc.clicked.connect(self.adicionar_documentos)
        docs_btns.addWidget(self.btn_add_doc)

        self.btn_del_doc = QPushButton("Excluir selecionado")
        self.btn_del_doc.clicked.connect(self.excluir_documento_selecionado)
        docs_btns.addWidget(self.btn_del_doc)

        scroll_cursos_layout.addLayout(docs_btns)

        # guarda paths novos (ainda não salvos)
        self.novos_documentos_paths = []

        scroll_cursos.setWidget(scroll_cursos_widget)
        tab_cursos_layout.addWidget(scroll_cursos)

        self.tabs.addTab(tab_cursos, "Cursos e Documentos")

        layout.addWidget(self.tabs)

        self.save_button = QPushButton("Salvar Alterações")
        self.save_button.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.carregar_instrutores()

    def carregar_instrutores(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            conn.close()

            self.instrutor_combo.clear()
            if instrutores:
                for instrutor in instrutores:
                    self.instrutor_combo.addItem(instrutor[1], instrutor[0])
                self.carregar_dados_instrutor()
            else:
                QMessageBox.warning(self, "Aviso", "Nenhum instrutor encontrado no banco de dados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao carregar instrutores: {str(e)}")

    def carregar_dados_instrutor(self):
        try:
            self.niveis_formacao_list.clearSelection()
            self.modalidades_list.clearSelection()
            self.cursos_list.clear()

            instrutor_id = self.instrutor_combo.currentData()
            if not instrutor_id:
                self.instrutor_input.clear()
                return

            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades,
                       data_solicitacao_credenciamento, validade_contrato, convocado_ano, sugestoes_cursos
                FROM instrutores
                WHERE id = ?
            """, (instrutor_id,))

            instrutor = cursor.fetchone()

            if instrutor:
                (nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades,
                 data_solicitacao, validade_contrato, convocado_ano, sugestoes_cursos) = instrutor

                self.processo_sei_input.setText(processo_sei or "")
                self.instrutor_input.setText(nome)
                self.cpf_input.setText(cpf or "")
                self.cnpj_input.setText(cnpj or "")
                self.empresa_input.setText(empresa or "")
                self.email_input.setText(email or "")
                self.telefone_input.setText(telefone or "")

                if data_solicitacao:
                    self.data_solicitacao_input.setDate(QDate.fromString(data_solicitacao, "yyyy-MM-dd"))
                else:
                    self.data_solicitacao_input.setDate(QDate.currentDate())

                if validade_contrato:
                    self.validade_contrato_input.setDate(QDate.fromString(validade_contrato, "yyyy-MM-dd"))
                else:
                    self.validade_contrato_input.setDate(QDate.currentDate())

                self.convocado_check.setChecked(convocado_ano == "Sim" if convocado_ano else False)
                self.sugestoes_cursos_input.setPlainText(sugestoes_cursos or "")

                if niveis_formacao:
                    niveis_lista = niveis_formacao.split(",")
                    for i in range(self.niveis_formacao_list.count()):
                        item = self.niveis_formacao_list.item(i)
                        item.setSelected(item.text() in niveis_lista)

                if modalidades:
                    modalidades_lista = modalidades.split(",")
                    for i in range(self.modalidades_list.count()):
                        item = self.modalidades_list.item(i)
                        item.setSelected(item.text() in modalidades_lista)

                cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
                todos_cursos = cursor.fetchall()
                for curso_id, curso_nome in todos_cursos:
                    item = QListWidgetItem(curso_nome)
                    item.setData(Qt.UserRole, curso_id)
                    self.cursos_list.addItem(item)

                cursor.execute("""
                    SELECT curso_id FROM instrutores_cursos WHERE instrutor_id = ?
                """, (instrutor_id,))
                cursos_associados = [row[0] for row in cursor.fetchall()]
                for i in range(self.cursos_list.count()):
                    item = self.cursos_list.item(i)
                    if item.data(Qt.UserRole) in cursos_associados:
                        item.setSelected(True)

                # Carregar temas associados ao instrutor
                self.temas_instrutor_list.clearSelection()
                cursor.execute("SELECT tema_id FROM temas_instrutores WHERE instrutor_id = ?", (instrutor_id,))
                temas_associados = {row[0] for row in cursor.fetchall()}
                for i in range(self.temas_instrutor_list.count()):
                    item = self.temas_instrutor_list.item(i)
                    if item.data(Qt.UserRole) in temas_associados:
                        item.setSelected(True)

                self.carregar_documentos_instrutor(instrutor_id)

            else:
                QMessageBox.warning(self, "Erro", "Os dados do instrutor não foram encontrados.")

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Ocorreu um erro: {str(e)}")

    def carregar_documentos_instrutor(self, instrutor_id):
        self.docs_list.clear()
        if not instrutor_id:
            return

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nome_arquivo, extensao, mime_type
            FROM instrutores_documentos
            WHERE instrutor_id = ?
            ORDER BY data_upload DESC, id DESC
        """, (instrutor_id,))
        docs = cursor.fetchall()
        conn.close()

        # Documentos já existentes no banco
        for doc_id, nome, ext, mime in docs:
            item = QListWidgetItem(f"[SALVO] {nome}")
            item.setToolTip(f"{mime or ''} {ext or ''}".strip())
            item.setData(Qt.UserRole, {"tipo": "db", "doc_id": doc_id})
            self.docs_list.addItem(item)

        # Documentos novos (ainda não salvos)
        for p in self.novos_documentos_paths:
            item = QListWidgetItem(f"[NOVO] {os.path.basename(p)}")
            item.setToolTip(p)
            item.setData(Qt.UserRole, {"tipo": "novo", "path": p})
            self.docs_list.addItem(item)

        if self.docs_list.count() == 0:
            it = QListWidgetItem("(Sem documentos)")
            it.setFlags(Qt.NoItemFlags)
            self.docs_list.addItem(it)

    def carregar_temas_para_instrutor(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()

            self.temas_instrutor_list.clear()
            for tema in temas:
                item = QListWidgetItem(tema[1])
                item.setData(Qt.UserRole, tema[0])
                self.temas_instrutor_list.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def adicionar_documentos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar documentos do instrutor",
            "",
            "Todos os arquivos (*.*);;PDF (*.pdf);;Word (*.doc *.docx);;Imagens (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not arquivos:
            return

        for p in arquivos:
            if p not in self.novos_documentos_paths:
                self.novos_documentos_paths.append(p)

        instrutor_id = self.instrutor_combo.currentData()
        self.carregar_documentos_instrutor(instrutor_id)

    def excluir_documento_selecionado(self):
        item = self.docs_list.currentItem()
        if not item:
            return

        data = item.data(Qt.UserRole)
        if not data or not isinstance(data, dict):
            return

        tipo = data.get("tipo")

        # Se for novo (ainda não salvo), só remove da lista interna
        if tipo == "novo":
            p = data.get("path")
            if p in self.novos_documentos_paths:
                self.novos_documentos_paths.remove(p)
            instrutor_id = self.instrutor_combo.currentData()
            self.carregar_documentos_instrutor(instrutor_id)
            return

        # Se for do banco, apaga do banco
        if tipo == "db":
            doc_id = data.get("doc_id")
            if not doc_id:
                return

            resp = QMessageBox.question(
                self,
                "Confirmação",
                "Tem certeza que deseja excluir este documento?\nEssa ação não pode ser desfeita.",
                QMessageBox.Yes | QMessageBox.No
            )
            if resp != QMessageBox.Yes:
                return

            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM instrutores_documentos WHERE id = ?", (doc_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Sucesso", "Documento excluído com sucesso!")
                instrutor_id = self.instrutor_combo.currentData()
                self.carregar_documentos_instrutor(instrutor_id)

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir documento:\n{e}")

    def salvar_alteracoes(self):
        instrutor_id = self.instrutor_combo.currentData()
        nome = self.instrutor_input.text()
        niveis_selecionados = [item.text() for item in self.niveis_formacao_list.selectedItems()]
        modalidades_selecionadas = [item.text() for item in self.modalidades_list.selectedItems()]
        cursos_selecionados = [self.cursos_list.item(i).data(Qt.UserRole) for i in range(self.cursos_list.count()) if self.cursos_list.item(i).isSelected()]

        if not nome or not niveis_selecionados or not modalidades_selecionadas:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE instrutores SET
            nome = ?,
            cpf = ?,
            cnpj = ?,
            empresa = ?,
            processo_sei = ?,
            email = ?,
            telefone = ?,
            niveis_formacao = ?,
            modalidades = ?,
            data_solicitacao_credenciamento = ?,
            validade_contrato = ?,
            convocado_ano = ?,
            sugestoes_cursos = ?
            WHERE id = ?
                """, (
            nome,
            self.cpf_input.text().strip(),
            self.cnpj_input.text().strip(),
            self.empresa_input.text().strip(),
            self.processo_sei_input.text().strip() or None,
            self.email_input.text().strip(),
            self.telefone_input.text().strip(),
            ",".join(niveis_selecionados),
            ",".join(modalidades_selecionadas),
            self.data_solicitacao_input.date().toString("yyyy-MM-dd"),
            self.validade_contrato_input.date().toString("yyyy-MM-dd"),
            "Sim" if self.convocado_check.isChecked() else "Não",
            self.sugestoes_cursos_input.toPlainText().strip() or None,
            instrutor_id
        ))

        cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
        for curso_id in cursos_selecionados:
            cursor.execute("INSERT INTO instrutores_cursos (instrutor_id, curso_id) VALUES (?, ?)", (instrutor_id, curso_id))

        # ===== Salvar temas associados ao instrutor =====
        temas_selecionados = [item.data(Qt.UserRole) for item in self.temas_instrutor_list.selectedItems()]
        cursor.execute("DELETE FROM temas_instrutores WHERE instrutor_id = ?", (instrutor_id,))
        for tema_id in temas_selecionados:
            cursor.execute("INSERT INTO temas_instrutores (tema_id, instrutor_id) VALUES (?, ?)",
                           (tema_id, instrutor_id))

        # ===== Inserir novos documentos anexados =====
        for path in self.novos_documentos_paths:
            try:
                with open(path, "rb") as f:
                    blob = f.read()

                nome_arq = os.path.basename(path)
                ext = os.path.splitext(nome_arq)[1].lower()
                mime, _ = mimetypes.guess_type(path)
                mime = mime or "application/octet-stream"

                cursor.execute("""
                    INSERT INTO instrutores_documentos
                    (instrutor_id, nome_arquivo, extensao, mime_type, conteudo)
                    VALUES (?, ?, ?, ?, ?)
                """, (instrutor_id, nome_arq, ext, mime, blob))

            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Não foi possível anexar:\n{path}\n\nErro: {e}")

        # limpa lista de novos depois de salvar
        self.novos_documentos_paths.clear()

        conn.commit()
        conn.close()
        QMessageBox.information(self, "Sucesso", f"Instrutor '{nome}' atualizado com sucesso!")
        self.carregar_documentos_instrutor(instrutor_id)


# Janela de cadastro de cursos
class CadastroCursoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setWindowTitle("Cadastrar Curso")
        self.setGeometry(200, 200, 600, 200)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nome do Curso"))
        self.curso_input = QLineEdit()
        self.curso_input.textChanged.connect(self.corrigir_nome_curso)
        layout.addWidget(self.curso_input)

        layout.addWidget(QLabel("Tema do Curso"))
        self.tema_combo = QComboBox()
        self.carregar_temas_combo()
        layout.addWidget(self.tema_combo)

        layout.addWidget(QLabel("Código EPC"))
        self.epc_input = QLineEdit()
        self.epc_input.setPlaceholderText("Ex: DF-123456")
        self.epc_input.textChanged.connect(self.formatar_epc)
        layout.addWidget(self.epc_input)

        layout.addWidget(QLabel("Carga Horária (em horas)"))
        self.carga_horaria_input = QLineEdit()
        self.carga_horaria_input.setValidator(QIntValidator(1, 10000))
        self.carga_horaria_input.setPlaceholderText("Ex: 40")
        layout.addWidget(self.carga_horaria_input)

        layout.addWidget(QLabel("Descrição do Curso"))
        self.descricao_input = QTextEdit()
        self.descricao_input.setPlaceholderText("Digite a descrição do curso...")
        self.descricao_input.setFixedHeight(120)
        layout.addWidget(self.descricao_input)

        self.add_button = QPushButton("Cadastrar")
        self.add_button.clicked.connect(self.cadastrar_curso)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def formatar_epc(self):
        texto = self.epc_input.text().upper()

        # Remove tudo que não seja letra ou número
        texto = re.sub(r"[^A-Z0-9]", "", texto)

        # Limita a 2 letras iniciais
        letras = texto[:2]
        numeros = texto[2:10]  # até 8 números

        # Mantém somente números após as letras
        numeros = re.sub(r"[^0-9]", "", numeros)

        if len(letras) == 2:
            texto_formatado = f"{letras}-{numeros}"
        else:
            texto_formatado = letras

        if self.epc_input.text() != texto_formatado:
            self.epc_input.blockSignals(True)
            self.epc_input.setText(texto_formatado)
            self.epc_input.blockSignals(False)

    def corrigir_nome_curso(self):
        texto = self.curso_input.text()
        texto_corrigido = re.sub(r' +', ' ', texto)
        if self.curso_input.text() != texto_corrigido:
            self.curso_input.setText(texto_corrigido)

    def carregar_temas_combo(self):
        """Carrega os temas do banco de dados no combo de temas"""
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()
            
            self.tema_combo.clear()
            self.tema_combo.addItem("")
            for tema in temas:
                self.tema_combo.addItem(tema[1], tema[0])
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def cadastrar_curso(self):
        nome = self.curso_input.text().strip()
        tema = self.tema_combo.currentText()
        descricao = self.descricao_input.toPlainText().strip()
        epc = self.epc_input.text().strip().upper()
        carga_horaria = self.carga_horaria_input.text().strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "Preencha o nome do curso.")
            return

        if epc and not re.match(r"^[A-Z]{2}-\d{1,8}$", epc):
            QMessageBox.warning(
                self,
                "Erro",
                "Código EPC inválido.\nUse o formato: UF-123 até no máximo 8 números."
            )
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Garantia de compatibilidade (caso algum banco antigo não tenha tema)
            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]

            if "tema" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN tema TEXT")

            if "descricao" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN descricao TEXT")

            # Inserção do curso
            cursor.execute("""
                INSERT INTO cursos (nome, tema, descricao, epc, carga_horaria)
                VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                tema,
                descricao,
                epc if epc else None,
                int(carga_horaria) if carga_horaria else None
            ))

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Sucesso",
                f'Curso "{nome}" cadastrado com sucesso!\nTema: {tema}'
            )

            # Limpar campos
            self.curso_input.clear()
            self.tema_combo.setCurrentIndex(0)
            self.descricao_input.clear()
            self.epc_input.clear()
            self.carga_horaria_input.clear()


        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um curso com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao cadastrar curso:\n{str(e)}")


# Janela para associar cursos a instrutores
class AssociarCursoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("conectar.png"))
        self.setWindowTitle("Associar Cursos a Instrutores")
        self.setGeometry(200, 200, 800, 400)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Selecione o Instrutor"))
        self.instrutor_combo = QComboBox()
        self.instrutor_combo.currentIndexChanged.connect(self.alternar_instrutor)
        layout.addWidget(self.instrutor_combo)

        layout.addWidget(QLabel("Selecione os Cursos"))
        self.cursos_list = QListWidget()
        self.cursos_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.cursos_list)

        self.add_button = QPushButton("Associar")
        self.add_button.clicked.connect(self.associar_cursos)
        layout.addWidget(self.add_button)

        self.setLayout(layout)
        self.selecao_temporaria = {}
        self.carregar_dados()

    def carregar_dados(self):
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
        instrutores = cursor.fetchall()
        for instrutor in instrutores:
            self.instrutor_combo.addItem(instrutor[1], instrutor[0])

        cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
        cursos = cursor.fetchall()
        for curso in cursos:
            item = QListWidgetItem(curso[1])
            item.setData(1, curso[0])
            self.cursos_list.addItem(item)

        conn.close()
        self.alternar_instrutor()

    def alternar_instrutor(self):
        instrutor_id_anterior = self.instrutor_combo.itemData(self.instrutor_combo.currentIndex() - 1)
        instrutor_id_atual = self.instrutor_combo.currentData()

        if instrutor_id_anterior:
            cursos_selecionados = [item.data(1) for item in self.cursos_list.selectedItems()]
            self.selecao_temporaria[instrutor_id_anterior] = set(cursos_selecionados)

        for i in range(self.cursos_list.count()):
            self.cursos_list.item(i).setSelected(False)

        if instrutor_id_atual in self.selecao_temporaria:
            cursos_temporarios = self.selecao_temporaria[instrutor_id_atual]
            for i in range(self.cursos_list.count()):
                if self.cursos_list.item(i).data(1) in cursos_temporarios:
                    self.cursos_list.item(i).setSelected(True)
        else:
            self.carregar_cursos_associados(instrutor_id_atual)

    def carregar_cursos_associados(self, instrutor_id):
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("SELECT curso_id FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
        cursos_associados = {row[0] for row in cursor.fetchall()}
        conn.close()

        for i in range(self.cursos_list.count()):
            item = self.cursos_list.item(i)
            if item.data(1) in cursos_associados:
                item.setSelected(True)

    def associar_cursos(self):
        instrutor_id = self.instrutor_combo.currentData()
        cursos_selecionados = [item.data(1) for item in self.cursos_list.selectedItems()]

        if instrutor_id and cursos_selecionados:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
            for curso_id in cursos_selecionados:
                cursor.execute("INSERT INTO instrutores_cursos (instrutor_id, curso_id) VALUES (?, ?)",
                               (instrutor_id, curso_id))
            conn.commit()
            conn.close()

            self.selecao_temporaria[instrutor_id] = set(cursos_selecionados)
            QMessageBox.information(self, "Sucesso", "Cursos associados ao instrutor com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", "Selecione um instrutor e pelo menos um curso.")


class ExcluirInstrutorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("excluir.png"))
        self.setWindowTitle("Excluir Instrutor")
        self.setGeometry(300, 300, 400, 100)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Selecione o Instrutor para Excluir"))

        self.instrutor_combo = QComboBox()
        layout.addWidget(self.instrutor_combo)

        self.excluir_button = QPushButton("Excluir")
        self.excluir_button.clicked.connect(self.excluir_instrutor)
        layout.addWidget(self.excluir_button)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.clicked.connect(self.close)
        layout.addWidget(self.cancelar_button)

        self.setLayout(layout)
        self.carregar_instrutores()

    def carregar_instrutores(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            conn.close()

            self.instrutor_combo.clear()
            for instrutor in instrutores:
                self.instrutor_combo.addItem(instrutor[1], instrutor[0])

            if not instrutores:
                QMessageBox.warning(self, "Aviso", "Nenhum instrutor encontrado no banco de dados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao carregar instrutores: {str(e)}")

    def excluir_instrutor(self):
        try:
            instrutor_id = self.instrutor_combo.currentData()
            if not instrutor_id:
                QMessageBox.warning(self, "Aviso", "Nenhum instrutor selecionado para exclusão.")
                return

            # (Opcional) pega o nome para mostrar na confirmação
            nome_instrutor = self.instrutor_combo.currentText()

            resposta = QMessageBox.question(
                self,
                "Confirmação",
                f"Tem certeza de que deseja excluir o instrutor '{nome_instrutor}'?\n"
                "Isso removerá também:\n"
                "• Documentos anexados\n"
                "• Cursos associados\n"
                "• Programações (datas/horários) vinculadas\n\n"
                "Essa ação não pode ser desfeita.",
                QMessageBox.Yes | QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return

            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Segurança: faz tudo em transação
            cursor.execute("BEGIN")

            # 1) Apaga documentos do instrutor
            cursor.execute("DELETE FROM instrutores_documentos WHERE instrutor_id = ?", (instrutor_id,))

            # 2) Apaga programações (cursos_datas) onde ele está vinculado
            cursor.execute("DELETE FROM cursos_datas WHERE instrutor_id = ?", (instrutor_id,))

            # 3) Apaga associações com cursos
            cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))

            # 4) Apaga o instrutor
            cursor.execute("DELETE FROM instrutores WHERE id = ?", (instrutor_id,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso",
                                    "Instrutor excluído com sucesso (incluindo documentos e vínculos)!")
            self.carregar_instrutores()

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir instrutor: {str(e)}")


class CadastrarTemasSubtemasWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setWindowTitle("Cadastrar Temas e Subtemas")
        self.setGeometry(200, 200, 600, 540)
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # === ABA 1: Temas e Subtemas ===
        aba_temas = QWidget()
        aba_temas_layout = QVBoxLayout()

        aba_temas_layout.addWidget(QLabel("Gerenciar Temas"))

        tema_input_layout = QHBoxLayout()
        self.novo_tema_input = QLineEdit()
        self.novo_tema_input.setPlaceholderText("Novo tema...")
        self.novo_tema_input.setMinimumHeight(40)
        tema_input_layout.addWidget(self.novo_tema_input)

        self.btn_adicionar_tema = QPushButton("Adicionar Tema")
        self.btn_adicionar_tema.clicked.connect(self.adicionar_tema)
        self.btn_adicionar_tema.setMinimumHeight(40)
        tema_input_layout.addWidget(self.btn_adicionar_tema)

        aba_temas_layout.addLayout(tema_input_layout)

        self.lista_temas = QListWidget()
        self.lista_temas.setMinimumHeight(150)
        aba_temas_layout.addWidget(self.lista_temas, stretch=1)

        self.btn_excluir_tema = QPushButton("Excluir Tema Selecionado")
        self.btn_excluir_tema.clicked.connect(self.excluir_tema)

        self.btn_editar_tema = QPushButton("Editar Tema Selecionado")
        self.btn_editar_tema.clicked.connect(self.editar_tema)

        tema_btns_layout = QHBoxLayout()
        tema_btns_layout.addWidget(self.btn_excluir_tema)
        tema_btns_layout.addWidget(self.btn_editar_tema)
        aba_temas_layout.addLayout(tema_btns_layout)

        aba_temas_layout.addWidget(QLabel("Gerenciar Subtemas"))

        subtema_input_layout = QVBoxLayout()
        self.combo_tema_pai = QComboBox()
        self.carregar_temas_combo_pai()
        self.combo_tema_pai.setMinimumHeight(40)
        subtema_input_layout.addWidget(self.combo_tema_pai)

        self.novo_subtema_input = QLineEdit()
        self.novo_subtema_input.setPlaceholderText("Novo subtema...")
        self.novo_subtema_input.setMinimumHeight(40)
        subtema_input_layout.addWidget(self.novo_subtema_input)

        self.btn_adicionar_subtema = QPushButton("Adicionar Subtema")
        self.btn_adicionar_subtema.clicked.connect(self.adicionar_subtema)
        self.btn_adicionar_subtema.setMinimumHeight(40)
        subtema_input_layout.addWidget(self.btn_adicionar_subtema)

        aba_temas_layout.addLayout(subtema_input_layout)

        self.lista_subtemas = QListWidget()
        self.lista_subtemas.setMinimumHeight(150)
        aba_temas_layout.addWidget(self.lista_subtemas, stretch=1)

        self.btn_excluir_subtema = QPushButton("Excluir Subtema Selecionado")
        self.btn_excluir_subtema.clicked.connect(self.excluir_subtema)

        self.btn_editar_subtema = QPushButton("Editar Subtema Selecionado")
        self.btn_editar_subtema.clicked.connect(self.editar_subtema)

        subtema_btns_layout = QHBoxLayout()
        subtema_btns_layout.addWidget(self.btn_excluir_subtema)
        subtema_btns_layout.addWidget(self.btn_editar_subtema)
        aba_temas_layout.addLayout(subtema_btns_layout)

        aba_temas.setLayout(aba_temas_layout)
        self.tabs.addTab(aba_temas, "Temas e Subtemas")

        # === ABA 2: Associar Instrutores ===
        aba_instrutores = QWidget()
        aba_instrutores_layout = QVBoxLayout()

        aba_instrutores_layout.addWidget(QLabel("Selecione o Instrutor"))

        self.combo_instrutor = QComboBox()
        self.carregar_instrutores_combo()
        self.combo_instrutor.setMinimumHeight(40)
        aba_instrutores_layout.addWidget(self.combo_instrutor)

        aba_instrutores_layout.addWidget(QLabel("Selecione os Temas para associar"))

        self.lista_temas_assoc = QListWidget()
        self.lista_temas_assoc.setSelectionMode(QListWidget.MultiSelection)
        self.lista_temas_assoc.setMinimumHeight(250)
        aba_instrutores_layout.addWidget(self.lista_temas_assoc, stretch=1)

        self.btn_salvar_assoc = QPushButton("Salvar Associações")
        self.btn_salvar_assoc.clicked.connect(self.salvar_assoc_instrutor_tema)
        self.btn_salvar_assoc.setMinimumHeight(40)
        aba_instrutores_layout.addWidget(self.btn_salvar_assoc)

        aba_instrutores.setLayout(aba_instrutores_layout)
        self.tabs.addTab(aba_instrutores, "Associar Instrutores")

        self.setLayout(main_layout)

        self.combo_tema_pai.currentIndexChanged.connect(self.carregar_subtemas)
        self.combo_instrutor.currentIndexChanged.connect(self.on_instrutor_assoc_changed)

        self.carregar_lista_temas()
        self.carregar_temas_assoc()

    def carregar_temas_combo_pai(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()

            self.combo_tema_pai.clear()
            for tema in temas:
                self.combo_tema_pai.addItem(tema[1], tema[0])
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def carregar_temas_combo_instrutor(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()

            self.combo_tema_instrutor.clear()
            for tema in temas:
                self.combo_tema_instrutor.addItem(tema[1], tema[0])
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def carregar_lista_temas(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            temas = cursor.fetchall()
            conn.close()

            self.lista_temas.clear()
            for tema in temas:
                item = QListWidgetItem(tema[1])
                item.setData(Qt.UserRole, tema[0])
                self.lista_temas.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def adicionar_tema(self):
        nome = self.novo_tema_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Erro", "Digite o nome do tema.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO temas (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()

            self.novo_tema_input.clear()
            self.carregar_lista_temas()
            self.carregar_temas_combo_pai()
            QMessageBox.information(self, "Sucesso", f'Tema "{nome}" adicionado com sucesso!')
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um tema com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar tema:\n{str(e)}")

    def excluir_tema(self):
        item = self.lista_temas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione um tema para excluir.")
            return

        tema_id = item.data(Qt.UserRole)
        tema_nome = item.text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f'Tem certeza que deseja excluir o tema "{tema_nome}"?\n'
            "Todos os subtemas associados também serão excluídos.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM subtemas WHERE tema_id = ?", (tema_id,))
                cursor.execute("DELETE FROM temas WHERE id = ?", (tema_id,))
                conn.commit()
                conn.close()

                self.carregar_lista_temas()
                self.carregar_temas_combo_pai()
                QMessageBox.information(self, "Sucesso", "Tema excluído com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir tema:\n{str(e)}")

    def editar_tema(self):
        item = self.lista_temas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione um tema para editar.")
            return

        tema_id = item.data(Qt.UserRole)
        tema_atual = item.text()

        from PyQt5.QtWidgets import QInputDialog
        novo_nome, ok = QInputDialog.getText(self, "Editar Tema", "Nome do tema:", text=tema_atual)
        if not ok or not novo_nome.strip():
            return

        novo_nome = novo_nome.strip()
        if novo_nome == tema_atual:
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE temas SET nome = ? WHERE id = ?", (novo_nome, tema_id))
            conn.commit()
            conn.close()

            self.carregar_lista_temas()
            self.carregar_temas_combo_pai()
            self.carregar_temas_assoc()
            QMessageBox.information(self, "Sucesso", f'Tema renomeado para "{novo_nome}"!')
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um tema com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar tema:\n{str(e)}")

    def adicionar_subtema(self):
        if self.combo_tema_pai.count() == 0:
            QMessageBox.warning(self, "Erro", "Adicione um tema primeiro.")
            return

        tema_id = self.combo_tema_pai.currentData()
        nome = self.novo_subtema_input.text().strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "Digite o nome do subtema.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO subtemas (tema_id, nome) VALUES (?, ?)", (tema_id, nome))
            conn.commit()
            conn.close()

            self.novo_subtema_input.clear()
            self.carregar_subtemas()
            QMessageBox.information(self, "Sucesso", f'Subtema "{nome}" adicionado com sucesso!')
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao adicionar subtema:\n{str(e)}")

    def excluir_subtema(self):
        item = self.lista_subtemas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione um subtema para excluir.")
            return

        subtema_id = item.data(Qt.UserRole)
        subtema_nome = item.text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f'Tem certeza que deseja excluir o subtema "{subtema_nome}"?',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM subtemas WHERE id = ?", (subtema_id,))
                conn.commit()
                conn.close()

                self.carregar_subtemas()
                QMessageBox.information(self, "Sucesso", "Subtema excluído com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir subtema:\n{str(e)}")

    def editar_subtema(self):
        item = self.lista_subtemas.currentItem()
        if not item:
            QMessageBox.warning(self, "Erro", "Selecione um subtema para editar.")
            return

        subtema_id = item.data(Qt.UserRole)
        subtema_atual = item.text()

        from PyQt5.QtWidgets import QInputDialog
        novo_nome, ok = QInputDialog.getText(self, "Editar Subtema", "Nome do subtema:", text=subtema_atual)
        if not ok or not novo_nome.strip():
            return

        novo_nome = novo_nome.strip()
        if novo_nome == subtema_atual:
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE subtemas SET nome = ? WHERE id = ?", (novo_nome, subtema_id))
            conn.commit()
            conn.close()

            self.carregar_subtemas()
            QMessageBox.information(self, "Sucesso", f'Subtema renomeado para "{novo_nome}"!')
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar subtema:\n{str(e)}")

    def carregar_subtemas(self):
        self.lista_subtemas.clear()

        if self.combo_tema_pai.count() == 0:
            return

        tema_id = self.combo_tema_pai.currentData()

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM subtemas WHERE tema_id = ? ORDER BY nome ASC", (tema_id,))
            subtemas = cursor.fetchall()
            conn.close()

            for subtema in subtemas:
                item = QListWidgetItem(subtema[1])
                item.setData(Qt.UserRole, subtema[0])
                self.lista_subtemas.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar subtemas: {e}")

    def carregar_instrutores_combo(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            conn.close()

            self.combo_instrutor.clear()
            for instrutor in instrutores:
                self.combo_instrutor.addItem(instrutor[1], instrutor[0])
        except Exception as e:
            print(f"Erro ao carregar instrutores: {e}")

    def on_instrutor_assoc_changed(self):
        self.carregar_temas_assoc()

    def carregar_temas_assoc(self):
        instrutor_id = self.combo_instrutor.currentData()
        self.lista_temas_assoc.clear()

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("SELECT id, nome FROM temas ORDER BY nome ASC")
            todos_temas = cursor.fetchall()

            if instrutor_id:
                cursor.execute("SELECT tema_id FROM temas_instrutores WHERE instrutor_id = ?", (instrutor_id,))
                temas_associados = {row[0] for row in cursor.fetchall()}
            else:
                temas_associados = set()

            conn.close()

            for tema in todos_temas:
                item = QListWidgetItem(tema[1])
                item.setData(Qt.UserRole, tema[0])
                if tema[0] in temas_associados:
                    item.setSelected(True)
                self.lista_temas_assoc.addItem(item)
        except Exception as e:
            print(f"Erro ao carregar temas: {e}")

    def salvar_assoc_instrutor_tema(self):
        instrutor_id = self.combo_instrutor.currentData()
        if not instrutor_id:
            QMessageBox.warning(self, "Erro", "Selecione um instrutor.")
            return

        temas_selecionados = [item.data(Qt.UserRole) for item in self.lista_temas_assoc.selectedItems()]

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM temas_instrutores WHERE instrutor_id = ?", (instrutor_id,))
            for tema_id in temas_selecionados:
                cursor.execute("INSERT INTO temas_instrutores (tema_id, instrutor_id) VALUES (?, ?)",
                               (tema_id, instrutor_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Associações salvas com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar associações:\n{str(e)}")


class ConversorWorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    finished_processing = pyqtSignal(bool, str)

    def __init__(self, arquivo):
        super().__init__()
        self.arquivo = arquivo
        self.resultado_df = None
        self.sucesso = False
        self.mensagem = ""

    def run(self):
        try:
            self.update_progress.emit(10)
            df = self.processar_arquivo(self.arquivo)
            self.resultado_df = df
            self.update_progress.emit(100)
            self.sucesso = True
            self.mensagem = "Arquivo processado com sucesso!"
        except Exception as e:
            self.update_log.emit(f"Erro: {str(e)}")
            self.mensagem = f"Erro ao processar arquivo: {str(e)}"

        self.finished_processing.emit(self.sucesso, self.mensagem)

    def processar_arquivo(self, arquivo):
        with open(arquivo, 'rb') as f:
            result = chardet.detect(f.read())

        encoding = result['encoding']
        self.update_log.emit(f"Encoding detectado: {encoding}")
        self.update_progress.emit(20)

        extensao = os.path.splitext(arquivo)[1].lower()

        try:
            if extensao in ['.csv']:
                df = pd.read_csv(arquivo, encoding=encoding, dtype={'CPF': str})
            elif extensao in ['.xlsx', '.xls']:
                df = pd.read_excel(arquivo, dtype={'CPF': str})
            else:
                raise ValueError(f"Extensão não suportada: {extensao}")
        except Exception as e:
            raise Exception(f"Erro ao ler arquivo: {str(e)}")

        self.update_progress.emit(40)

        colunas = [col.strip() for col in df.columns]
        tipo_arquivo = self.identificar_tipo_planilha(colunas)

        if tipo_arquivo == "tipo1":
            self.update_log.emit("Planilha identificada como Tipo 1 (Nome, Sobrenome, Email, Check-in, CPF)")

            mapeamento = {}
            for col in df.columns:
                col_lower = col.lower().strip()
                if "nome" == col_lower and "sobrenome" not in col_lower:
                    mapeamento[col] = "Nome"
                elif "sobrenome" == col_lower:
                    mapeamento[col] = "Sobrenome"
                elif "email" == col_lower or "e-mail" == col_lower:
                    mapeamento[col] = "Email"
                elif "check" in col_lower:
                    mapeamento[col] = "Check-in"
                elif "cpf" == col_lower:
                    mapeamento[col] = "CPF"

            if mapeamento:
                df = df.rename(columns=mapeamento)

            colunas_faltantes = [col for col in ["Nome", "Sobrenome", "CPF"] if col not in df.columns]
            if colunas_faltantes:
                raise Exception(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")

            df['NOME / CPF'] = df['Nome'].astype(str) + ' ' + df['Sobrenome'].astype(str)

        elif tipo_arquivo == "tipo2":
            self.update_log.emit("Planilha identificada como Tipo 2 (NOME e CPF)")

            mapeamento = {}
            for col in df.columns:
                col_upper = col.upper().strip()
                if "NOME" == col_upper:
                    mapeamento[col] = "NOME"
                elif "CPF" == col_upper:
                    mapeamento[col] = "CPF"

            if mapeamento:
                df = df.rename(columns=mapeamento)

            colunas_faltantes = [col for col in ["NOME", "CPF"] if col not in df.columns]
            if colunas_faltantes:
                raise Exception(f"Colunas obrigatórias faltando: {', '.join(colunas_faltantes)}")

            df['NOME / CPF'] = df['NOME'].astype(str)

        else:
            raise Exception(
                "Formato de planilha não reconhecido. Necessário Tipo 1 (Nome, Sobrenome, Email, Check-in, CPF) ou Tipo 2 (NOME, CPF)")

        self.update_progress.emit(70)

        if "CPF" in df.columns:
            try:
                df["CPF"] = df["CPF"].astype(str).str.replace(r'\D', '', regex=True)
                df["CPF"] = df["CPF"].apply(lambda x: x.zfill(11) if x and x != 'nan' else x)
                self.update_log.emit("CPFs formatados com 11 dígitos (zeros à esquerda preservados)")
            except Exception as e:
                self.update_log.emit(f"Aviso: Não foi possível formatar a coluna CPF: {str(e)}")

        def remover_acentos(texto):
            if isinstance(texto, str):
                nfkd = unicodedata.normalize('NFKD', texto)
                return ''.join([c for c in nfkd if not unicodedata.combining(c)])
            return texto

        df['NOME / CPF'] = df['NOME / CPF'].apply(remover_acentos)

        if "CPF" in df.columns:
            df['NOME / CPF'] = df['NOME / CPF'].astype(str) + ',' + df['CPF'].astype(str)
        else:
            raise Exception("Coluna CPF não encontrada para montar NOME / CPF.")

        self.update_log.emit("Processamento finalizado. Pronto para salvar.")

        df_final = df[['NOME / CPF']]

        return df_final

    def identificar_tipo_planilha(self, colunas):
        colunas_lower = [col.lower() for col in colunas]
        colunas_upper = [col.upper() for col in colunas]
        colunas_original = [col for col in colunas]

        if ("nome" in colunas_lower and
                ("sobrenome" in colunas_lower) and
                any(col in colunas_lower for col in ["email", "e-mail"]) and
                any("check" in col.lower() for col in colunas_original) and
                "cpf" in colunas_lower):
            return "tipo1"

        elif "NOME" in colunas_upper and "CPF" in colunas_upper:
            return "tipo2"

        elif any("NOME" == col.upper() for col in colunas_original) and any(
                "CPF" == col.upper() for col in colunas_original):
            return "tipo2"

        elif any("nome" == col.lower() for col in colunas_original) and any(
                "cpf" == col.lower() for col in colunas_original):
            if any("sobrenome" == col.lower() for col in colunas_original):
                return "tipo1"
            else:
                return "tipo2"

        return "desconhecido"


class ConversorPlanilhasWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversor de Planilhas para CSV UTF-8 BOM")
        self.setGeometry(100, 100, 800, 600)
        self.arquivo_selecionado = ""
        self.inicializar_interface()

        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QLabel {
                font-size: 13px;
                color: #333333;
            }
        """)

    def inicializar_interface(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        titulo = QLabel("Conversor de Planilhas para CSV UTF-8 BOM")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #333333; margin-bottom: 15px;")
        layout_principal.addWidget(titulo)

        frame_selecao = QFrame()
        frame_selecao.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #dddddd; }")
        layout_selecao = QVBoxLayout(frame_selecao)

        label_selecao = QLabel("Selecione a planilha para conversão")
        label_selecao.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        layout_selecao.addWidget(label_selecao)

        info_tipos = QLabel("O programa detectará automaticamente se a planilha é:\n"
                            "• Tipo 1: Nome, Sobrenome, Email, Check-in, CPF\n"
                            "• Tipo 2: NOME, CPF")
        info_tipos.setStyleSheet("font-size: 14px; color: #555555;")
        layout_selecao.addWidget(info_tipos)

        layout_arquivo = QHBoxLayout()

        btn_selecionar = QPushButton("Selecionar Planilha")
        btn_selecionar.clicked.connect(self.selecionar_arquivo)
        btn_selecionar.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #3a76d8; }
            QPushButton:pressed { background-color: #2a66c8; }
        """)
        layout_arquivo.addWidget(btn_selecionar)

        self.txt_arquivo = QTextEdit()
        self.txt_arquivo.setReadOnly(True)
        self.txt_arquivo.setMaximumHeight(40)
        self.txt_arquivo.setPlaceholderText("Nenhum arquivo selecionado")
        layout_arquivo.addWidget(self.txt_arquivo)

        layout_selecao.addLayout(layout_arquivo)
        layout_principal.addWidget(frame_selecao)

        frame_processo = QFrame()
        frame_processo.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #dddddd; }")
        layout_processo = QVBoxLayout(frame_processo)

        btn_converter = QPushButton("Converter Planilha")
        btn_converter.clicked.connect(self.iniciar_processamento)
        btn_converter.setMinimumHeight(50)
        btn_converter.setStyleSheet("""
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #3a76d8; }
            QPushButton:pressed { background-color: #2a66c8; }
        """)
        layout_processo.addWidget(btn_converter)

        layout_processo.addWidget(QLabel("Progresso:"))
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dddddd;
                border-radius: 4px;
                text-align: center;
                height: 15px;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 3px;
            }
        """)
        layout_processo.addWidget(self.barra_progresso)

        layout_principal.addWidget(frame_processo)

        frame_log = QFrame()
        frame_log.setStyleSheet("QFrame { background-color: white; border-radius: 8px; border: 1px solid #dddddd; }")
        layout_log = QVBoxLayout(frame_log)

        label_log = QLabel("Log de Processamento")
        label_log.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        layout_log.addWidget(label_log)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
        """)
        layout_log.addWidget(self.txt_log)

        layout_principal.addWidget(frame_log)

    def selecionar_arquivo(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar Planilha", "",
                                                 "Planilhas (*.xlsx *.xls *.csv);;Todos os Arquivos (*)")

        if arquivo:
            self.arquivo_selecionado = arquivo
            self.txt_arquivo.clear()
            self.txt_arquivo.append(arquivo)
            self.adicionar_log(f"Arquivo selecionado: {os.path.basename(arquivo)}")

    def iniciar_processamento(self):
        if not self.arquivo_selecionado:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo selecionado!")
            return

        self.txt_log.clear()
        self.adicionar_log(f"Iniciando processamento do arquivo: {os.path.basename(self.arquivo_selecionado)}")
        self.barra_progresso.setValue(0)

        self.thread_worker = ConversorWorkerThread(self.arquivo_selecionado)
        self.thread_worker.update_progress.connect(self.atualizar_progresso)
        self.thread_worker.update_log.connect(self.adicionar_log)
        self.thread_worker.finished_processing.connect(self.processamento_concluido)
        self.thread_worker.start()

    def atualizar_progresso(self, valor):
        self.barra_progresso.setValue(valor)

    def adicionar_log(self, mensagem):
        hora = datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{hora}] {mensagem}")
        cursor = self.txt_log.textCursor()
        cursor.movePosition(cursor.End)
        self.txt_log.setTextCursor(cursor)

    def processamento_concluido(self, sucesso, mensagem):
        if sucesso:
            nome_sugerido = os.path.splitext(os.path.basename(self.arquivo_selecionado))[0] + "_processado.csv"

            caminho_saida, _ = QFileDialog.getSaveFileName(
                self,
                "Salvar Arquivo CSV",
                nome_sugerido,
                "Arquivos CSV (*.csv)"
            )

            if caminho_saida:
                try:
                    with codecs.open(caminho_saida, 'w', encoding='utf-8-sig') as f:
                        self.thread_worker.resultado_df.to_csv(f, index=False, sep=';')
                    QMessageBox.information(self, "Concluído", f"Arquivo salvo como:\n{caminho_saida}")
                    self.adicionar_log(f"Arquivo salvo como: {caminho_saida}")
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao Salvar", str(e))
                    self.adicionar_log(f"Erro ao salvar arquivo: {str(e)}")
            else:
                self.adicionar_log("Salvamento cancelado pelo usuário.")
        else:
            QMessageBox.warning(self, "Erro", mensagem)