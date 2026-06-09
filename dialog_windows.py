from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QMessageBox, QListWidget, QListWidgetItem,
    QComboBox, QTimeEdit, QHBoxLayout, QCalendarWidget, QHeaderView, QFileDialog, QTextEdit,
    QScrollArea
)
import sqlite3
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QTextCharFormat, QColor, QIcon
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
        self.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        layout.addWidget(self.instrutor_input)

        layout.addWidget(QLabel("CPF"))
        self.cpf_input = QLineEdit()
        self.cpf_input.setPlaceholderText("Digite apenas se quiser (ex: 123.456.789-00)")
        self.cpf_input.setClearButtonEnabled(True)
        self.cpf_input.setPlaceholderText("")  # campo começa vazio
        self.cpf_input.editingFinished.connect(self.validar_cpf_campo)
        layout.addWidget(self.cpf_input)

        layout.addWidget(QLabel("CNPJ (se houver)"))
        self.cnpj_input = QLineEdit()
        layout.addWidget(self.cnpj_input)

        layout.addWidget(QLabel("Nome da Empresa"))
        self.empresa_input = QLineEdit()
        layout.addWidget(self.empresa_input)

        layout.addWidget(QLabel("Nº Processo SEI"))
        self.processo_sei_input = QLineEdit()
        self.processo_sei_input.setPlaceholderText("Ex: 00000.000000/2024-11")
        layout.addWidget(self.processo_sei_input)

        layout.addWidget(QLabel("E-mail"))
        self.email_input = QLineEdit()
        layout.addWidget(self.email_input)

        layout.addWidget(QLabel("Telefone"))
        self.telefone_input = QLineEdit()
        self.telefone_input.setInputMask("(00) 9 0000-0000;_")
        self.telefone_input.setPlaceholderText("")  # começa vazio
        self.telefone_input.setClearButtonEnabled(True)
        self.telefone_input.editingFinished.connect(self.validar_telefone_campo)
        layout.addWidget(self.telefone_input)

        layout.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        niveis_formacao = ["Doutor", "Especialista", "Graduação", "Mestre"]
        for nivel in niveis_formacao:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        layout.addWidget(self.niveis_formacao_list)

        layout.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        modalidades = ["Presencial", "On-line", "Conteudista"]
        for modalidade in modalidades:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        layout.addWidget(self.modalidades_list)

        # ===== Documentos anexos =====
        layout.addWidget(QLabel("Documentos do Instrutor (PDF, Word, Imagens, etc.)"))
        self.docs_list = QListWidget()
        layout.addWidget(self.docs_list)

        btn_docs_layout = QHBoxLayout()
        self.btn_add_doc = QPushButton("Anexar documentos")
        self.btn_add_doc.clicked.connect(self.anexar_documentos)
        btn_docs_layout.addWidget(self.btn_add_doc)

        self.btn_rem_doc = QPushButton("Remover selecionado")
        self.btn_rem_doc.clicked.connect(self.remover_documento_selecionado)
        btn_docs_layout.addWidget(self.btn_rem_doc)

        layout.addLayout(btn_docs_layout)

        # Lista interna de caminhos selecionados
        self.documentos_paths = []


        self.add_button = QPushButton("Cadastrar")
        self.add_button.clicked.connect(self.cadastrar_instrutor)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

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
                (nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
            """, (
            nome,
            cpf_digits if cpf_digits else None,
            self.cnpj_input.text().strip() or None,
            self.empresa_input.text().strip() or None,
            self.processo_sei_input.text().strip() or None,
            self.email_input.text().strip() or None,
            tel_digits if tel_digits else None,
            ",".join(niveis_selecionados) if niveis_selecionados else None,
            ",".join(modalidades_selecionadas) if modalidades_selecionadas else None
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
            self.docs_list.clear()
            self.documentos_paths.clear()
            self.processo_sei_input.clear()


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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        scroll_layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        scroll_layout.addWidget(self.instrutor_input)
        scroll_layout.addWidget(QLabel("CPF"))
        self.cpf_input = QLineEdit()
        scroll_layout.addWidget(self.cpf_input)

        scroll_layout.addWidget(QLabel("CNPJ (se houver)"))
        self.cnpj_input = QLineEdit()
        scroll_layout.addWidget(self.cnpj_input)

        scroll_layout.addWidget(QLabel("Nome da Empresa"))
        self.empresa_input = QLineEdit()
        scroll_layout.addWidget(self.empresa_input)

        scroll_layout.addWidget(QLabel("Nº Processo SEI"))
        self.processo_sei_input = QLineEdit()
        scroll_layout.addWidget(self.processo_sei_input)

        scroll_layout.addWidget(QLabel("E-mail"))
        self.email_input = QLineEdit()
        scroll_layout.addWidget(self.email_input)

        scroll_layout.addWidget(QLabel("Telefone"))
        self.telefone_input = QLineEdit()
        scroll_layout.addWidget(self.telefone_input)

        scroll_layout.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        niveis_formacao = ["Doutor", "Especialista", "Graduação", "Mestre"]
        for nivel in niveis_formacao:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        scroll_layout.addWidget(self.niveis_formacao_list)

        scroll_layout.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        modalidades = ["Presencial", "On-line", "Conteudista"]
        for modalidade in modalidades:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        scroll_layout.addWidget(self.modalidades_list)

        scroll_layout.addWidget(QLabel("Cursos Associados"))
        self.cursos_list = QListWidget()
        self.cursos_list.setSelectionMode(QListWidget.MultiSelection)
        scroll_layout.addWidget(self.cursos_list)

        # ===== Documentos do Instrutor =====
        scroll_layout.addWidget(QLabel("Documentos do Instrutor"))

        self.docs_list = QListWidget()
        scroll_layout.addWidget(self.docs_list)

        docs_btns = QHBoxLayout()

        self.btn_add_doc = QPushButton("Adicionar documentos")
        self.btn_add_doc.clicked.connect(self.adicionar_documentos)
        docs_btns.addWidget(self.btn_add_doc)

        self.btn_del_doc = QPushButton("Excluir selecionado")
        self.btn_del_doc.clicked.connect(self.excluir_documento_selecionado)
        docs_btns.addWidget(self.btn_del_doc)

        scroll_layout.addLayout(docs_btns)

        # guarda paths novos (ainda não salvos)
        self.novos_documentos_paths = []

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

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
                SELECT nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades

                FROM instrutores
                WHERE id = ?
            """, (instrutor_id,))

            instrutor = cursor.fetchone()

            if instrutor:
                (nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades) = instrutor

                self.processo_sei_input.setText(processo_sei or "")
                self.instrutor_input.setText(nome)
                self.cpf_input.setText(cpf or "")
                self.cnpj_input.setText(cnpj or "")
                self.empresa_input.setText(empresa or "")
                self.email_input.setText(email or "")
                self.telefone_input.setText(telefone or "")

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
            modalidades = ?

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
            instrutor_id
        ))

        cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
        for curso_id in cursos_selecionados:
            cursor.execute("INSERT INTO instrutores_cursos (instrutor_id, curso_id) VALUES (?, ?)", (instrutor_id, curso_id))

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
        temas = ["Contabilidade", "Direito", "Especializações", "Ética",
                 "Ferramentas", "Gestão", "Recursos Humanos", "Tecnologia",
                 "Tributos e Obrigações Acessórias"]
        self.tema_combo.addItems(temas)
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
        self.descricao_input.setFixedHeight(120)  # opcional
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
        texto_corrigido = " ".join(self.curso_input.text().split()).strip()
        if self.curso_input.text() != texto_corrigido:
            self.curso_input.setText(texto_corrigido)

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

# Continua no próximo arquivo com as classes restantes...