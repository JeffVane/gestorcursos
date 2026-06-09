from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QCalendarWidget, QDialog, QMessageBox,
    QListWidget, QListWidgetItem, QMenu, QAction, QComboBox, QTimeEdit,
    QHBoxLayout, QHeaderView, QLineEdit, QFileDialog, QTabWidget, QCheckBox,
    QInputDialog, QPlainTextEdit, QSpinBox, QProgressDialog
)
import sqlite3
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QThread, QEventLoop
from PyQt5.QtGui import QTextCharFormat, QColor, QIcon
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit
from PyQt5.QtWidgets import QFormLayout, QGroupBox, QDialogButtonBox, QGridLayout, QTextEdit,QTimeEdit,QFrame
from PyQt5.QtGui import QIntValidator
import os
import tempfile
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import re
from urllib.parse import urlencode, parse_qs
import requests
from packaging.version import Version, InvalidVersion



import sys

# Importar classes das janelas de diálogo
from dialog_windows import (
    CadastroInstrutorWindow, EditarInstrutorWindow, CadastroCursoWindow,
    AssociarCursoWindow, ExcluirInstrutorWindow
)

# Importar funções do banco de dados
from database_utils import criar_banco, atualizar_banco


class ProgramarCursoWindow(QDialog):
    def __init__(self, data_selecionada, parent=None, curso_id=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("agenda.png"))
        self.setWindowTitle("Programar/Editar Curso")
        self.setGeometry(300, 300, 800, 500)

        self.data_selecionada = data_selecionada
        self.curso_programado_id = None

        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Data Selecionada: {self.data_selecionada}"))

        layout.addWidget(QLabel("Programações Existentes:"))
        self.programacoes_list = QListWidget()
        self.programacoes_list.itemClicked.connect(self.carregar_programacao)
        layout.addWidget(self.programacoes_list)

        self.form_widget = QWidget()
        form_layout = QVBoxLayout()

        form_layout.addWidget(QLabel("Selecione o Instrutor"))
        self.instrutor_combo = QComboBox()
        form_layout.addWidget(self.instrutor_combo)

        form_layout.addWidget(QLabel("Selecione o Curso"))
        self.curso_combo = QComboBox()
        form_layout.addWidget(self.curso_combo)

        form_layout.addWidget(QLabel("Selecione a Hora"))
        self.hora_input = QTimeEdit()
        self.hora_input.setDisplayFormat("HH:mm")
        form_layout.addWidget(self.hora_input)

        self.form_widget.setLayout(form_layout)
        layout.addWidget(self.form_widget)

        button_layout = QHBoxLayout()

        self.salvar_button = QPushButton("Salvar")
        self.salvar_button.clicked.connect(self.salvar_programacao)
        button_layout.addWidget(self.salvar_button)

        self.excluir_button = QPushButton("Excluir")
        self.excluir_button.clicked.connect(self.excluir_programacao)
        self.excluir_button.setEnabled(False)
        button_layout.addWidget(self.excluir_button)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancelar_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.carregar_instrutores()
        self.carregar_cursos()
        self.carregar_programacoes_existentes()

    def carregar_instrutores(self):
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome")
        instrutores = cursor.fetchall()
        conn.close()

        self.instrutor_combo.clear()
        for instrutor in instrutores:
            self.instrutor_combo.addItem(instrutor[1], instrutor[0])

    def carregar_cursos(self):
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM cursos ORDER BY nome")
        cursos = cursor.fetchall()
        conn.close()

        self.curso_combo.clear()
        for curso in cursos:
            self.curso_combo.addItem(curso[1], curso[0])

    def carregar_programacoes_existentes(self):
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                cursos_datas.id, cursos.nome as curso_nome,
                instrutores.nome as instrutor_nome, cursos_datas.hora
            FROM cursos_datas
            JOIN cursos ON cursos.id = cursos_datas.curso_id
            JOIN instrutores ON instrutores.id = cursos_datas.instrutor_id
            WHERE cursos_datas.data = ?
            ORDER BY cursos_datas.hora
        """, (self.data_selecionada,))
        programacoes = cursor.fetchall()
        conn.close()

        self.programacoes_list.clear()
        for prog_id, curso, instrutor, hora in programacoes:
            item = QListWidgetItem(f"{hora} - {curso} (Instrutor: {instrutor})")
            item.setData(Qt.UserRole, prog_id)
            self.programacoes_list.addItem(item)

    def carregar_programacao(self, item):
        self.curso_programado_id = item.data(Qt.UserRole)
        self.excluir_button.setEnabled(True)

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT curso_id, instrutor_id, hora FROM cursos_datas WHERE id = ?
        """, (self.curso_programado_id,))
        programacao = cursor.fetchone()
        conn.close()

        if programacao:
            curso_id, instrutor_id, hora = programacao

            index = self.curso_combo.findData(curso_id)
            if index >= 0:
                self.curso_combo.setCurrentIndex(index)

            index = self.instrutor_combo.findData(instrutor_id)
            if index >= 0:
                self.instrutor_combo.setCurrentIndex(index)

            hora_obj = QTime.fromString(hora, "HH:mm")
            self.hora_input.setTime(hora_obj)

    def salvar_programacao(self):
        curso_id = self.curso_combo.currentData()
        instrutor_id = self.instrutor_combo.currentData()  # <<< USA O SELECIONADO
        hora = self.hora_input.time().toString("HH:mm")

        if not curso_id:
            QMessageBox.warning(self, "Erro", "Selecione o curso.")
            return

        if not instrutor_id:
            QMessageBox.warning(self, "Erro", "Selecione o instrutor.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # (Opcional, mas recomendado) Validar se o instrutor está associado ao curso
            cursor.execute("""
                SELECT 1 FROM instrutores_cursos
                WHERE curso_id = ? AND instrutor_id = ?
                LIMIT 1
            """, (curso_id, instrutor_id))
            if not cursor.fetchone():
                QMessageBox.warning(self, "Erro", "Este instrutor não está associado ao curso selecionado.")
                conn.close()
                return

            if self.curso_programado_id:
                cursor.execute("""
                    UPDATE cursos_datas SET curso_id = ?, instrutor_id = ?, hora = ?
                    WHERE id = ?
                """, (curso_id, instrutor_id, hora, self.curso_programado_id))
                mensagem = "Programação atualizada com sucesso!"
            else:
                cursor.execute("""
                    INSERT INTO cursos_datas (curso_id, data, hora, instrutor_id)
                    VALUES (?, ?, ?, ?)
                """, (curso_id, self.data_selecionada, hora, instrutor_id))
                mensagem = "Curso programado com sucesso!"

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", mensagem)
            self.carregar_programacoes_existentes()
            self.curso_programado_id = None
            self.excluir_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao salvar programação: {str(e)}")

    def excluir_programacao(self):
        if not self.curso_programado_id:
            return

        resposta = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza que deseja excluir esta programação?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cursos_datas WHERE id = ?", (self.curso_programado_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Sucesso", "Programação excluída com sucesso!")
                self.carregar_programacoes_existentes()
                self.curso_programado_id = None
                self.excluir_button.setEnabled(False)

            except Exception as e:
                QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir programação: {str(e)}")

    def closeEvent(self, event):
        try:
            print("Fechando janela ProgramarCursoWindow...")
            event.accept()
        except Exception as e:
            print(f"Erro ao fechar janela: {e}")
            event.ignore()


class DetalhesInstrutorDialog(QDialog):
    def __init__(self, instrutor_id, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("informacoes.png"))
        self.setWindowTitle("Detalhes do Instrutor")
        self.setMinimumSize(760, 520)

        layout_principal = QVBoxLayout(self)

        # ===== Grupo: Identificação =====
        grp_id = QGroupBox("Identificação")
        grid_id = QGridLayout()

        self.txt_nome = QLineEdit(); self._ro(self.txt_nome)
        self.txt_cpf = QLineEdit(); self._ro(self.txt_cpf)
        self.txt_cnpj = QLineEdit(); self._ro(self.txt_cnpj)
        self.txt_empresa = QLineEdit(); self._ro(self.txt_empresa)
        self.txt_processo_sei = QLineEdit()
        self._ro(self.txt_processo_sei)

        grid_id.addWidget(QLabel("Nome"), 0, 0)
        grid_id.addWidget(self.txt_nome, 0, 1, 1, 3)

        grid_id.addWidget(QLabel("CPF"), 1, 0)
        grid_id.addWidget(self.txt_cpf, 1, 1)

        grid_id.addWidget(QLabel("CNPJ"), 1, 2)
        grid_id.addWidget(self.txt_cnpj, 1, 3)

        grid_id.addWidget(QLabel("Empresa"), 2, 0)
        grid_id.addWidget(self.txt_empresa, 2, 1, 1, 3)


        grid_id.addWidget(QLabel("Processo SEI"), 3, 0)
        grid_id.addWidget(self.txt_processo_sei, 3, 1, 1, 3)

        grp_id.setLayout(grid_id)
        layout_principal.addWidget(grp_id)

        # ===== Grupo: Contato =====
        grp_ct = QGroupBox("Contato")
        form_ct = QFormLayout()

        self.txt_email = QLineEdit(); self._ro(self.txt_email)
        self.txt_telefone = QLineEdit(); self._ro(self.txt_telefone)

        form_ct.addRow("E-mail", self.txt_email)
        form_ct.addRow("Telefone", self.txt_telefone)

        grp_ct.setLayout(form_ct)
        layout_principal.addWidget(grp_ct)

        # ===== Grupo: Perfil =====
        grp_pf = QGroupBox("Perfil")
        form_pf = QFormLayout()

        self.txt_niveis = QLineEdit(); self._ro(self.txt_niveis)
        self.txt_modalidades = QLineEdit(); self._ro(self.txt_modalidades)

        form_pf.addRow("Níveis de formação", self.txt_niveis)
        form_pf.addRow("Modalidades", self.txt_modalidades)

        grp_pf.setLayout(form_pf)
        layout_principal.addWidget(grp_pf)

        # ===== Grupo: Cursos =====
        grp_cs = QGroupBox("Cursos associados")
        v_cs = QVBoxLayout()

        self.txt_cursos = QTextEdit()
        self.txt_cursos.setReadOnly(True)
        self.txt_cursos.setMinimumHeight(120)

        v_cs.addWidget(self.txt_cursos)
        grp_cs.setLayout(v_cs)
        layout_principal.addWidget(grp_cs)

        # ===== Grupo: Documentos =====
        grp_docs = QGroupBox("Documentos do Instrutor")
        v_docs = QVBoxLayout()

        self.docs_list = QListWidget()
        self.docs_list.itemDoubleClicked.connect(self.abrir_documento)
        v_docs.addWidget(self.docs_list)

        self.docs_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.docs_list.customContextMenuRequested.connect(self.menu_documentos)

        grp_docs.setLayout(v_docs)
        layout_principal.addWidget(grp_docs)


        # ===== Botões =====
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttons.rejected.connect(self.close)
        layout_principal.addWidget(self.buttons)

        # Estilo leve e limpo
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cfcfcf;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            QLineEdit, QTextEdit {
                background: #ffffff;
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
            QLabel {
                color: #333;
                font-weight: normal;
            }
        """)

        self.carregar(instrutor_id)

    def _ro(self, w: QLineEdit):
        w.setReadOnly(True)

    def _v(self, s):
        return "" if s is None else str(s).strip()

    def carregar(self, instrutor_id):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis_formacao, modalidades

                FROM instrutores
                WHERE id = ?
            """, (instrutor_id,))
            dados = cursor.fetchone()

            cursor.execute("""
                SELECT cursos.nome
                FROM instrutores_cursos
                JOIN cursos ON cursos.id = instrutores_cursos.curso_id
                WHERE instrutores_cursos.instrutor_id = ?
                ORDER BY cursos.nome
            """, (instrutor_id,))
            cursos = [c[0] for c in cursor.fetchall()]

            conn.close()

            if not dados:
                QMessageBox.warning(self, "Aviso", "Instrutor não encontrado.")
                self.close()
                return

            nome, cpf, cnpj, empresa, processo_sei, email, telefone, niveis, modalidades = dados

            self.txt_processo_sei.setText(self._v(processo_sei))
            self.txt_nome.setText(self._v(nome))
            self.txt_cpf.setText(self._v(cpf))
            self.txt_cnpj.setText(self._v(cnpj))
            self.txt_empresa.setText(self._v(empresa))
            self.txt_email.setText(self._v(email))
            self.txt_telefone.setText(self._v(telefone))
            self.txt_niveis.setText(self._v(niveis))
            self.txt_modalidades.setText(self._v(modalidades))
            self.instrutor_id = instrutor_id
            self.carregar_documentos(instrutor_id)


            self.txt_cursos.setPlainText("\n".join(cursos) if cursos else "")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar detalhes:\n{str(e)}")
            self.close()


    def carregar_documentos(self, instrutor_id):
        self.docs_list.clear()
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

        for doc_id, nome, ext, mime in docs:
            item = QListWidgetItem(nome)
            item.setToolTip(f"{mime or ''} {ext or ''}".strip())
            item.setData(Qt.UserRole, doc_id)
            self.docs_list.addItem(item)

        if not docs:
            self.docs_list.addItem(QListWidgetItem("(Sem documentos anexados)"))
            self.docs_list.item(0).setFlags(Qt.NoItemFlags)

    def abrir_documento(self, item):
        doc_id = item.data(Qt.UserRole)
        if not doc_id:
            return

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nome_arquivo, extensao, conteudo
            FROM instrutores_documentos
            WHERE id = ?
        """, (doc_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            QMessageBox.warning(self, "Aviso", "Documento não encontrado no banco.")
            return

        nome, ext, blob = row
        ext = (ext or os.path.splitext(nome)[1] or "").lower()
        if not ext.startswith(".") and ext:
            ext = "." + ext

        # salva em arquivo temporário e abre no app padrão do sistema
        try:
            tmp_dir = tempfile.gettempdir()
            safe_name = nome.replace("/", "_").replace("\\", "_")
            tmp_path = os.path.join(tmp_dir, f"instrutor_doc_{doc_id}_{safe_name}")

            # garante extensão (ajuda o Windows a abrir no app correto)
            if ext and not tmp_path.lower().endswith(ext):
                tmp_path += ext

            with open(tmp_path, "wb") as f:
                f.write(blob)

            QDesktopServices.openUrl(QUrl.fromLocalFile(tmp_path))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o documento:\n{e}")

    def menu_documentos(self, pos):
        item = self.docs_list.itemAt(pos)
        if not item:
            return

        doc_id = item.data(Qt.UserRole)
        if not doc_id:
            return

        menu = QMenu(self)
        ac_excluir = QAction("🗑️ Excluir documento", self)
        ac_excluir.triggered.connect(lambda: self.excluir_documento(doc_id))
        menu.addAction(ac_excluir)

        menu.exec_(self.docs_list.mapToGlobal(pos))

    def excluir_documento(self, doc_id):
        resposta = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza que deseja excluir este documento?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM instrutores_documentos WHERE id = ?",
                (doc_id,)
            )
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Documento excluído com sucesso!")
            self.carregar_documentos(self.instrutor_id)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao excluir documento:\n{str(e)}")


class ExibirInstrutoresWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("informacoes.png"))
        self.setWindowTitle("Informações dos Instrutores")
        self.setGeometry(300, 300, 1100, 700)

        layout = QVBoxLayout()

        # ===== TABELA ENXUTA (SEM SCROLL HORIZONTAL) =====
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Nome", "Empresa", "Telefone", "E-mail"])
        self.tabela.horizontalHeader().setStretchLastSection(True)

        self.tabela.setColumnWidth(0, 280)
        self.tabela.setColumnWidth(1, 280)
        self.tabela.setColumnWidth(2, 160)
        self.tabela.setColumnWidth(3, 320)

        # duplo clique abre detalhes
        self.tabela.itemDoubleClicked.connect(self.abrir_detalhes)

        layout.addWidget(self.tabela)

        # botão opcional (caso você prefira clicar no botão)
        self.btn_detalhes = QPushButton("Ver Detalhes do Instrutor Selecionado")
        self.btn_detalhes.clicked.connect(self.abrir_detalhes_por_botao)
        layout.addWidget(self.btn_detalhes)

        self.setLayout(layout)
        self.carregar_instrutores()

    def carregar_instrutores(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, nome, empresa, telefone, email
                FROM instrutores
                ORDER BY nome ASC
            """)
            instrutores = cursor.fetchall()
            conn.close()

            self.tabela.setRowCount(len(instrutores))

            for row, (instrutor_id, nome, empresa, telefone, email) in enumerate(instrutores):
                item_nome = QTableWidgetItem(nome or "")
                item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
                item_nome.setData(Qt.UserRole, instrutor_id)  # guarda o ID aqui
                self.tabela.setItem(row, 0, item_nome)

                item_empresa = QTableWidgetItem(empresa or "")
                item_empresa.setFlags(item_empresa.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 1, item_empresa)

                item_tel = QTableWidgetItem(telefone or "")
                item_tel.setFlags(item_tel.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 2, item_tel)

                item_email = QTableWidgetItem(email or "")
                item_email.setFlags(item_email.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 3, item_email)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar instrutores: {str(e)}")

    def obter_instrutor_id_selecionado(self):
        row = self.tabela.currentRow()
        if row < 0:
            return None
        item_nome = self.tabela.item(row, 0)
        if not item_nome:
            return None
        return item_nome.data(Qt.UserRole)

    def abrir_detalhes(self, item):
        # chamado no duplo clique
        instrutor_id = item.data(Qt.UserRole) if item and item.column() == 0 else self.obter_instrutor_id_selecionado()
        if not instrutor_id:
            QMessageBox.warning(self, "Aviso", "Selecione um instrutor.")
            return
        DetalhesInstrutorDialog(instrutor_id, self).exec_()

    def abrir_detalhes_por_botao(self):
        instrutor_id = self.obter_instrutor_id_selecionado()
        if not instrutor_id:
            QMessageBox.warning(self, "Aviso", "Selecione um instrutor.")
            return
        DetalhesInstrutorDialog(instrutor_id, self).exec_()



class ExibirCursosWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("informacoes.png"))
        self.setWindowTitle("Cursos Cadastrados")
        self.setGeometry(250, 250, 1400, 700)

        layout = QVBoxLayout()

        # Barra de pesquisa
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Digite código EPC, curso, tema, descrição ou carga horária..."
        )
        self.search_input.textChanged.connect(self.aplicar_filtro)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels([
            "Código EPC",
            "Curso",
            "Tema",
            "Descrição",
            "Carga Horária"
        ])
        self.tabela.horizontalHeader().setStretchLastSection(True)

        # Ajuste de colunas
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # EPC
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Curso
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Tema
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Descrição
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Carga horária

        self.tabela.setWordWrap(False)
        self.tabela.verticalHeader().setDefaultSectionSize(28)

        self.tabela.itemDoubleClicked.connect(self.abrir_gerenciar_alunos)

        layout.addWidget(self.tabela)
        self.setLayout(layout)

        self.cursos_brutos = []
        self.carregar_cursos()

    def carregar_cursos(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Compatibilidade com bancos antigos
            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]

            tem_tema = "tema" in colunas
            tem_descricao = "descricao" in colunas
            tem_epc = "epc" in colunas
            tem_carga = "carga_horaria" in colunas

            select_cols = [
                "id",
                "epc" if tem_epc else "'' as epc",
                "nome",
                "tema" if tem_tema else "'' as tema",
                "descricao" if tem_descricao else "'' as descricao",
                "carga_horaria" if tem_carga else "'' as carga_horaria",
            ]

            cursor.execute(f"""
                SELECT {', '.join(select_cols)}
                FROM cursos
                ORDER BY nome ASC
            """)

            self.cursos_brutos = cursor.fetchall()
            conn.close()

            self.aplicar_filtro()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar cursos: {str(e)}")

    def aplicar_filtro(self):
        texto = (self.search_input.text() or "").strip().lower()

        if not texto:
            cursos_filtrados = self.cursos_brutos
        else:
            cursos_filtrados = []
            for row_data in self.cursos_brutos:
                curso_id = row_data[0]
                epc = row_data[1]
                nome = row_data[2]
                tema = row_data[3]
                descricao = row_data[4]
                carga_horaria = row_data[5]
                alvo = f"{epc or ''} {nome or ''} {tema or ''} {descricao or ''} {carga_horaria or ''}".lower()
                if texto in alvo:
                    cursos_filtrados.append(row_data)

        self.tabela.setRowCount(0)

        for row, row_data in enumerate(cursos_filtrados):
            curso_id = row_data[0]
            epc = row_data[1]
            nome = row_data[2]
            tema = row_data[3]
            descricao = row_data[4]
            carga_horaria = row_data[5]

            self.tabela.insertRow(row)

            item_epc = QTableWidgetItem(epc or "")
            item_epc.setFlags(item_epc.flags() & ~Qt.ItemIsEditable)
            item_epc.setData(Qt.UserRole, curso_id)

            item_nome = QTableWidgetItem(nome or "")
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)

            item_tema = QTableWidgetItem(tema or "")
            item_tema.setFlags(item_tema.flags() & ~Qt.ItemIsEditable)

            descricao_txt = (descricao or "").replace("\n", " ").replace("\r", " ").strip()
            if len(descricao_txt) > 120:
                descricao_txt = descricao_txt[:117] + "..."
            item_desc = QTableWidgetItem(descricao_txt)
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
            item_desc.setToolTip(descricao or "")

            ch_txt = "" if carga_horaria in (None, "") else f"{carga_horaria} h"
            item_carga = QTableWidgetItem(ch_txt)
            item_carga.setFlags(item_carga.flags() & ~Qt.ItemIsEditable)
            item_carga.setTextAlignment(Qt.AlignCenter)

            self.tabela.setItem(row, 0, item_epc)
            self.tabela.setItem(row, 1, item_nome)
            self.tabela.setItem(row, 2, item_tema)
            self.tabela.setItem(row, 3, item_desc)
            self.tabela.setItem(row, 4, item_carga)

        self.tabela.resizeRowsToContents()

    def abrir_gerenciar_alunos(self, item):
        row = item.row()
        item_epc = self.tabela.item(row, 0)
        curso_id = item_epc.data(Qt.UserRole) if item_epc else None
        nome_curso = self.tabela.item(row, 1).text() if self.tabela.item(row, 1) else ""
        if curso_id:
            janela = GerenciarAlunosWindow(curso_id, nome_curso, self)
            janela.exec_()

class GerenciarAlunosWindow(QDialog):
    def __init__(self, curso_id, nome_curso, parent=None):
        super().__init__(parent)
        self.curso_id = curso_id
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setWindowTitle(f"Alunos - {nome_curso}")
        self.setGeometry(200, 200, 1000, 600)

        layout = QVBoxLayout()

        # === Formulário de cadastro ===
        form_group = QGroupBox("Cadastrar Aluno")
        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("Nome:"), 0, 0)
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome do aluno")
        form_layout.addWidget(self.nome_input, 0, 1)

        form_layout.addWidget(QLabel("Faculdade/Universidade:"), 1, 0)
        self.faculdade_input = QLineEdit()
        self.faculdade_input.setPlaceholderText("Faculdade ou Universidade")
        form_layout.addWidget(self.faculdade_input, 1, 1)

        form_layout.addWidget(QLabel("Documento:"), 2, 0)
        doc_layout = QHBoxLayout()
        self.file_path_label = QLabel("Nenhum arquivo selecionado")
        self.file_path_label.setStyleSheet("color: #666;")
        doc_layout.addWidget(self.file_path_label)
        self.file_button = QPushButton("Selecionar Arquivo")
        self.file_button.clicked.connect(self.selecionar_arquivo)
        doc_layout.addWidget(self.file_button)
        form_layout.addLayout(doc_layout, 2, 1)

        self.cadastrar_button = QPushButton("Cadastrar Aluno")
        self.cadastrar_button.setObjectName("primaryButton")
        self.cadastrar_button.clicked.connect(self.cadastrar_aluno)
        form_layout.addWidget(self.cadastrar_button, 3, 1, Qt.AlignRight)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # === Tabela de alunos ===
        table_label = QLabel("Alunos Cadastrados")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4a90e2; padding: 8px 0;")
        layout.addWidget(table_label)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar:"))
        self.search_alunos_input = QLineEdit()
        self.search_alunos_input.setPlaceholderText("Digite nome, faculdade ou documento...")
        self.search_alunos_input.textChanged.connect(self.aplicar_filtro_alunos)
        search_layout.addWidget(self.search_alunos_input)
        layout.addLayout(search_layout)

        self.tabela_alunos = QTableWidget()
        self.tabela_alunos.setColumnCount(5)
        self.tabela_alunos.setHorizontalHeaderLabels([
            "ID", "Nome", "Faculdade/Universidade", "Documento", "Ações"
        ])
        header = self.tabela_alunos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabela_alunos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_alunos.verticalHeader().setVisible(False)
        layout.addWidget(self.tabela_alunos)

        self.arquivo_selecionado = None
        self.setLayout(layout)
        self.carregar_alunos()

    def selecionar_arquivo(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Documento", "",
            "Documentos (*.pdf *.xls *.xlsx *.doc *.docx *.png *.jpg *.jpeg *.bmp *.txt);;Todos (*.*)"
        )
        if arquivo:
            self.arquivo_selecionado = arquivo
            nome = os.path.basename(arquivo)
            self.file_path_label.setText(nome)
            self.file_path_label.setStyleSheet("color: #333;")

    def cadastrar_aluno(self):
        nome = self.nome_input.text().strip()
        faculdade = self.faculdade_input.text().strip()

        if not nome:
            QMessageBox.warning(self, "Erro", "Preencha o nome do aluno.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            if self.arquivo_selecionado:
                with open(self.arquivo_selecionado, "rb") as f:
                    conteudo = f.read()
                nome_arquivo = os.path.basename(self.arquivo_selecionado)
                ext = os.path.splitext(nome_arquivo)[1]
                cursor.execute("""
                    INSERT INTO alunos (curso_id, nome, faculdade, nome_arquivo, extensao, conteudo)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.curso_id, nome, faculdade, nome_arquivo, ext, conteudo))
            else:
                cursor.execute("""
                    INSERT INTO alunos (curso_id, nome, faculdade)
                    VALUES (?, ?, ?)
                """, (self.curso_id, nome, faculdade))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", f"Aluno '{nome}' cadastrado com sucesso!")
            self.nome_input.clear()
            self.faculdade_input.clear()
            self.file_path_label.setText("Nenhum arquivo selecionado")
            self.file_path_label.setStyleSheet("color: #666;")
            self.arquivo_selecionado = None
            self.carregar_alunos()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao cadastrar aluno: {str(e)}")

    def carregar_alunos(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, faculdade, nome_arquivo
                FROM alunos
                WHERE curso_id = ?
                ORDER BY nome ASC
            """, (self.curso_id,))
            self.alunos_dados = cursor.fetchall()
            conn.close()

            self.aplicar_filtro_alunos()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar alunos: {str(e)}")

    def aplicar_filtro_alunos(self):
        texto = self.search_alunos_input.text().strip().lower() if hasattr(self, 'search_alunos_input') else ""

        if not texto:
            filtrados = self.alunos_dados
        else:
            filtrados = []
            for aluno_id, nome, faculdade, nome_arquivo in self.alunos_dados:
                alvo = f"{nome or ''} {faculdade or ''} {nome_arquivo or ''}".lower()
                if texto in alvo:
                    filtrados.append((aluno_id, nome, faculdade, nome_arquivo))

        self.tabela_alunos.setRowCount(0)

        for row, (aluno_id, nome, faculdade, nome_arquivo) in enumerate(filtrados):
            self.tabela_alunos.insertRow(row)

            item_id = QTableWidgetItem(str(aluno_id))
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
            self.tabela_alunos.setItem(row, 0, item_id)

            item_nome = QTableWidgetItem(nome or "")
            item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)
            self.tabela_alunos.setItem(row, 1, item_nome)

            item_faculdade = QTableWidgetItem(faculdade or "")
            item_faculdade.setFlags(item_faculdade.flags() & ~Qt.ItemIsEditable)
            self.tabela_alunos.setItem(row, 2, item_faculdade)

            item_doc = QTableWidgetItem(nome_arquivo or "Sem documento")
            item_doc.setFlags(item_doc.flags() & ~Qt.ItemIsEditable)
            self.tabela_alunos.setItem(row, 3, item_doc)

            # Botão de ações
            btn_layout = QHBoxLayout()
            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)

            if nome_arquivo:
                btn_visualizar = QPushButton("Visualizar")
                btn_visualizar.setStyleSheet("padding: 4px 12px; font-size: 12px;")
                btn_visualizar.clicked.connect(lambda checked, aid=aluno_id: self.visualizar_documento(aid))
                btn_layout.addWidget(btn_visualizar)

            btn_editar = QPushButton("Editar")
            btn_editar.setStyleSheet("padding: 4px 12px; font-size: 12px; background-color: #f39c12;")
            btn_editar.clicked.connect(lambda checked, aid=aluno_id: self.editar_aluno(aid))
            btn_layout.addWidget(btn_editar)

            btn_excluir = QPushButton("Excluir")
            btn_excluir.setStyleSheet("padding: 4px 12px; font-size: 12px; background-color: #e74c3c;")
            btn_excluir.clicked.connect(lambda checked, aid=aluno_id, anome=nome: self.excluir_aluno(aid, anome))
            btn_layout.addWidget(btn_excluir)

            self.tabela_alunos.setCellWidget(row, 4, btn_widget)

        self.tabela_alunos.resizeRowsToContents()

    def visualizar_documento(self, aluno_id):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome_arquivo, extensao, conteudo
                FROM alunos
                WHERE id = ?
            """, (aluno_id,))
            row = cursor.fetchone()
            conn.close()

            if not row or not row[2]:
                QMessageBox.warning(self, "Aviso", "Este aluno não possui documento anexado.")
                return

            nome, ext, blob = row
            ext = (ext or os.path.splitext(nome)[1] or "").lower()
            if not ext.startswith(".") and ext:
                ext = "." + ext

            tmp_dir = tempfile.gettempdir()
            safe_name = nome.replace("/", "_").replace("\\", "_")
            tmp_path = os.path.join(tmp_dir, f"aluno_doc_{aluno_id}_{safe_name}")
            if ext and not tmp_path.lower().endswith(ext):
                tmp_path += ext

            with open(tmp_path, "wb") as f:
                f.write(blob)

            QDesktopServices.openUrl(QUrl.fromLocalFile(tmp_path))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o documento:\n{e}")

    def editar_aluno(self, aluno_id):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome, faculdade, nome_arquivo
                FROM alunos WHERE id = ?
            """, (aluno_id,))
            dados = cursor.fetchone()
            conn.close()

            if not dados:
                QMessageBox.warning(self, "Erro", "Aluno não encontrado.")
                return

            nome_atual, faculdade_atual, arquivo_atual = dados

            dialog = QDialog(self)
            dialog.setWindowTitle("Editar Aluno")
            dialog.setGeometry(300, 300, 500, 250)

            layout = QVBoxLayout(dialog)

            layout.addWidget(QLabel("Nome:"))
            nome_input = QLineEdit(nome_atual or "")
            layout.addWidget(nome_input)

            layout.addWidget(QLabel("Faculdade/Universidade:"))
            faculdade_input = QLineEdit(faculdade_atual or "")
            layout.addWidget(faculdade_input)

            layout.addWidget(QLabel("Documento:"))
            doc_layout = QHBoxLayout()
            file_label = QLabel(arquivo_atual or "Nenhum arquivo")
            file_label.setStyleSheet("color: #666;")
            doc_layout.addWidget(file_label)
            novo_arquivo = [None]

            def selecionar():
                arquivo, _ = QFileDialog.getOpenFileName(
                    dialog, "Selecionar Documento", "",
                    "Documentos (*.pdf *.xls *.xlsx *.doc *.docx *.png *.jpg *.jpeg *.bmp *.txt);;Todos (*.*)"
                )
                if arquivo:
                    novo_arquivo[0] = arquivo
                    file_label.setText(os.path.basename(arquivo))
                    file_label.setStyleSheet("color: #333;")

            btn_sel = QPushButton("Selecionar Arquivo")
            btn_sel.clicked.connect(selecionar)
            doc_layout.addWidget(btn_sel)
            layout.addLayout(doc_layout)

            btn_salvar = QPushButton("Salvar")
            btn_salvar.clicked.connect(lambda: self.salvar_edicao_aluno(
                aluno_id, nome_input.text().strip(),
                faculdade_input.text().strip(), novo_arquivo[0], dialog
            ))
            layout.addWidget(btn_salvar)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar aluno: {str(e)}")

    def salvar_edicao_aluno(self, aluno_id, nome, faculdade, arquivo_path, dialog):
        if not nome:
            QMessageBox.warning(self, "Erro", "Preencha o nome do aluno.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            if arquivo_path:
                with open(arquivo_path, "rb") as f:
                    conteudo = f.read()
                nome_arquivo = os.path.basename(arquivo_path)
                ext = os.path.splitext(nome_arquivo)[1]
                cursor.execute("""
                    UPDATE alunos
                    SET nome = ?, faculdade = ?, nome_arquivo = ?, extensao = ?, conteudo = ?
                    WHERE id = ?
                """, (nome, faculdade, nome_arquivo, ext, conteudo, aluno_id))
            else:
                cursor.execute("""
                    UPDATE alunos
                    SET nome = ?, faculdade = ?
                    WHERE id = ?
                """, (nome, faculdade, aluno_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Aluno atualizado com sucesso!")
            dialog.accept()
            self.carregar_alunos()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar edição: {str(e)}")

    def excluir_aluno(self, aluno_id, nome):
        resposta = QMessageBox.question(
            self, "Confirmação",
            f"Tem certeza que deseja excluir o aluno '{nome}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Aluno excluído com sucesso!")
                self.carregar_alunos()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir aluno: {str(e)}")


class HistoricoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Histórico de Cursos")
        self.setWindowIcon(QIcon("historico.png"))

        # 👉 HABILITA MAXIMIZAR / MINIMIZAR
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)

        # tamanho inicial (mas agora pode maximizar)
        self.resize(1400, 750)


        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_label = QLabel("Pesquisar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite EPC, curso, tema, descrição, carga horária ou instrutor...")
        self.search_input.textChanged.connect(self.aplicar_filtros)

        self.mes_combo = QComboBox()
        self.mes_combo.addItem("Todos os meses", None)
        for mes in range(1, 13):
            self.mes_combo.addItem(QDate.longMonthName(mes), mes)
        self.mes_combo.currentIndexChanged.connect(self.aplicar_filtros)

        self.ano_combo = QComboBox()
        self.ano_combo.addItem("Todos os anos", None)
        self.ano_combo.currentIndexChanged.connect(self.aplicar_filtros)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(QLabel("Filtrar por Mês:"))
        search_layout.addWidget(self.mes_combo)
        search_layout.addWidget(QLabel("Filtrar por Ano:"))
        search_layout.addWidget(self.ano_combo)

        layout.addLayout(search_layout)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(8)
        self.tabela.setHorizontalHeaderLabels([
            "Código EPC", "Curso", "Tema", "Descrição", "Carga Horária",
            "Instrutor", "Datas", "Horário"
        ])
        self.tabela.horizontalHeader().setStretchLastSection(True)

        # Larguras (ajuste fino se quiser)
        self.tabela.setColumnWidth(0, 120)  # EPC
        self.tabela.setColumnWidth(1, 280)  # Curso
        self.tabela.setColumnWidth(2, 160)  # Tema
        self.tabela.setColumnWidth(3, 420)  # Descrição
        self.tabela.setColumnWidth(4, 110)  # Carga horária
        self.tabela.setColumnWidth(5, 220)  # Instrutor
        self.tabela.setColumnWidth(6, 220)  # Datas
        self.tabela.setColumnWidth(7, 120)  # Horário

        layout.addWidget(self.tabela)

        self.exportar_pdf_button = QPushButton("Exportar para PDF")
        self.exportar_pdf_button.clicked.connect(self.exportar_para_pdf)
        layout.addWidget(self.exportar_pdf_button)

        self.setLayout(layout)
        self.carregar_historico()

    def carregar_historico(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Compatibilidade com bancos antigos
            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [c[1] for c in cursor.fetchall()]
            tem_tema = "tema" in colunas
            tem_descricao = "descricao" in colunas
            tem_epc = "epc" in colunas
            tem_carga = "carga_horaria" in colunas

            epc_sel = "cursos.epc" if tem_epc else "'' as epc"
            tema_sel = "cursos.tema" if tem_tema else "'' as tema"
            desc_sel = "cursos.descricao" if tem_descricao else "'' as descricao"
            carga_sel = "cursos.carga_horaria" if tem_carga else "'' as carga_horaria"

            cursor.execute(f"""
                SELECT
                    {epc_sel} AS epc,
                    cursos.nome AS curso_nome,
                    {tema_sel} AS tema,
                    {desc_sel} AS descricao,
                    {carga_sel} AS carga_horaria,
                    instrutores.nome AS instrutor_nome,
                    cursos_datas.data AS data,
                    cursos_datas.hora AS hora
                FROM cursos_datas
                JOIN cursos ON cursos.id = cursos_datas.curso_id
                JOIN instrutores ON instrutores.id = cursos_datas.instrutor_id
                ORDER BY curso_nome, instrutor_nome, data, hora
            """)

            historico = cursor.fetchall()
            conn.close()

            self.historico_bruto = historico

            # Popular anos disponíveis a partir do histórico
            anos = sorted({
                QDate.fromString(d, "yyyy-MM-dd").year()
                for *_, d, __ in [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in historico]
                if QDate.fromString(d, "yyyy-MM-dd").isValid()
            })

            self.ano_combo.blockSignals(True)
            self.ano_combo.clear()
            self.ano_combo.addItem("Todos os anos", None)
            for ano in anos:
                self.ano_combo.addItem(str(ano), ano)
            self.ano_combo.blockSignals(False)

            self.aplicar_filtros()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {str(e)}")

    def formatar_datas(self, datas_ordenadas):
        if not datas_ordenadas:
            return ""

        if len(datas_ordenadas) == 1:
            return datas_ordenadas[0].toString("dd/MM/yyyy")

        consecutivas = all(
            datas_ordenadas[i - 1].daysTo(datas_ordenadas[i]) == 1
            for i in range(1, len(datas_ordenadas))
        )

        if consecutivas:
            if len(datas_ordenadas) == 2:
                d1 = datas_ordenadas[0].toString("dd/MM/yyyy")
                d2 = datas_ordenadas[1].toString("dd/MM/yyyy")
                return f"{d1} e {d2}"
            else:
                di = datas_ordenadas[0].toString("dd/MM/yyyy")
                df = datas_ordenadas[-1].toString("dd/MM/yyyy")
                return f"{di} à {df}"

        return ", ".join(d.toString("dd/MM/yyyy") for d in datas_ordenadas)

    def aplicar_filtros(self):
        def norm(s: str) -> str:
            if s is None:
                return ""
            return " ".join(str(s).strip().split())

        texto_pesquisa = norm(self.search_input.text()).lower()
        mes_selecionado = self.mes_combo.currentData()
        ano_selecionado = self.ano_combo.currentData()

        registros = []
        for epc, curso, tema, descricao, carga, instrutor, data, hora in self.historico_bruto:
            epc_n = norm(epc)
            curso_n = norm(curso)
            tema_n = norm(tema)
            desc_n = norm(descricao)
            carga_n = norm(carga)
            instrutor_n = norm(instrutor)
            hora_n = norm(hora)

            data_qdate = QDate.fromString(data, "yyyy-MM-dd")
            if not data_qdate.isValid():
                continue

            if texto_pesquisa:
                alvo = f"{epc_n} {curso_n} {tema_n} {desc_n} {carga_n} {instrutor_n}".lower()
                if texto_pesquisa not in alvo:
                    continue

            if mes_selecionado is not None and data_qdate.month() != mes_selecionado:
                continue
            if ano_selecionado is not None and data_qdate.year() != ano_selecionado:
                continue

            registros.append((epc_n, curso_n, tema_n, desc_n, carga_n, instrutor_n, data_qdate, hora_n))

        # Agrupa por (epc, curso, instrutor) para manter consistência mesmo se curso repetir em versões
        grupos = {}
        for epc, curso, tema, desc, carga, instrutor, data_qdate, hora in registros:
            chave = (epc, curso, tema, desc, carga, instrutor)
            if chave not in grupos:
                grupos[chave] = {"datas": set(), "horas": set()}
            grupos[chave]["datas"].add(data_qdate)
            grupos[chave]["horas"].add(hora)

        agrupado = []
        for (epc, curso, tema, desc, carga, instrutor), info in grupos.items():
            datas_ordenadas = sorted(info["datas"], key=lambda d: d.toJulianDay())
            horas_ordenadas = sorted(info["horas"])

            datas_txt = self.formatar_datas(datas_ordenadas)
            horas_txt = ", ".join(horas_ordenadas)

            carga_txt = "" if not carga else f"{carga} h"
            agrupado.append((epc, curso, tema, desc, carga_txt, instrutor, datas_txt, horas_txt))

        agrupado.sort(key=lambda x: ((x[1] or "").lower(), (x[5] or "").lower()))

        self.tabela.setRowCount(0)
        for row, (epc, curso, tema, desc, carga_txt, instrutor, datas, horas) in enumerate(agrupado):
            self.tabela.insertRow(row)

            def item(txt, center=False):
                it = QTableWidgetItem(txt or "")
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if center:
                    it.setTextAlignment(Qt.AlignCenter)
                return it

            self.tabela.setItem(row, 0, item(epc))
            self.tabela.setItem(row, 1, item(curso))
            self.tabela.setItem(row, 2, item(tema))
            self.tabela.setItem(row, 3, item(desc))
            self.tabela.setItem(row, 4, item(carga_txt, center=True))
            self.tabela.setItem(row, 5, item(instrutor))
            self.tabela.setItem(row, 6, item(datas))
            self.tabela.setItem(row, 7, item(horas, center=True))

        self.tabela.resizeRowsToContents()

    def exportar_para_pdf(self):
        try:
            nome_arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
            if not nome_arquivo:
                return

            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            pdf = SimpleDocTemplate(
                nome_arquivo,
                pagesize=letter,
                leftMargin=18, rightMargin=18,
                topMargin=18, bottomMargin=18
            )

            elementos = []

            mes = self.mes_combo.currentText()
            ano = self.ano_combo.currentText()

            periodo = []
            if self.mes_combo.currentData() is not None:
                periodo.append(mes)
            if self.ano_combo.currentData() is not None:
                periodo.append(ano)

            texto_periodo = " - ".join(periodo) if periodo else "Todos os registros"

            styles = getSampleStyleSheet()
            cell = ParagraphStyle(
                "cell",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.6,
                leading=10.6,
                wordWrap="CJK",
                spaceAfter=0,
                spaceBefore=0,
            )
            head = ParagraphStyle(
                "head",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9.2,
                leading=11,
                alignment=1,
            )

            def P(txt, st=cell):
                txt = "" if txt is None else str(txt)
                txt = " ".join(txt.strip().split())
                return Paragraph(txt, st)

            t_periodo = Table([[P(f"Período: {texto_periodo}", ParagraphStyle(
                "periodo", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=12, alignment=1
            ))]], colWidths=[560])
            t_periodo.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elementos.append(t_periodo)
            elementos.append(Spacer(1, 6))

            # Cabeçalho
            headers = ["Código EPC", "Curso", "Tema", "Descrição", "CH", "Instrutor", "Datas", "Horário"]
            dados = [[P(h, head) for h in headers]]

            # Linhas
            for r in range(self.tabela.rowCount()):
                linha = []
                for c in range(self.tabela.columnCount()):
                    txt = self.tabela.item(r, c).text() if self.tabela.item(r, c) else ""
                    linha.append(P(txt))
                dados.append(linha)

            # Larguras (somam ~560)
            colWidths = [62, 110, 70, 150, 30, 95, 80, 45]

            tabela = Table(dados, colWidths=colWidths, repeatRows=1)
            tabela.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (4, 1), (4, -1), "CENTER"),  # CH
                ("ALIGN", (7, 1), (7, -1), "CENTER"),  # horário
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))

            elementos.append(tabela)
            pdf.build(elementos)

            QMessageBox.information(self, "Sucesso", "Histórico exportado para PDF com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")



class ExcluirCursoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("editar.png"))
        self.setWindowTitle("Editar ou Excluir Curso")
        self.resize(650, 520)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Selecione o Curso"))
        self.curso_combo = QComboBox()
        self.curso_combo.currentIndexChanged.connect(self.carregar_dados_curso)
        layout.addWidget(self.curso_combo)

        # ===== EPC =====
        layout.addWidget(QLabel("Editar Código EPC"))
        self.epc_input = QLineEdit()
        self.epc_input.setPlaceholderText("Ex: DF-123456")
        layout.addWidget(self.epc_input)

        # ===== Nome =====
        layout.addWidget(QLabel("Editar Nome do Curso"))
        self.curso_input = QLineEdit()
        layout.addWidget(self.curso_input)

        # ===== Tema =====
        layout.addWidget(QLabel("Editar Tema do Curso"))
        self.tema_combo = QComboBox()
        temas = [
            "Contabilidade", "Direito", "Especializações", "Ética",
            "Ferramentas", "Gestão", "Recursos Humanos", "Tecnologia",
            "Tributos e Obrigações Acessórias"
        ]
        self.tema_combo.addItems(temas)
        layout.addWidget(self.tema_combo)

        # ===== Descrição =====
        layout.addWidget(QLabel("Editar Descrição do Curso"))
        self.descricao_input = QTextEdit()
        self.descricao_input.setFixedHeight(140)
        layout.addWidget(self.descricao_input)

        # ===== Carga horária =====
        layout.addWidget(QLabel("Editar Carga Horária (em horas)"))
        self.carga_horaria_input = QLineEdit()
        self.carga_horaria_input.setValidator(QIntValidator(1, 10000))
        self.carga_horaria_input.setPlaceholderText("Ex: 40")
        layout.addWidget(self.carga_horaria_input)

        button_layout = QHBoxLayout()

        self.editar_button = QPushButton("Salvar Alterações")
        self.editar_button.clicked.connect(self.editar_curso)
        button_layout.addWidget(self.editar_button)

        self.excluir_button = QPushButton("Excluir Curso")
        self.excluir_button.clicked.connect(self.excluir_curso)
        button_layout.addWidget(self.excluir_button)

        layout.addLayout(button_layout)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.clicked.connect(self.close)
        layout.addWidget(self.cancelar_button)

        self.setLayout(layout)
        self.carregar_cursos()

    def carregar_cursos(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
            cursos = cursor.fetchall()
            conn.close()

            self.curso_combo.clear()
            for curso in cursos:
                self.curso_combo.addItem(curso[1], curso[0])

            if cursos:
                self.carregar_dados_curso()
            else:
                QMessageBox.warning(self, "Aviso", "Nenhum curso encontrado no banco de dados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao carregar cursos: {str(e)}")

    def carregar_dados_curso(self):
        curso_id = self.curso_combo.currentData()
        if not curso_id:
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Compatibilidade com bancos antigos
            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [c[1] for c in cursor.fetchall()]

            tem_epc = "epc" in colunas
            tem_tema = "tema" in colunas
            tem_descricao = "descricao" in colunas
            tem_carga = "carga_horaria" in colunas

            epc_sel = "epc" if tem_epc else "'' as epc"
            tema_sel = "tema" if tem_tema else "'' as tema"
            desc_sel = "descricao" if tem_descricao else "'' as descricao"
            carga_sel = "carga_horaria" if tem_carga else "'' as carga_horaria"

            cursor.execute(f"""
                SELECT nome, {tema_sel}, {desc_sel}, {epc_sel}, {carga_sel}
                FROM cursos
                WHERE id = ?
            """, (curso_id,))
            curso = cursor.fetchone()
            conn.close()

            if curso:
                nome, tema, descricao, epc, carga = curso

                self.curso_input.setText(nome or "")
                self.descricao_input.setPlainText(descricao or "")

                self.epc_input.setText((epc or "").strip())
                self.carga_horaria_input.setText("" if carga in (None, "") else str(carga))

                # Tema: tenta selecionar no combo
                tema_txt = (tema or "").strip()
                idx = self.tema_combo.findText(tema_txt)
                if idx >= 0:
                    self.tema_combo.setCurrentIndex(idx)
                else:
                    # se vier um tema antigo fora da lista, adiciona temporariamente
                    if tema_txt:
                        self.tema_combo.insertItem(0, tema_txt)
                        self.tema_combo.setCurrentIndex(0)
                    else:
                        self.tema_combo.setCurrentIndex(0)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados do curso: {str(e)}")

    def editar_curso(self):
        curso_id = self.curso_combo.currentData()
        novo_nome = self.curso_input.text().strip()
        novo_tema = self.tema_combo.currentText().strip()
        nova_descricao = self.descricao_input.toPlainText().strip()
        novo_epc = self.epc_input.text().strip().upper()
        carga_txt = self.carga_horaria_input.text().strip()

        if not curso_id or not novo_nome:
            QMessageBox.warning(self, "Erro", "Selecione um curso e insira um nome.")
            return

        # EPC opcional, mas se preenchido valida formato
        if novo_epc and not re.match(r"^[A-Z]{2}-\d{1,6}$", novo_epc):
            QMessageBox.warning(self, "Erro", "Código EPC inválido. Use o formato: DF-123456")
            self.epc_input.setFocus()
            self.epc_input.selectAll()
            return

        carga_val = None
        if carga_txt:
            try:
                carga_val = int(carga_txt)
                if carga_val <= 0:
                    raise ValueError("Carga horária deve ser maior que zero.")
            except Exception:
                QMessageBox.warning(self, "Erro", "Carga horária inválida. Informe um número inteiro (ex: 40).")
                self.carga_horaria_input.setFocus()
                self.carga_horaria_input.selectAll()
                return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Garantir colunas (compatibilidade)
            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [c[1] for c in cursor.fetchall()]

            if "tema" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN tema TEXT")
            if "descricao" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN descricao TEXT")
            if "epc" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN epc TEXT")
            if "carga_horaria" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN carga_horaria INTEGER")

            cursor.execute("""
                UPDATE cursos
                SET nome = ?, tema = ?, descricao = ?, epc = ?, carga_horaria = ?
                WHERE id = ?
            """, (novo_nome, novo_tema, nova_descricao,
                  (novo_epc if novo_epc else None),
                  carga_val,
                  curso_id))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Curso atualizado com sucesso!")
            self.carregar_cursos()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Erro", "Já existe um curso com esse nome.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar curso: {str(e)}")

    def excluir_curso(self):
        curso_id = self.curso_combo.currentData()
        if not curso_id:
            QMessageBox.warning(self, "Aviso", "Nenhum curso selecionado para exclusão.")
            return

        resposta = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza de que deseja excluir este curso?\n"
            "Isso removerá também:\n"
            "• Programações (datas/horários)\n"
            "• Associações com instrutores\n"
            "• Alunos cadastrados\n\n"
            "Essa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alunos WHERE curso_id = ?", (curso_id,))
                cursor.execute("DELETE FROM cursos_datas WHERE curso_id = ?", (curso_id,))
                cursor.execute("DELETE FROM instrutores_cursos WHERE curso_id = ?", (curso_id,))
                cursor.execute("DELETE FROM cursos WHERE id = ?", (curso_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Sucesso", "Curso excluído com sucesso!")
                self.carregar_cursos()

            except Exception as e:
                QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir curso: {str(e)}")



class EmailEditor(QTextEdit):
    edit_button_signal = pyqtSignal(str)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        cursor = self.cursorForPosition(event.pos())
        fmt = cursor.charFormat()

        if fmt.isAnchor() and fmt.anchorHref().startswith('btn://'):
            menu.addSeparator()
            edit_act = menu.addAction("✎ Editar Botão")
            edit_act.triggered.connect(
                lambda: self.edit_button_signal.emit('edit'))
            remove_act = menu.addAction("✖ Remover Botão")
            remove_act.triggered.connect(
                lambda: self.edit_button_signal.emit('remove'))

        menu.exec_(event.globalPos())


def _converter_botoes_para_html(html):
    def _substituir(m):
        qs = parse_qs(m.group(1))
        texto = qs.get('text', [''])[0]
        url = qs.get('url', [''])[0]
        cor = qs.get('color', ['#3498db'])[0]
        raio = qs.get('radius', ['8'])[0]
        pad_v = qs.get('pad_v', ['12'])[0]
        pad_h = qs.get('pad_h', ['24'])[0]
        align = qs.get('align', ['center'])[0]
        return (
            f'<div align="{align}">'
            f'<table cellpadding="0" cellspacing="0" style="display:inline-table;">'
            f'<tr><td style="background-color:{cor}; border-radius:{raio}px; '
            f'padding:{pad_v}px {pad_h}px;" align="center">'
            f'<a href="{url}" style="color:#ffffff; text-decoration:none; '
            f'font-weight:bold; font-size:14px; display:block;">{texto}</a>'
            f'</td></tr></table></div>'
        )
    return re.sub(
        r'href="btn://data\?(.+?)"(.*?)>(.*?)</a>',
        _substituir,
        html,
        flags=re.DOTALL
    )


def _converter_imagens_para_html(html, imagens, usar_cid=False):
    def _substituir(m):
        img_id = m.group(1)
        dados = imagens.get(img_id)
        if not dados:
            return ''
        px = dados['px']
        align = dados['align']
        if usar_cid:
            src = f"cid:img_{img_id}@gestorcursos"
        else:
            src = f"data:{dados['mime']};base64,{dados['b64']}"
        if align == "center":
            return f'<div align="center"><img src="{src}" width="{px}" style="max-width:100%; height:auto;"></div>'
        return f'<div align="{align}"><img src="{src}" width="{px}" style="max-width:100%; height:auto;"></div>'
    return re.sub(
        r'_IMG_(\d+)_(\d+)_(left|center|right)_',
        _substituir,
        html
    )


class SendEmailThread(QThread):
    log_message = pyqtSignal(str)
    progress = pyqtSignal(int, int)
    error_smtp = pyqtSignal(str)
    finished_send = pyqtSignal(int, list)

    def __init__(self, emails, assunto, html_corpo, variaveis,
                 instrutor_empresa, smtp_host, smtp_port, smtp_user,
                 smtp_password, smtp_from_name, smtp_use_tls,
                 imagens, intervalo):
        super().__init__()
        self.emails = emails
        self.assunto = assunto
        self.html_corpo = html_corpo
        self.variaveis = variaveis
        self.instrutor_empresa = instrutor_empresa
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from_name = smtp_from_name
        self.smtp_use_tls = smtp_use_tls
        self.imagens = imagens
        self.intervalo = intervalo

    def run(self):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.image import MIMEImage
        import base64

        enviados = 0
        erros = []

        try:
            server = smtplib.SMTP(self.smtp_host, int(self.smtp_port), timeout=30)
            if self.smtp_use_tls:
                server.starttls()
            server.login(self.smtp_user, self.smtp_password)

            from_name = self.smtp_from_name or self.smtp_user

            for i, email in enumerate(self.emails):
                corpo_personalizado = self.html_corpo
                for var, valor in self.variaveis.items():
                    corpo_personalizado = corpo_personalizado.replace(var, valor)
                corpo_personalizado = corpo_personalizado.replace("{{nome_aluno}}", "")
                corpo_personalizado = corpo_personalizado.replace("{{empresa_instrutor}}", self.instrutor_empresa or "")
                corpo_personalizado = _converter_botoes_para_html(corpo_personalizado)
                corpo_personalizado = _converter_imagens_para_html(corpo_personalizado, self.imagens, usar_cid=True)
                corpo_personalizado = re.sub(
                    r'<html[^>]*>|<head>.*?</head>|<body[^>]*>|</html>|</body>',
                    '', corpo_personalizado, flags=re.DOTALL
                ).strip()

                email_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background:#f4f4f4;">
<div style="max-width:750px; margin:0 auto; background:#ffffff; font-family:'Segoe UI',Arial,sans-serif;">
<div style="padding:24px; font-size:14px; line-height:1.7; color:#333;">
{corpo_personalizado}
</div></div></body></html>"""

                msg_related = MIMEMultipart('related', type='text/html')
                msg_alternative = MIMEMultipart('alternative')
                msg_alternative.attach(MIMEText(email_html, 'html', 'utf-8'))
                msg_related.attach(msg_alternative)

                for img_id_str, img_data in self.imagens.items():
                    img_bytes = base64.b64decode(img_data['b64'])
                    sub_type = img_data['mime'].split('/')[-1]
                    img_part = MIMEImage(img_bytes, _subtype=sub_type)
                    img_part.add_header('Content-ID', f"<img_{img_id_str}@gestorcursos>")
                    img_part['Content-Disposition'] = 'inline'
                    msg_related.attach(img_part)

                msg_related['From'] = f"{from_name} <{self.smtp_user}>"
                msg_related['To'] = email
                msg_related['Subject'] = self.assunto

                try:
                    server.send_message(msg_related)
                    enviados += 1
                except Exception as e:
                    erros.append(f"{email}: {str(e)}")

                self.progress.emit(i + 1, len(self.emails))
                self.log_message.emit(f"Enviado {i+1}/{len(self.emails)}: {email}")

                delay = self.intervalo
                if delay > 0 and email != self.emails[-1]:
                    self.log_message.emit(f"Aguardando {delay}s...")
                    for _ in range(delay):
                        self.msleep(1000)

            server.quit()

        except Exception as e:
            self.error_smtp.emit(str(e))
            self.finished_send.emit(enviados, erros)
            return

        self.log_message.emit(f"Concluído. Enviados: {enviados}")
        if self.imagens:
            self.log_message.emit(f"Imagens anexadas via CID: {len(self.imagens)}")
        if erros:
            self.log_message.emit(f"Erros: {len(erros)}")
            for e in erros[:5]:
                self.log_message.emit(f"  Erro: {e}")

        self.finished_send.emit(enviados, erros)


class DetalhesProgramacaoWindow(QDialog):
    def __init__(self, prog_id, curso_id, data, parent=None):
        super().__init__(parent)
        self.prog_id = prog_id
        self.curso_id = curso_id
        self.data = data
        self._imagens = {}
        self._img_counter = 0
        self._template_atual = None
        self._template_modificado = False
        self.setWindowIcon(QIcon("agenda.png"))
        self.setWindowTitle("Detalhes da Programação")
        self.setGeometry(250, 250, 1100, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

        layout = QVBoxLayout()

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # === Aba 1: Editar Programação ===
        self.tab_editar = QWidget()
        self.setup_tab_editar()
        self.tabs.addTab(self.tab_editar, "Editar Programação")

        # === Aba 2: Alunos ===
        self.tab_alunos = QWidget()
        self.setup_tab_alunos()
        self.tabs.addTab(self.tab_alunos, "Alunos")

        # === Aba 3: Enviar Emails ===
        self.tab_emails = QWidget()
        self.setup_tab_emails()
        self.tabs.addTab(self.tab_emails, "Enviar Emails")

        # === Aba 4: Logs ===
        self.tab_logs = QWidget()
        self.setup_tab_logs()
        self.tabs.addTab(self.tab_logs, "Logs")

        self.setLayout(layout)
        self.carregar_dados()

    def setup_tab_editar(self):
        layout = QVBoxLayout()

        edit_group = QGroupBox("Editar Programação")
        edit_layout = QGridLayout()

        edit_layout.addWidget(QLabel("Curso:"), 0, 0)
        self.curso_combo = QComboBox()
        edit_layout.addWidget(self.curso_combo, 0, 1)

        edit_layout.addWidget(QLabel("Instrutor:"), 1, 0)
        self.instrutor_combo = QComboBox()
        edit_layout.addWidget(self.instrutor_combo, 1, 1)

        edit_layout.addWidget(QLabel("Hora:"), 2, 0)
        self.hora_input = QTimeEdit()
        self.hora_input.setDisplayFormat("HH:mm")
        edit_layout.addWidget(self.hora_input, 2, 1)

        btn_edit_layout = QHBoxLayout()
        self.salvar_button = QPushButton("Salvar Alterações")
        self.salvar_button.clicked.connect(self.salvar_programacao)
        btn_edit_layout.addWidget(self.salvar_button)

        self.excluir_button = QPushButton("Excluir Programação")
        self.excluir_button.setStyleSheet("background-color: #e74c3c;")
        self.excluir_button.clicked.connect(self.excluir_programacao)
        btn_edit_layout.addWidget(self.excluir_button)

        edit_layout.addLayout(btn_edit_layout, 3, 0, 1, 2)
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)

        layout.addStretch()
        self.tab_editar.setLayout(layout)

    def setup_tab_alunos(self):
        layout = QVBoxLayout()

        alunos_group = QGroupBox("Alunos deste Curso")
        alunos_layout = QVBoxLayout()

        btn_alunos = QPushButton("Gerenciar Alunos")
        btn_alunos.setStyleSheet("padding: 6px 16px; font-size: 12px; min-height: 28px;")
        btn_alunos.setFixedWidth(200)
        btn_alunos.clicked.connect(self.abrir_gerenciar_alunos)
        alunos_layout.addWidget(btn_alunos)

        self.alunos_resumo = QLabel("Carregando...")
        self.alunos_resumo.setStyleSheet("color: #666; padding: 8px;")
        alunos_layout.addWidget(self.alunos_resumo)

        alunos_group.setLayout(alunos_layout)
        layout.addWidget(alunos_group)

        layout.addStretch()
        self.tab_alunos.setLayout(layout)

    def _criar_toolbar(self, editor):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        btn_bold = QPushButton("B")
        btn_bold.setFixedSize(26, 26)
        btn_bold.setToolTip("Negrito")
        btn_bold.setStyleSheet("font-weight: bold; font-size: 13px; padding: 0;")
        btn_bold.clicked.connect(lambda: self._format_text(editor, "bold"))
        toolbar.addWidget(btn_bold)

        btn_italic = QPushButton("I")
        btn_italic.setFixedSize(26, 26)
        btn_italic.setToolTip("Itálico")
        btn_italic.setStyleSheet("font-style: italic; font-size: 13px; padding: 0;")
        btn_italic.clicked.connect(lambda: self._format_text(editor, "italic"))
        toolbar.addWidget(btn_italic)

        btn_underline = QPushButton("U")
        btn_underline.setFixedSize(26, 26)
        btn_underline.setToolTip("Sublinhado")
        btn_underline.setStyleSheet("text-decoration: underline; font-size: 13px; padding: 0;")
        btn_underline.clicked.connect(lambda: self._format_text(editor, "underline"))
        toolbar.addWidget(btn_underline)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFixedWidth(1)
        toolbar.addWidget(sep1)

        heading_combo = QComboBox()
        heading_combo.setFixedHeight(26)
        heading_combo.setMinimumWidth(80)
        heading_combo.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        heading_combo.addItems(["Normal", "H1", "H2", "H3"])
        heading_combo.currentTextChanged.connect(
            lambda t: self._format_heading(editor, {"Normal": 0, "H1": 1, "H2": 2, "H3": 3}.get(t, 0))
        )
        toolbar.addWidget(heading_combo)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFixedWidth(1)
        toolbar.addWidget(sep2)

        btn_align_left = QPushButton("≡")
        btn_align_left.setFixedSize(26, 26)
        btn_align_left.setToolTip("Alinhar à Esquerda")
        btn_align_left.setStyleSheet("font-size: 13px; padding: 0;")
        btn_align_left.clicked.connect(lambda: self._format_align(editor, "left"))
        toolbar.addWidget(btn_align_left)

        btn_align_center = QPushButton("≡")
        btn_align_center.setFixedSize(26, 26)
        btn_align_center.setToolTip("Centralizar")
        btn_align_center.setStyleSheet("font-size: 13px; padding: 0;")
        btn_align_center.clicked.connect(lambda: self._format_align(editor, "center"))
        toolbar.addWidget(btn_align_center)

        btn_align_right = QPushButton("≡")
        btn_align_right.setFixedSize(26, 26)
        btn_align_right.setToolTip("Alinhar à Direita")
        btn_align_right.setStyleSheet("font-size: 13px; padding: 0;")
        btn_align_right.clicked.connect(lambda: self._format_align(editor, "right"))
        toolbar.addWidget(btn_align_right)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFixedWidth(1)
        toolbar.addWidget(sep3)

        btn_color = QPushButton("A")
        btn_color.setFixedSize(26, 26)
        btn_color.setToolTip("Cor da Fonte")
        btn_color.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 0; color: #e74c3c; background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; } QPushButton:hover { background: #e0e0e0; }")
        btn_color.clicked.connect(lambda: self._escolher_cor(editor))
        toolbar.addWidget(btn_color)

        btn_bg = QPushButton("■")
        btn_bg.setFixedSize(26, 26)
        btn_bg.setToolTip("Cor de Fundo (Realçar)")
        btn_bg.setStyleSheet("QPushButton { font-size: 16px; padding: 0; color: #f1c40f; background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; } QPushButton:hover { background: #e0e0e0; }")
        btn_bg.clicked.connect(lambda: self._escolher_cor_fundo(editor))
        toolbar.addWidget(btn_bg)

        sep4 = QFrame()
        sep4.setFrameShape(QFrame.VLine)
        sep4.setFixedWidth(1)
        toolbar.addWidget(sep4)

        btn_bullet = QPushButton("•")
        btn_bullet.setFixedSize(26, 26)
        btn_bullet.setToolTip("Lista com Marcadores")
        btn_bullet.setStyleSheet("font-size: 14px; padding: 0;")
        btn_bullet.clicked.connect(lambda: self._insert_list(editor, "bullet"))
        toolbar.addWidget(btn_bullet)

        btn_numbered = QPushButton("1.")
        btn_numbered.setFixedSize(26, 26)
        btn_numbered.setToolTip("Lista Numerada")
        btn_numbered.setStyleSheet("font-size: 12px; padding: 0;")
        btn_numbered.clicked.connect(lambda: self._insert_list(editor, "numbered"))
        toolbar.addWidget(btn_numbered)

        sep5 = QFrame()
        sep5.setFrameShape(QFrame.VLine)
        sep5.setFixedWidth(1)
        toolbar.addWidget(sep5)

        btn_link = QPushButton("🔗")
        btn_link.setFixedSize(28, 26)
        btn_link.setToolTip("Inserir Link")
        btn_link.setStyleSheet("font-size: 12px; padding: 0;")
        btn_link.clicked.connect(lambda: self._inserir_link(editor))
        toolbar.addWidget(btn_link)

        btn_image = QPushButton("🖼")
        btn_image.setFixedSize(28, 26)
        btn_image.setToolTip("Inserir Imagem")
        btn_image.setStyleSheet("font-size: 12px; padding: 0;")
        btn_image.clicked.connect(lambda: self._inserir_imagem(editor))
        toolbar.addWidget(btn_image)

        btn_button = QPushButton("▣")
        btn_button.setFixedSize(26, 26)
        btn_button.setToolTip("Inserir Botão")
        btn_button.setStyleSheet("font-size: 13px; padding: 0;")
        btn_button.clicked.connect(lambda: self._inserir_botao(editor))
        toolbar.addWidget(btn_button)

        sep6 = QFrame()
        sep6.setFrameShape(QFrame.VLine)
        sep6.setFixedWidth(1)
        toolbar.addWidget(sep6)

        variaveis_combo = QComboBox()
        variaveis_combo.setFixedHeight(26)
        variaveis_combo.setMinimumWidth(140)
        variaveis_combo.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        variaveis_combo.addItem("Inserir Variável...")
        variaveis_combo.addItems([
            "{{nome_curso}}", "{{data_curso}}", "{{hora_curso}}",
            "{{nome_instrutor}}", "{{carga_horaria}}", "{{tema_curso}}",
        ])
        variaveis_combo.currentIndexChanged.connect(lambda idx, e=editor, v=variaveis_combo: self._inserir_variavel(e, v, idx))
        toolbar.addWidget(variaveis_combo)

        toolbar.addStretch()
        return toolbar

    def _secao_email(self, titulo, editor, min_height=80):
        group = QGroupBox(titulo)
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(2)
        toolbar = self._criar_toolbar(editor)
        layout.addLayout(toolbar)
        editor.setMinimumHeight(min_height)
        editor.textChanged.connect(self.atualizar_previa)
        editor.textChanged.connect(self._marcar_template_modificado)
        editor.edit_button_signal.connect(lambda act, e=editor: self._acao_botao_context_menu(e, act))
        layout.addWidget(editor)
        return group

    def _editor_atual(self):
        for e in [self.email_cabecalho, self.email_corpo, self.email_rodape]:
            if e.hasFocus():
                return e
        return self.email_corpo

    def setup_tab_emails(self):
        layout = QHBoxLayout()

        # Painel esquerdo: Editor
        editor_panel = QWidget()
        editor_layout = QVBoxLayout()
        editor_panel.setLayout(editor_layout)

        # Assunto
        editor_layout.addWidget(QLabel("Assunto:"))
        self.email_assunto = QLineEdit()
        self.email_assunto.setPlaceholderText("Ex: Lembrete - Curso amanhã às 08:00")
        self.email_assunto.textChanged.connect(self._marcar_template_modificado)
        editor_layout.addWidget(self.email_assunto)

        # Emails (campo para colar emails)
        editor_layout.addWidget(QLabel("Emails dos Destinatários (um por linha ou separados por vírgula/ponto e vírgula):"))
        self.email_destinatarios = QTextEdit()
        self.email_destinatarios.setPlaceholderText("exemplo@email.com\noutro@email.com\nterceiro@email.com")
        self.email_destinatarios.setMaximumHeight(60)
        self.email_destinatarios.setStyleSheet("font-family: monospace; font-size: 11px;")
        editor_layout.addWidget(self.email_destinatarios)

        # Seções do email
        self.email_cabecalho = EmailEditor()
        self.email_cabecalho.setPlaceholderText("Cabeçalho do email...")
        editor_layout.addWidget(self._secao_email("Cabeçalho", self.email_cabecalho, 80))

        self.email_corpo = EmailEditor()
        self.email_corpo.setPlaceholderText("Corpo principal do email...")
        editor_layout.addWidget(self._secao_email("Corpo Principal", self.email_corpo, 150))

        self.email_rodape = EmailEditor()
        self.email_rodape.setPlaceholderText("Rodapé do email...")
        editor_layout.addWidget(self._secao_email("Rodapé", self.email_rodape, 80))

        # Botões de ação (na horizontal)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        btn_previa = QPushButton("👁 Prévia")
        btn_previa.setFixedHeight(28)
        btn_previa.setStyleSheet("padding: 4px 12px; font-size: 12px;")
        btn_previa.clicked.connect(self.atualizar_previa)
        btn_layout.addWidget(btn_previa)

        btn_limpar = QPushButton("🗑 Limpar")
        btn_limpar.setFixedHeight(28)
        btn_limpar.setStyleSheet("padding: 4px 12px; font-size: 12px;")
        btn_limpar.clicked.connect(self.limpar_editor)
        btn_layout.addWidget(btn_limpar)

        # Templates
        btn_salvar_template = QPushButton("💾 Salvar")
        btn_salvar_template.setFixedHeight(28)
        btn_salvar_template.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        btn_salvar_template.clicked.connect(self.salvar_template)
        btn_layout.addWidget(btn_salvar_template)

        btn_carregar_template = QPushButton("📁 Carregar")
        btn_carregar_template.setFixedHeight(28)
        btn_carregar_template.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        btn_carregar_template.clicked.connect(self.carregar_template)
        btn_layout.addWidget(btn_carregar_template)

        btn_salvar_alteracoes = QPushButton("💾 Salvar Alterações")
        self.btn_salvar_alteracoes = btn_salvar_alteracoes
        btn_salvar_alteracoes.setFixedHeight(28)
        btn_salvar_alteracoes.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        btn_salvar_alteracoes.clicked.connect(self.sobrescrever_template)
        btn_salvar_alteracoes.setEnabled(False)
        btn_layout.addWidget(btn_salvar_alteracoes)

        btn_html = QPushButton("</> HTML")
        btn_html.setFixedHeight(28)
        btn_html.setStyleSheet("padding: 2px 10px; font-size: 11px;")
        btn_html.clicked.connect(self.editar_html)
        btn_layout.addWidget(btn_html)

        btn_layout.addStretch()

        btn_layout.addWidget(QLabel("Intervalo:"))
        self.intervalo_spin = QSpinBox()
        self.intervalo_spin.setRange(1, 60)
        self.intervalo_spin.setValue(5)
        self.intervalo_spin.setSuffix(" seg")
        self.intervalo_spin.setFixedWidth(80)
        self.intervalo_spin.setFixedHeight(28)
        self.intervalo_spin.setStyleSheet("font-size: 12px;")
        btn_layout.addWidget(self.intervalo_spin)

        self.btn_enviar = QPushButton("📧 Enviar")
        self.btn_enviar.setFixedHeight(30)
        self.btn_enviar.setStyleSheet("background-color: #27ae60; color: white; padding: 4px 16px; font-weight: bold; font-size: 12px; border-radius: 4px;")
        self.btn_enviar.clicked.connect(self.enviar_emails)
        btn_layout.addWidget(self.btn_enviar)

        editor_layout.addLayout(btn_layout)

        # Painel direito: Prévia
        preview_panel = QWidget()
        preview_panel.setMinimumWidth(480)
        preview_layout = QVBoxLayout()
        preview_panel.setLayout(preview_layout)

        preview_layout.addWidget(QLabel("Prévia do Email:"))

        self.email_previa = QTextEdit()
        self.email_previa.setReadOnly(True)
        self.email_previa.setMinimumHeight(500)
        self.email_previa.setStyleSheet("background-color: #fafafa; border: 1px solid #ddd;")
        preview_layout.addWidget(self.email_previa, 1)

        self.email_info = QLabel("Carregando...")
        self.email_info.setStyleSheet("color: #666; font-size: 12px; padding: 10px; background: #f0f0f0; border-radius: 4px;")
        self.email_info.setWordWrap(True)
        preview_layout.addWidget(self.email_info)

        layout.addWidget(editor_panel, 2)
        layout.addWidget(preview_panel, 3)

        self.tab_emails.setLayout(layout)
        self.carregar_info_previa()

    def setup_tab_logs(self):
        layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs do sistema aparecerão aqui...")
        layout.addWidget(self.log_text)
        self.tab_logs.setLayout(layout)

    def log(self, mensagem):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {mensagem}")
        # Auto-muda para aba de logs
        self.tabs.setCurrentWidget(self.tab_logs)

    def _format_text(self, editor, fmt):
        cursor = editor.textCursor()
        if fmt == "bold":
            editor.setFontWeight(75 if cursor.charFormat().fontWeight() < 75 else 50)
        elif fmt == "italic":
            editor.setFontItalic(not cursor.charFormat().fontItalic())
        elif fmt == "underline":
            editor.setFontUnderline(not cursor.charFormat().fontUnderline())
        editor.setFocus()

    def _format_heading(self, editor, level):
        if level == 0:
            editor.setFontPointSize(12)
        elif level == 1:
            editor.setFontPointSize(24)
        elif level == 2:
            editor.setFontPointSize(18)
        elif level == 3:
            editor.setFontPointSize(14)
        editor.setFocus()

    def _format_align(self, editor, align):
        if align == "left":
            editor.setAlignment(Qt.AlignLeft)
        elif align == "center":
            editor.setAlignment(Qt.AlignCenter)
        elif align == "right":
            editor.setAlignment(Qt.AlignRight)

    def _escolher_cor(self, editor):
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor("#e74c3c"), self, "Escolher Cor da Fonte")
        if color.isValid():
            cursor = editor.textCursor()
            fmt = cursor.charFormat()
            fmt.setForeground(color)
            cursor.setCharFormat(fmt)
            editor.setFocus()

    def _escolher_cor_fundo(self, editor):
        from PyQt5.QtGui import QColor
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor("#f1c40f"), self, "Escolher Cor de Fundo")
        if color.isValid():
            cursor = editor.textCursor()
            block_fmt = cursor.blockFormat()
            block_fmt.setBackground(color)
            cursor.setBlockFormat(block_fmt)
            editor.setFocus()

    def _insert_list(self, editor, list_type):
        if list_type == "bullet":
            editor.insertHtml("<ul><li>Item</li></ul>")
        elif list_type == "numbered":
            editor.insertHtml("<ol><li>Item</li></ol>")

    def _inserir_link(self, editor):
        url, ok = QInputDialog.getText(self, "Inserir Link", "URL:")
        if ok and url:
            text, ok2 = QInputDialog.getText(self, "Texto do Link", "Texto (opcional):")
            if ok2:
                link_text = text if text else url
                html = f'<a href="{url}">{link_text}</a>'
            editor.insertHtml(html)

    def _inserir_botao(self, editor):
        dialog = QDialog(self)
        dialog.setWindowTitle("Inserir Botão")
        dialog.setGeometry(300, 300, 380, 380)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Texto do Botão:"))
        texto_input = QLineEdit()
        texto_input.setPlaceholderText("Ex: Inscreva-se")
        layout.addWidget(texto_input)

        layout.addWidget(QLabel("Link (URL):"))
        url_input = QLineEdit()
        url_input.setPlaceholderText("Ex: https://exemplo.com/curso")
        layout.addWidget(url_input)

        layout.addWidget(QLabel("Cor do Botão:"))
        cor_combo = QComboBox()
        cor_combo.addItems(["Azul", "Verde", "Vermelho", "Laranja", "Roxo", "Cinza"])
        layout.addWidget(cor_combo)

        layout.addWidget(QLabel("Arredondamento:"))
        raio_combo = QComboBox()
        raio_combo.addItems(["Nenhum (0px)", "Pouco (4px)", "Médio (8px)", "Muito (15px)", "Total (25px)"])
        layout.addWidget(raio_combo)

        layout.addWidget(QLabel("Preenchimento Vertical:"))
        pad_v_combo = QComboBox()
        pad_v_combo.addItems(["Pequeno (6px)", "Médio (12px)", "Grande (18px)"])
        layout.addWidget(pad_v_combo)

        layout.addWidget(QLabel("Preenchimento Horizontal:"))
        pad_h_combo = QComboBox()
        pad_h_combo.addItems(["Pequeno (12px)", "Médio (24px)", "Grande (36px)"])
        layout.addWidget(pad_h_combo)

        layout.addWidget(QLabel("Alinhamento:"))
        align_combo = QComboBox()
        align_combo.addItems(["Esquerda", "Centro", "Direita"])
        layout.addWidget(align_combo)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Inserir")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            texto = texto_input.text().strip() or "Clique Aqui"
            url = url_input.text().strip() or "#"

            cores = {"Azul": "#3498db", "Verde": "#27ae60", "Vermelho": "#e74c3c",
                     "Laranja": "#e67e22", "Roxo": "#8e44ad", "Cinza": "#7f8c8d"}
            cor = cores[cor_combo.currentText()]

            raios = {"Nenhum (0px)": "0", "Pouco (4px)": "4", "Médio (8px)": "8",
                     "Muito (15px)": "15", "Total (25px)": "25"}
            raio = raios[raio_combo.currentText()]

            pads_v = {"Pequeno (6px)": "6", "Médio (12px)": "12", "Grande (18px)": "18"}
            pad_v = pads_v[pad_v_combo.currentText()]

            pads_h = {"Pequeno (12px)": "12", "Médio (24px)": "24", "Grande (36px)": "36"}
            pad_h = pads_h[pad_h_combo.currentText()]

            align = {"Esquerda": "left", "Centro": "center", "Direita": "right"}[align_combo.currentText()]

            params = urlencode({
                'text': texto, 'url': url, 'color': cor,
                'radius': raio, 'pad_v': pad_v, 'pad_h': pad_h, 'align': align
            })
            href = f"btn://data?{params}"
            html = (
                f'<a href="{href}" style="background-color:{cor}; color:white; '
                f'padding:{pad_v}px {pad_h}px; text-decoration:none; font-weight:bold; '
                f'display:inline-block; font-size:14px;">{texto}</a>'
            )
            editor.insertHtml(html)

    def _editar_botao(self, editor):
        cursor = editor.textCursor()
        fmt = cursor.charFormat()

        if not fmt.isAnchor() or not fmt.anchorHref().startswith('btn://'):
            QMessageBox.information(
                self, "Editar Botão",
                "Posicione o cursor sobre um botão e clique com botão direito.")
            return

        href = fmt.anchorHref()
        qs = parse_qs(href.split('?', 1)[1])
        texto = qs.get('text', [''])[0]
        url = qs.get('url', [''])[0]
        cor_hex = qs.get('color', ['#3498db'])[0]
        raio_px = qs.get('radius', ['8'])[0]
        pad_v_px = qs.get('pad_v', ['12'])[0]
        pad_h_px = qs.get('pad_h', ['24'])[0]
        align = qs.get('align', ['center'])[0]

        cor_para_nome = {"#3498db": "Azul", "#27ae60": "Verde", "#e74c3c": "Vermelho",
                         "#e67e22": "Laranja", "#8e44ad": "Roxo", "#7f8c8d": "Cinza"}
        nome_cor = cor_para_nome.get(cor_hex, "Azul")

        raio_para_nome = {"0": "Nenhum (0px)", "4": "Pouco (4px)", "8": "Médio (8px)",
                          "15": "Muito (15px)", "25": "Total (25px)"}
        nome_raio = raio_para_nome.get(raio_px, "Médio (8px)")

        pad_v_para_nome = {"6": "Pequeno (6px)", "12": "Médio (12px)", "18": "Grande (18px)"}
        nome_pad_v = pad_v_para_nome.get(pad_v_px, "Médio (12px)")

        pad_h_para_nome = {"12": "Pequeno (12px)", "24": "Médio (24px)", "36": "Grande (36px)"}
        nome_pad_h = pad_h_para_nome.get(pad_h_px, "Médio (24px)")

        align_para_nome = {"left": "Esquerda", "center": "Centro", "right": "Direita"}
        nome_align = align_para_nome.get(align, "Centro")

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Botão")
        dialog.setGeometry(300, 300, 380, 380)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Texto do Botão:"))
        texto_input = QLineEdit(texto)
        layout.addWidget(texto_input)

        layout.addWidget(QLabel("Link (URL):"))
        url_input = QLineEdit(url)
        layout.addWidget(url_input)

        layout.addWidget(QLabel("Cor do Botão:"))
        cor_combo = QComboBox()
        cor_combo.addItems(["Azul", "Verde", "Vermelho", "Laranja", "Roxo", "Cinza"])
        cor_combo.setCurrentText(nome_cor)
        layout.addWidget(cor_combo)

        layout.addWidget(QLabel("Arredondamento:"))
        raio_combo = QComboBox()
        raio_combo.addItems(["Nenhum (0px)", "Pouco (4px)", "Médio (8px)", "Muito (15px)", "Total (25px)"])
        raio_combo.setCurrentText(nome_raio)
        layout.addWidget(raio_combo)

        layout.addWidget(QLabel("Preenchimento Vertical:"))
        pad_v_combo = QComboBox()
        pad_v_combo.addItems(["Pequeno (6px)", "Médio (12px)", "Grande (18px)"])
        pad_v_combo.setCurrentText(nome_pad_v)
        layout.addWidget(pad_v_combo)

        layout.addWidget(QLabel("Preenchimento Horizontal:"))
        pad_h_combo = QComboBox()
        pad_h_combo.addItems(["Pequeno (12px)", "Médio (24px)", "Grande (36px)"])
        pad_h_combo.setCurrentText(nome_pad_h)
        layout.addWidget(pad_h_combo)

        layout.addWidget(QLabel("Alinhamento:"))
        align_combo = QComboBox()
        align_combo.addItems(["Esquerda", "Centro", "Direita"])
        align_combo.setCurrentText(nome_align)
        layout.addWidget(align_combo)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Atualizar")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            novo_texto = texto_input.text().strip() or "Clique Aqui"
            novo_url = url_input.text().strip() or "#"

            cores = {"Azul": "#3498db", "Verde": "#27ae60", "Vermelho": "#e74c3c",
                     "Laranja": "#e67e22", "Roxo": "#8e44ad", "Cinza": "#7f8c8d"}
            nova_cor = cores[cor_combo.currentText()]

            raios = {"Nenhum (0px)": "0", "Pouco (4px)": "4", "Médio (8px)": "8",
                     "Muito (15px)": "15", "Total (25px)": "25"}
            novo_raio = raios[raio_combo.currentText()]

            pads_v = {"Pequeno (6px)": "6", "Médio (12px)": "12", "Grande (18px)": "18"}
            novo_pad_v = pads_v[pad_v_combo.currentText()]

            pads_h = {"Pequeno (12px)": "12", "Médio (24px)": "24", "Grande (36px)": "36"}
            novo_pad_h = pads_h[pad_h_combo.currentText()]

            novo_align = {"Esquerda": "left", "Centro": "center", "Direita": "right"}[align_combo.currentText()]

            params = urlencode({
                'text': novo_texto, 'url': novo_url, 'color': nova_cor,
                'radius': novo_raio, 'pad_v': novo_pad_v, 'pad_h': novo_pad_h,
                'align': novo_align
            })
            novo_href = f"btn://data?{params}"
            nova_tag = (
                f'<a href="{novo_href}" style="background-color:{nova_cor}; color:white; '
                f'padding:{novo_pad_v}px {novo_pad_h}px; text-decoration:none; font-weight:bold; '
                f'display:inline-block; font-size:14px;">{novo_texto}</a>'
            )

            html = editor.toHtml()
            html = re.sub(
                rf'href="{re.escape(href)}"[^>]*>.*?</a>',
                nova_tag,
                html,
                flags=re.DOTALL
            )
            editor.setHtml(html)

    def _acao_botao_context_menu(self, editor, action):
        cursor = editor.textCursor()
        fmt = cursor.charFormat()
        
        if action == 'edit':
            self._editar_botao(editor)
        elif action == 'remove':
            if fmt.isAnchor() and fmt.anchorHref().startswith('btn://'):
                href = fmt.anchorHref()
                html = editor.toHtml()
                html = re.sub(
                    rf'href="{re.escape(href)}"[^>]*>.*?</a>',
                    '',
                    html,
                    count=1,
                    flags=re.DOTALL
                )
                editor.setHtml(html)
    
    def _inserir_imagem(self, editor):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.gif *.bmp)")
        if not arquivo:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Inserir Imagem")
        dialog.setGeometry(300, 300, 300, 250)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Tamanho:"))
        tamanho_combo = QComboBox()
        tamanho_combo.addItems(["Pequena (25%)", "Media (50%)", "Grande (75%)", "Total (100%)"])
        tamanho_combo.setCurrentIndex(1)
        layout.addWidget(tamanho_combo)

        layout.addWidget(QLabel("Alinhamento:"))
        alinhamento_combo = QComboBox()
        alinhamento_combo.addItems(["Esquerda", "Centro", "Direita"])
        layout.addWidget(alinhamento_combo)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Inserir")
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted:
            import base64
            with open(arquivo, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(arquivo)[1].lower()
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "bmp": "image/bmp"}.get(ext[1:], "image/png")

            pcts = {"Pequena (25%)": 0.25, "Media (50%)": 0.5, "Grande (75%)": 0.75, "Total (100%)": 1}
            pct = pcts[tamanho_combo.currentText()]
            align = {"Esquerda": "left", "Centro": "center", "Direita": "right"}[alinhamento_combo.currentText()]

            img_id = self._img_counter
            self._img_counter += 1
            editor_width = editor.viewport().width()
            px = int(editor_width * pct)
            self._imagens[str(img_id)] = {
                'b64': b64, 'mime': mime, 'px': px, 'align': align
            }
            editor.insertPlainText(f"_IMG_{img_id}_{px}_{align}_")
    
    def _inserir_variavel(self, editor, combo, index):
        if index > 0:
            var = combo.currentText()
            editor.insertPlainText(var)
            combo.setCurrentIndex(0)
    
    def _html_body(self, editor):
        raw = editor.toHtml()
        m = re.search(r'<body[^>]*>(.*)</body>', raw, re.DOTALL)
        content = m.group(1).strip() if m else raw
        content = re.sub(r'</?(?:html|head|body|meta|!DOCTYPE)[^>]*>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        return content

    def _secao_html_isolada(self, editor):
        raw = editor.toHtml()
        m_body = re.search(r'<body([^>]*)>(.*)</body>', raw, re.DOTALL)
        if m_body:
            body_attrs = m_body.group(1)
            content = m_body.group(2).strip()
            m_style = re.search(r'style="([^"]*)"', body_attrs)
            body_style = m_style.group(1) if m_style else ""
        else:
            content = raw
            body_style = ""
        content = re.sub(r'</?(?:html|head|body|meta|!DOCTYPE)[^>]*>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        return (
            f'<table width="100%" cellpadding="12" cellspacing="0" '
            f'style="border-collapse:collapse; {body_style}">'
            f'<tr><td>{content}</td></tr></table>'
        )

    def atualizar_previa(self):
        assunto = self.email_assunto.text()
        cab = self._secao_html_isolada(self.email_cabecalho)
        corpo = self._secao_html_isolada(self.email_corpo)
        rodape = self._secao_html_isolada(self.email_rodape)
        separador = '<hr style="border: none; border-top: 2px dashed #ccc; margin: 12px 0;">'
        partes = [p for p in [cab, corpo, rodape] if p]
        html = separador.join(partes) if partes else ""
        
        # Buscar dados reais do curso para a prévia
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.nome, c.tema, c.descricao, c.carga_horaria, i.nome, i.empresa, cd.hora
                FROM cursos_datas cd
                JOIN cursos c ON c.id = cd.curso_id
                JOIN instrutores i ON i.id = cd.instrutor_id
                WHERE cd.id = ?
            """, (self.prog_id,))
            curso_info = cursor.fetchone()
            conn.close()
            
            if curso_info:
                curso_nome, tema, descricao, carga_horaria, instrutor_nome, instrutor_empresa, hora = curso_info
                data_formatada = QDate.fromString(self.data, "yyyy-MM-dd").toString("dd/MM/yyyy")
                
                preview_html = html.replace("{{nome_curso}}", f"<strong>{curso_nome or ''}</strong>")\
                                  .replace("{{data_curso}}", f"<strong>{data_formatada}</strong>")\
                                  .replace("{{hora_curso}}", f"<strong>{hora or ''}</strong>")\
                                  .replace("{{nome_instrutor}}", f"<strong>{instrutor_nome or ''}</strong>")\
                                  .replace("{{carga_horaria}}", f"<strong>{carga_horaria}h</strong>" if carga_horaria else "")\
                                  .replace("{{tema_curso}}", f"<strong>{tema or ''}</strong>")
                preview_html = preview_html.replace("{{empresa_instrutor}}", f"<strong>{instrutor_empresa or ''}</strong>")
                preview_html = preview_html.replace("{{nome_aluno}}", "")
            else:
                preview_html = html.replace("{{nome_curso}}", "<strong>[Nome do Curso]</strong>")\
                                  .replace("{{data_curso}}", "<strong>[Data]</strong>")\
                                  .replace("{{hora_curso}}", "<strong>[Hora]</strong>")\
                                  .replace("{{nome_instrutor}}", "<strong>[Instrutor]</strong>")\
                                  .replace("{{empresa_instrutor}}", "<strong>[Empresa]</strong>")\
                                  .replace("{{carga_horaria}}", "<strong>[Carga Horária]</strong>")\
                                  .replace("{{tema_curso}}", "<strong>[Tema]</strong>")
                preview_html = preview_html.replace("{{nome_aluno}}", "")
        except:
            preview_html = html.replace("{{nome_curso}}", "<strong>[Nome do Curso]</strong>")\
                              .replace("{{data_curso}}", "<strong>[Data]</strong>")\
                              .replace("{{hora_curso}}", "<strong>[Hora]</strong>")\
                              .replace("{{nome_instrutor}}", "<strong>[Instrutor]</strong>")\
                              .replace("{{empresa_instrutor}}", "<strong>[Empresa]</strong>")\
                              .replace("{{carga_horaria}}", "<strong>[Carga Horária]</strong>")\
                              .replace("{{tema_curso}}", "<strong>[Tema]</strong>")
            preview_html = preview_html.replace("{{nome_aluno}}", "")
        
        # Converter placeholders de botões para HTML real
        preview_html = _converter_botoes_para_html(preview_html)
        preview_html = _converter_imagens_para_html(preview_html, self._imagens)
        
        preview_html = re.sub(r'<html[^>]*>|<head>.*?</head>|<body[^>]*>|</html>|</body>', '', preview_html, flags=re.DOTALL).strip()
        
        self.email_previa.setHtml(f"""
        <div align="center" style="font-family: 'Segoe UI', Arial, sans-serif; background: #f0f0f0; padding: 20px;">
            <table cellpadding="0" cellspacing="0" style="width: 100%; background: #ffffff; border-radius: 6px; border: 1px solid #ddd;">
                <tr>
                    <td style="padding: 14px 20px 8px 20px; background: #f9f9f9; border-bottom: 1px solid #e0e0e0;">
                        <div style="font-size: 13px; color: #555;">
                            <b style="color: #333;">De:</b> sistema@gestorcursos.com &nbsp;|&nbsp;
                            <b style="color: #333;">Para:</b> destinatario@email.com &nbsp;|&nbsp;
                            <b style="color: #333;">Assunto:</b> {assunto or '(sem assunto)'}
                        </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 0;">
                        {preview_html}
                    </td>
                </tr>
                <tr>
                    <td align="center" style="padding: 10px; font-size: 11px; color: #999; border-top: 1px solid #eee;">
                        Previa visual - variaveis serao substituidas no envio real
                    </td>
                </tr>
            </table>
        </div>
        """)
    
    def carregar_info_previa(self):
        try:
            texto_emails = self.email_destinatarios.toPlainText().strip()
            if texto_emails:
                emails_colados = [e.strip() for e in re.split(r'[,;\n]+', texto_emails) if e.strip() and "@" in e.strip()]
                self.email_info.setText(f"📧 <b>Emails colados:</b> {len(emails_colados)} email(s) válido(s)")
            else:
                self.email_info.setText(f"📧 <b>Emails colados:</b> Nenhum (campo vazio!)")
        except:
            self.email_info.setText("Erro ao carregar info")
    
    def limpar_editor(self):
        self.email_assunto.clear()
        self.email_cabecalho.clear()
        self.email_corpo.clear()
        self.email_rodape.clear()
        self.email_destinatarios.clear()
        self._template_atual = None
        self._template_modificado = False
        self._atualizar_botao_salvar_alteracoes()
        self.atualizar_previa()
        self.carregar_info_previa()

    def salvar_template(self):
        nome_padrao = self._template_atual or ""
        nome, ok = QInputDialog.getText(self, "Salvar Template", "Nome do template:", text=nome_padrao)
        if ok and nome:
            self._salvar_template_por_nome(nome)

    def sobrescrever_template(self):
        if not self._template_atual:
            QMessageBox.warning(self, "Aviso", "Nenhum template carregado. Use 'Salvar' para criar um novo.")
            return
        self._salvar_template_por_nome(self._template_atual)

    def _salvar_template_por_nome(self, nome):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY,
                    nome TEXT UNIQUE,
                    assunto TEXT,
                    corpo_html TEXT
                )
            """)
            cursor.execute("PRAGMA table_info(email_templates)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'corpo_cabecario' not in cols:
                cursor.execute("ALTER TABLE email_templates ADD COLUMN corpo_cabecario TEXT")
            if 'corpo_rodape' not in cols:
                cursor.execute("ALTER TABLE email_templates ADD COLUMN corpo_rodape TEXT")
            cursor.execute("""
                INSERT OR REPLACE INTO email_templates
                    (nome, assunto, corpo_html, corpo_cabecario, corpo_rodape)
                VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                self.email_assunto.text(),
                self._html_body(self.email_corpo),
                self._html_body(self.email_cabecalho),
                self._html_body(self.email_rodape),
            ))
            conn.commit()
            conn.close()
            self._template_atual = nome
            self._template_modificado = False
            self._atualizar_botao_salvar_alteracoes()
            QMessageBox.information(self, "Sucesso", f"Template '{nome}' salvo!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar template: {str(e)}")

    def _marcar_template_modificado(self):
        if not self._template_modificado and self._template_atual:
            self._template_modificado = True
            self._atualizar_botao_salvar_alteracoes()

    def _atualizar_botao_salvar_alteracoes(self):
        self.btn_salvar_alteracoes.setEnabled(
            self._template_atual is not None and self._template_modificado
        )

    def editar_html(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar HTML")
        dialog.setGeometry(300, 300, 700, 500)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("HTML completo do email (cabeçário + corpo + rodapé):"))
        editor = QPlainTextEdit()
        combined = (
            f"<!-- CABECALHO -->\n{self._html_body(self.email_cabecalho)}\n"
            f"<!-- CORPO -->\n{self._html_body(self.email_corpo)}\n"
            f"<!-- RODAPE -->\n{self._html_body(self.email_rodape)}"
        )
        editor.setPlainText(combined)
        editor.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(editor)
        btn_layout = QHBoxLayout()
        btn_aplicar = QPushButton("Aplicar")
        btn_aplicar.clicked.connect(dialog.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        btn_layout.addWidget(btn_aplicar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        if dialog.exec_() == QDialog.Accepted:
            html = editor.toPlainText().strip()
            if html:
                # Tenta separar pelos marcadores, senão coloca tudo no corpo
                m_cab = re.search(r'<!-- CABECALHO -->(.*?)<!-- CORPO -->', html, re.DOTALL)
                m_corp = re.search(r'<!-- CORPO -->(.*?)<!-- RODAPE -->', html, re.DOTALL)
                m_rod = re.search(r'<!-- RODAPE -->(.*)', html, re.DOTALL)
                if m_cab and m_corp and m_rod:
                    self.email_cabecalho.setHtml(m_cab.group(1).strip())
                    self.email_corpo.setHtml(m_corp.group(1).strip())
                    self.email_rodape.setHtml(m_rod.group(1).strip())
                else:
                    self.email_corpo.setHtml(html)
                self.atualizar_previa()
    
    def carregar_template(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS email_templates (id INTEGER PRIMARY KEY, nome TEXT UNIQUE, assunto TEXT, corpo_html TEXT)")
            try:
                cursor.execute("SELECT nome, assunto, corpo_html, corpo_cabecario, corpo_rodape FROM email_templates")
                templates = cursor.fetchall()
            except sqlite3.OperationalError:
                cursor.execute("SELECT nome, assunto, corpo_html FROM email_templates")
                templates = [(r[0], r[1], r[2], None, None) for r in cursor.fetchall()]
            conn.close()

            if not templates:
                QMessageBox.information(self, "Aviso", "Nenhum template salvo.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Gerenciar Templates")
            dialog.setGeometry(300, 300, 500, 400)
            layout = QVBoxLayout(dialog)

            layout.addWidget(QLabel("Selecione um template:"))
            list_widget = QListWidget()
            for t in templates:
                list_widget.addItem(t[0])
            layout.addWidget(list_widget)

            btn_layout = QHBoxLayout()
            btn_carregar = QPushButton("Carregar")
            btn_carregar.clicked.connect(dialog.accept)
            btn_renomear = QPushButton("Renomear")
            btn_excluir = QPushButton("Excluir")
            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.clicked.connect(dialog.reject)

            btn_layout.addWidget(btn_carregar)
            btn_layout.addWidget(btn_renomear)
            btn_layout.addWidget(btn_excluir)
            btn_layout.addWidget(btn_cancelar)
            layout.addLayout(btn_layout)

            # Handler para renomear
            def renomear():
                item = list_widget.currentItem()
                if not item:
                    QMessageBox.warning(dialog, "Aviso", "Selecione um template.")
                    return
                novo_nome, ok = QInputDialog.getText(dialog, "Renomear", "Novo nome:", text=item.text())
                if ok and novo_nome:
                    try:
                        conn2 = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                        c2 = conn2.cursor()
                        c2.execute("UPDATE email_templates SET nome = ? WHERE nome = ?", (novo_nome, item.text()))
                        conn2.commit()
                        conn2.close()
                        item.setText(novo_nome)
                        QMessageBox.information(dialog, "Sucesso", "Template renomeado!")
                    except Exception as e:
                        QMessageBox.critical(dialog, "Erro", str(e))

            # Handler para excluir
            def excluir():
                item = list_widget.currentItem()
                if not item:
                    QMessageBox.warning(dialog, "Aviso", "Selecione um template.")
                    return
                resp = QMessageBox.question(dialog, "Confirmar", f"Excluir template '{item.text()}'?",
                                            QMessageBox.Yes | QMessageBox.No)
                if resp == QMessageBox.Yes:
                    try:
                        conn2 = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                        c2 = conn2.cursor()
                        c2.execute("DELETE FROM email_templates WHERE nome = ?", (item.text(),))
                        conn2.commit()
                        conn2.close()
                        list_widget.takeItem(list_widget.row(item))
                        QMessageBox.information(dialog, "Sucesso", "Template excluído!")
                    except Exception as e:
                        QMessageBox.critical(dialog, "Erro", str(e))

            btn_renomear.clicked.connect(renomear)
            btn_excluir.clicked.connect(excluir)

            if dialog.exec_() == QDialog.Accepted:
                item = list_widget.currentItem()
                if not item:
                    return
                nome = item.text()
                for row in templates:
                    if row[0] == nome:
                        t_nome, t_assunto, t_corpo = row[0], row[1], row[2]
                        t_cabecario = row[3] if len(row) > 3 else None
                        t_rodape = row[4] if len(row) > 4 else None
                        self.email_assunto.setText(t_assunto)
                        self._template_atual = None  # evita marcar como modificado
                        self.email_cabecalho.setHtml(t_cabecario or "")
                        self.email_corpo.setHtml(t_corpo or "")
                        self.email_rodape.setHtml(t_rodape or "")
                        self._template_atual = nome
                        self._template_modificado = False
                        self._atualizar_botao_salvar_alteracoes()
                        self.atualizar_previa()
                        break
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerenciar templates: {str(e)}")

    def carregar_dados(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Carregar cursos
            cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
            cursos = cursor.fetchall()
            self.curso_combo.clear()
            for cid, cnome in cursos:
                self.curso_combo.addItem(cnome, cid)

            # Carregar instrutores
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            self.instrutor_combo.clear()
            for iid, inome in instrutores:
                self.instrutor_combo.addItem(inome, iid)

            # Carregar dados da programação
            cursor.execute("""
                SELECT curso_id, instrutor_id, hora FROM cursos_datas WHERE id = ?
            """, (self.prog_id,))
            prog = cursor.fetchone()
            if prog:
                p_curso_id, p_instrutor_id, p_hora = prog
                idx = self.curso_combo.findData(p_curso_id)
                if idx >= 0:
                    self.curso_combo.setCurrentIndex(idx)
                idx = self.instrutor_combo.findData(p_instrutor_id)
                if idx >= 0:
                    self.instrutor_combo.setCurrentIndex(idx)
                if p_hora:
                    self.hora_input.setTime(QTime.fromString(p_hora, "HH:mm"))

            # Contar alunos
            cursor.execute("SELECT COUNT(*) FROM alunos WHERE curso_id = ?", (self.curso_id,))
            total_alunos = cursor.fetchone()[0]
            self.alunos_resumo.setText(f"{total_alunos} aluno(s) cadastrado(s) neste curso.")

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {str(e)}")

    def salvar_programacao(self):
        curso_id = self.curso_combo.currentData()
        instrutor_id = self.instrutor_combo.currentData()
        hora = self.hora_input.time().toString("HH:mm")

        if not curso_id or not instrutor_id:
            QMessageBox.warning(self, "Erro", "Selecione o curso e o instrutor.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM instrutores_cursos
                WHERE curso_id = ? AND instrutor_id = ? LIMIT 1
            """, (curso_id, instrutor_id))
            if not cursor.fetchone():
                QMessageBox.warning(self, "Erro", "Este instrutor não está associado ao curso selecionado.")
                conn.close()
                return

            cursor.execute("""
                UPDATE cursos_datas SET curso_id = ?, instrutor_id = ?, hora = ?
                WHERE id = ?
            """, (curso_id, instrutor_id, hora, self.prog_id))

            conn.commit()
            conn.close()

            self.curso_id = curso_id
            QMessageBox.information(self, "Sucesso", "Programação atualizada com sucesso!")
            self.carregar_dados()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def excluir_programacao(self):
        resposta = QMessageBox.question(
            self, "Confirmação",
            "Tem certeza que deseja excluir esta programação?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cursos_datas WHERE id = ?", (self.prog_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Programação excluída!")
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {str(e)}")

    def abrir_gerenciar_alunos(self):
        nome_curso = self.curso_combo.currentText()
        janela = GerenciarAlunosWindow(self.curso_id, nome_curso, self)
        janela.exec_()
        self.carregar_dados()

    def enviar_emails(self):
        assunto = self.email_assunto.text().strip()
        html_corpo = self._secao_html_isolada(self.email_cabecalho) + self._secao_html_isolada(self.email_corpo) + self._secao_html_isolada(self.email_rodape)

        if not assunto or not html_corpo.strip():
            QMessageBox.warning(self, "Erro", "Preencha o assunto e a mensagem.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_name, smtp_use_tls FROM email_config LIMIT 1")
            config = cursor.fetchone()
            if not config or not config[0]:
                QMessageBox.warning(self, "Erro", "Configure o SMTP primeiro no menu 'Configurar Email (SMTP)'.")
                conn.close()
                return
            smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_name, smtp_use_tls = config

            cursor.execute("""
                SELECT c.nome, c.tema, c.descricao, c.carga_horaria, i.nome, i.empresa, cd.hora
                FROM cursos_datas cd
                JOIN cursos c ON c.id = cd.curso_id
                JOIN instrutores i ON i.id = cd.instrutor_id
                WHERE cd.id = ?
            """, (self.prog_id,))
            curso_info = cursor.fetchone()
            conn.close()

            if not curso_info:
                QMessageBox.warning(self, "Erro", "Informações do curso não encontradas.")
                return

            curso_nome, tema, descricao, carga_horaria, instrutor_nome, instrutor_empresa, hora = curso_info
            data_formatada = QDate.fromString(self.data, "yyyy-MM-dd").toString("dd/MM/yyyy")

            variaveis = {
                "{{nome_curso}}": curso_nome or "",
                "{{data_curso}}": data_formatada,
                "{{hora_curso}}": hora or "",
                "{{nome_instrutor}}": instrutor_nome or "",
                "{{carga_horaria}}": f"{carga_horaria}h" if carga_horaria else "",
                "{{tema_curso}}": tema or "",
            }

            texto_emails = self.email_destinatarios.toPlainText().strip()
            if not texto_emails:
                QMessageBox.warning(self, "Erro", "Cole os emails no campo de destinatários.")
                return
            emails = [e.strip() for e in re.split(r'[,;\n]+', texto_emails) if e.strip() and "@" in e.strip()]
            if not emails:
                QMessageBox.warning(self, "Erro", "Nenhum email válido encontrado no campo.")
                return

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar dados: {str(e)}")
            return

        self.thread_envio = SendEmailThread(
            emails, assunto, html_corpo, variaveis, instrutor_empresa,
            smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_name,
            smtp_use_tls, self._imagens, self.intervalo_spin.value()
        )
        self.thread_envio.log_message.connect(lambda msg: self.log(msg))
        self.thread_envio.progress.connect(lambda atual, total: self.log(f"Progresso: {atual}/{total}"))
        self.thread_envio.error_smtp.connect(lambda err: QMessageBox.critical(self, "Erro SMTP", f"Erro na conexão SMTP: {err}"))
        self.thread_envio.finished_send.connect(self._envio_finalizado)
        self.btn_enviar.setEnabled(False)
        self.btn_enviar.setText("⏳ Enviando...")
        self.thread_envio.start()

    def _envio_finalizado(self, enviados, erros):
        self.btn_enviar.setEnabled(True)
        self.btn_enviar.setText("📧 Enviar")
        msg = f"✅ Enviados: {enviados}\n"
        if erros:
            msg += f"❌ Erros: {len(erros)}\n\n" + "\n".join(erros[:10])
            if len(erros) > 10:
                msg += f"\n... e mais {len(erros) - 10} erros"
        QMessageBox.information(self, "Resultado do Envio", msg)


# Janela principal com layout melhorado
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("crc.ico"))
        self.setWindowTitle("Gerenciamento de Cursos e Instrutores")
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()

        # Widget central com layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        self.central_widget.setLayout(main_layout)

        # =========================
        # PAINEL ESQUERDO (Sidebar)
        # =========================
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)
        left_panel.setObjectName("leftPanel")

        # Título do painel (botão com menu dropdown)
        self.menu_acoes_button = QPushButton("Menu de Ações")
        self.menu_acoes_button.setObjectName("panelTitle")
        self.menu_acoes_button.setMenu(self.criar_menu_acoes())
        left_layout.addWidget(self.menu_acoes_button)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("separator")
        left_layout.addWidget(line)

        # Botão Programar Curso
        self.programar_curso_button = QPushButton("Programar Curso")
        self.programar_curso_button.clicked.connect(self.abrir_programacao_rapida)
        self.programar_curso_button.setObjectName("primaryButton")
        left_layout.addWidget(self.programar_curso_button)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("separator")
        left_layout.addWidget(line)

        # Calendário
        calendar_label = QLabel("Calendário")
        calendar_label.setObjectName("sectionLabel")
        left_layout.addWidget(calendar_label)

        self.calendar = QCalendarWidget()
        self.calendar.setFocusPolicy(Qt.NoFocus)
        self.calendar.clicked.connect(self.handle_single_click)
        self.calendar.activated.connect(self.handle_double_click)
        self.calendar.setObjectName("calendar")
        left_layout.addWidget(self.calendar)

        # Label de datas selecionadas
        self.selected_dates_label = QLabel("Nenhuma data selecionada")
        self.selected_dates_label.setObjectName("infoLabel")
        self.selected_dates_label.setWordWrap(True)
        left_layout.addWidget(self.selected_dates_label)

        left_layout.addStretch()

        # =========================
        # PAINEL DIREITO (Conteúdo)
        # =========================
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        right_panel.setObjectName("rightPanel")

        # Cabeçalho da tabela
        table_header = QLabel("Cursos Programados")
        table_header.setObjectName("tableHeader")
        right_layout.addWidget(table_header)

        # Tabela de cursos
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Curso", "Instrutor", "Horário"])
        self.tabela.setObjectName("coursesTable")

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.tabela.setWordWrap(True)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SingleSelection)
        self.tabela.verticalHeader().setVisible(False)

        self.tabela.itemDoubleClicked.connect(self.abrir_detalhes_programacao)

        right_layout.addWidget(self.tabela)

        # Adicionar painéis ao layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)

        # Inicialização
        self.selected_dates = set()
        self.programmed_dates = set()
        self.atualizar_calendario()

        # Aplicar estilo CSS com cores originais
        self.setStyleSheet("""
            /* ========== GERAL ========== */
            QMainWindow {
                background-color: #f5f5f5;
            }

            /* ========== PAINÉIS ========== */
            #leftPanel {
                background-color: #ffffff;
                border-right: 2px solid #e0e0e0;
                padding: 15px;
            }

            #rightPanel {
                background-color: #ffffff;
                padding: 20px;
                margin: 10px;
                border-radius: 10px;
            }

            /* ========== TÍTULOS E LABELS ========== */
            #panelTitle {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                background-color: #4a90e2;
                border-radius: 8px;
                margin-bottom: 15px;
            }

            #tableHeader {
                color: #4a90e2;
                font-size: 20px;
                font-weight: bold;
                padding: 10px 0;
                margin-bottom: 10px;
            }

            #sectionLabel {
                color: #4a90e2;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 5px 5px 5px;
            }

            #infoLabel {
                color: #666;
                font-size: 13px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #4a90e2;
                margin-top: 10px;
            }

            /* ========== BOTÕES ========== */
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                min-height: 40px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }

            QPushButton:hover {
                background-color: #357abd;
                box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.3);
            }

            QPushButton:pressed {
                background-color: #2d6cb1;
            }

            /* ========== CALENDÁRIO ========== */
            #calendar {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }

            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #4a90e2;
                color: white;
            }

            QCalendarWidget QToolButton {
                color: white;
                background-color: transparent;
                border-radius: 4px;
                padding: 5px;
            }

            QCalendarWidget QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }

            QCalendarWidget QMenu {
                background-color: white;
                color: #333;
            }

            QCalendarWidget QSpinBox {
                color: white;
                background-color: transparent;
                selection-background-color: rgba(255, 255, 255, 0.2);
            }

            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-background-color: #4a90e2;
                selection-color: white;
            }

            /* ========== TABELA ========== */
            #coursesTable {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                font-size: 14px;
            }

            #coursesTable::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }

            #coursesTable::item:selected {
                background-color: #4a90e2;
                color: white;
            }

            #coursesTable::item:hover {
                background-color: #f0f4f8;
            }

            QHeaderView::section {
                background-color: #4a90e2;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.2);
            }

            QHeaderView::section:first {
                border-top-left-radius: 6px;
            }

            QHeaderView::section:last {
                border-top-right-radius: 6px;
                border-right: none;
            }

            /* ========== SEPARADOR ========== */
            #separator {
                color: #e0e0e0;
                margin: 15px 0;
            }

            /* ========== INPUTS ========== */
            QLineEdit, QTimeEdit, QComboBox {
                background-color: white;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                color: #333;
            }

            QLineEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border: 2px solid #4a90e2;
                box-shadow: 0px 0px 8px rgba(74, 144, 226, 0.5);
            }

            /* ========== MENU ========== */
            QMenu {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 5px;
            }

            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
                margin: 2px 5px;
            }

            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }

            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 5px 10px;
            }
        """)

    def handle_single_click(self, clicked_date):
        date_str = clicked_date.toString("dd/MM/yyyy")
        self.atualizar_tabela_cursos(clicked_date)
        self.selected_dates_label.setText(f"Cursos programados para: {date_str}")

    def handle_double_click(self, clicked_date):
        self.abrir_programar_curso(clicked_date)

    def update_calendar_visual(self):
        default_format = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_format)

        programmed_format = QTextCharFormat()
        programmed_format.setBackground(QColor("lightgreen"))

        for date_str in self.programmed_dates:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            self.calendar.setDateTextFormat(date, programmed_format)

        selected_format = QTextCharFormat()
        selected_format.setBackground(QColor("lightblue"))

        for date_str in self.selected_dates:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            self.calendar.setDateTextFormat(date, selected_format)

    def atualizar_calendario(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT data FROM cursos_datas")
            datas = cursor.fetchall()
            conn.close()

            default_format = QTextCharFormat()
            self.calendar.setDateTextFormat(QDate(), default_format)

            future_format = QTextCharFormat()
            future_format.setBackground(QColor("lightgreen"))

            past_format = QTextCharFormat()
            past_format.setBackground(QColor("gray"))

            hoje = QDate.currentDate()

            for data in datas:
                data_qdate = QDate.fromString(data[0], "yyyy-MM-dd")
                if data_qdate < hoje:
                    self.calendar.setDateTextFormat(data_qdate, past_format)
                else:
                    self.calendar.setDateTextFormat(data_qdate, future_format)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar calendário: {str(e)}")

    def abrir_programacao_rapida(self):
        try:
            datas_selecionadas = set()

            dialog = QDialog(self)
            dialog.setWindowTitle("Programação Rápida de Curso")
            dialog.setGeometry(300, 300, 500, 600)
            dialog.setWindowIcon(QIcon("agenda.png"))

            layout = QVBoxLayout(dialog)

            layout.addWidget(QLabel("Selecione o Curso"))
            search_input = QLineEdit()
            search_input.setPlaceholderText("Pesquisar curso...")
            layout.addWidget(search_input)

            curso_combo = QComboBox()
            layout.addWidget(curso_combo)
            layout.addWidget(QLabel("Selecione o Instrutor"))
            instrutor_combo = QComboBox()
            layout.addWidget(instrutor_combo)

            def carregar_instrutores_do_curso():
                instrutor_combo.clear()
                curso_id = curso_combo.currentData()
                if not curso_id:
                    return

                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT instrutores.id, instrutores.nome
                    FROM instrutores_cursos
                    JOIN instrutores ON instrutores.id = instrutores_cursos.instrutor_id
                    WHERE instrutores_cursos.curso_id = ?
                    ORDER BY instrutores.nome ASC
                """, (curso_id,))
                instrutores = cursor.fetchall()
                conn.close()

                for iid, nome in instrutores:
                    instrutor_combo.addItem(nome, iid)

            curso_combo.currentIndexChanged.connect(carregar_instrutores_do_curso)

            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
            cursos = cursor.fetchall()
            conn.close()

            if not cursos:
                QMessageBox.warning(self, "Aviso", "Nenhum curso cadastrado!")
                return

            cursos_originais = cursos

            def filtrar_cursos(texto):
                texto = texto.lower()
                curso_combo.clear()
                for curso_id, curso_nome in cursos_originais:
                    if texto in curso_nome.lower():
                        curso_combo.addItem(curso_nome, curso_id)

            search_input.textChanged.connect(filtrar_cursos)
            filtrar_cursos("")
            carregar_instrutores_do_curso()

            layout.addWidget(QLabel("Selecione as Datas"))
            calendario = QCalendarWidget()
            layout.addWidget(calendario)

            def toggle_date(date):
                date_str = date.toString("yyyy-MM-dd")
                if date_str in datas_selecionadas:
                    datas_selecionadas.remove(date_str)
                else:
                    datas_selecionadas.add(date_str)
                update_calendar_visual()

            def update_calendar_visual():
                default_format = QTextCharFormat()
                calendario.setDateTextFormat(QDate(), default_format)
                highlight_format = QTextCharFormat()
                highlight_format.setBackground(QColor("lightblue"))
                for date_str in datas_selecionadas:
                    date = QDate.fromString(date_str, "yyyy-MM-dd")
                    calendario.setDateTextFormat(date, highlight_format)

            calendario.clicked.connect(toggle_date)

            layout.addWidget(QLabel("Hora do Curso"))
            hora_input = QTimeEdit()
            hora_input.setDisplayFormat("HH:mm")
            layout.addWidget(hora_input)

            salvar_button = QPushButton("Salvar Programação")
            salvar_button.clicked.connect(lambda: self.salvar_programacao_rapida(
                curso_combo.currentData(),
                instrutor_combo.currentData(),
                datas_selecionadas,
                hora_input.time().toString("HH:mm"),
                dialog
            ))
            layout.addWidget(salvar_button)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao abrir programação: {str(e)}")

    def salvar_programacao_rapida(self, curso_id, instrutor_id, datas, hora, dialog):
        if not curso_id or not datas:
            QMessageBox.warning(self, "Erro", "Selecione curso e pelo menos uma data.")
            return

        if not instrutor_id:
            QMessageBox.warning(self, "Erro", "Selecione o instrutor.")
            return

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT 1 FROM instrutores_cursos
                WHERE curso_id = ? AND instrutor_id = ?
                LIMIT 1
            """, (curso_id, instrutor_id))
            if not cursor.fetchone():
                QMessageBox.warning(self, "Erro", "Este instrutor não está associado ao curso selecionado.")
                return

            for date_str in datas:
                cursor.execute("""
                    INSERT INTO cursos_datas (curso_id, data, hora, instrutor_id)
                    VALUES (?, ?, ?, ?)
                """, (curso_id, date_str, hora, instrutor_id))

            conn.commit()
            QMessageBox.information(self, "Sucesso", "Cursos programados com sucesso!")

            self.atualizar_calendario()
            datas.clear()
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao programar cursos: {str(e)}")
        finally:
            conn.close()

    def atualizar_tabela_cursos(self, qdate):
        if isinstance(qdate, str):
            qdate = QDate.fromString(qdate, "yyyy-MM-dd")
            if not qdate.isValid():
                return

        if not isinstance(qdate, QDate):
            return

        try:
            data = qdate.toString("yyyy-MM-dd")

            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    cursos.nome as curso_nome,
                    instrutores.nome as instrutor_nome,
                    cursos_datas.hora,
                    cursos_datas.id as prog_id,
                    cursos.id as curso_id
                FROM cursos_datas
                JOIN cursos ON cursos.id = cursos_datas.curso_id
                JOIN instrutores ON instrutores.id = cursos_datas.instrutor_id
                WHERE cursos_datas.data = ?
                ORDER BY cursos_datas.hora
            ''', (data,))
            cursos = cursor.fetchall()
            conn.close()

            self.tabela.setRowCount(0)

            for row, (curso_nome, instrutor_nome, hora, prog_id, curso_id) in enumerate(cursos):
                self.tabela.insertRow(row)

                curso_item = QTableWidgetItem(curso_nome)
                curso_item.setFlags(curso_item.flags() & ~Qt.ItemIsEditable)
                curso_item.setData(Qt.UserRole, prog_id)
                curso_item.setData(Qt.UserRole + 1, curso_id)

                instrutor_item = QTableWidgetItem(instrutor_nome)
                instrutor_item.setFlags(instrutor_item.flags() & ~Qt.ItemIsEditable)

                hora_item = QTableWidgetItem(hora)
                hora_item.setFlags(hora_item.flags() & ~Qt.ItemIsEditable)

                self.tabela.setItem(row, 0, curso_item)
                self.tabela.setItem(row, 1, instrutor_item)
                self.tabela.setItem(row, 2, hora_item)

            if self.tabela.rowCount() == 0:
                self.tabela.insertRow(0)
                item = QTableWidgetItem("Nenhum curso programado para esta data")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self.tabela.setSpan(0, 0, 1, 3)
                self.tabela.setItem(0, 0, item)

        except Exception as e:
            print(f"Erro ao atualizar tabela de cursos: {e}")

    def abrir_programar_curso(self, qdate):
        if not isinstance(qdate, QDate):
            return

        data = qdate.toString("yyyy-MM-dd")
        janela_programacao = ProgramarCursoWindow(data, self)
        janela_programacao.setModal(True)
        janela_programacao.exec_()

        self.atualizar_calendario()
        self.atualizar_tabela_cursos(self.calendar.selectedDate())

    def abrir_detalhes_programacao(self, item):
        row = item.row()
        curso_item = self.tabela.item(row, 0)
        if not curso_item:
            return
        prog_id = curso_item.data(Qt.UserRole)
        curso_id = curso_item.data(Qt.UserRole + 1)
        data = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if prog_id and curso_id:
            janela = DetalhesProgramacaoWindow(prog_id, curso_id, data, self)
            janela.exec_()
            self.atualizar_calendario()
            self.atualizar_tabela_cursos(self.calendar.selectedDate())

    def criar_menu_acoes(self):
        menu = QMenu()
        menu.addAction(QAction(QIcon("conectar.png"), "Associar Cursos a Instrutor", self,
                               triggered=self.abrir_associar_curso))
        menu.addAction(QAction(QIcon("cadastre-se.png"), "Cadastrar Curso", self,
                               triggered=self.abrir_cadastro_curso))
        menu.addAction(QAction(QIcon("cadastre-se.png"), "Cadastrar Instrutor", self,
                               triggered=self.abrir_cadastro_instrutor))
        menu.addAction(QAction(QIcon("editar.png"), "Editar/Excluir Curso", self,
                               triggered=self.abrir_editar_excluir_curso))
        menu.addAction(QAction(QIcon("editar.png"), "Editar Instrutor", self,
                               triggered=self.abrir_editar_instrutor))
        menu.addAction(QAction(QIcon("excluir.png"), "Excluir Instrutor", self,
                               triggered=self.abrir_excluir_instrutor))
        menu.addAction(QAction(QIcon("informacoes.png"), "Exibir Cursos (Tema e Descrição)", self,
                               triggered=self.abrir_exibir_cursos))
        menu.addAction(QAction(QIcon("informacoes.png"), "Exibir Informações dos Instrutores", self,
                               triggered=self.abrir_exibir_instrutores))
        menu.addAction(QAction(QIcon("historico.png"), "Ver Histórico", self,
                               triggered=self.abrir_historico))
        menu.addSeparator()
        menu.addAction(QAction(QIcon("conectar.png"), "Configurar Email (SMTP)", self,
                               triggered=self.abrir_config_email))
        return menu

    def abrir_cadastro_instrutor(self):
        CadastroInstrutorWindow(self).exec_()

    def abrir_cadastro_curso(self):
        CadastroCursoWindow(self).exec_()

    def abrir_associar_curso(self):
        AssociarCursoWindow(self).exec_()

    def abrir_editar_instrutor(self):
        EditarInstrutorWindow(self).exec_()

    def abrir_excluir_instrutor(self):
        ExcluirInstrutorWindow(self).exec_()

    def abrir_exibir_instrutores(self):
        ExibirInstrutoresWindow(self).exec_()

    def abrir_historico(self):
        HistoricoWindow(self).exec_()

    def abrir_editar_excluir_curso(self):
        ExcluirCursoWindow(self).exec_()

    def abrir_exibir_cursos(self):
        ExibirCursosWindow(self).exec_()

    def abrir_config_email(self):
        ConfigEmailWindow(self).exec_()


# Janela de Configuração de Email (SMTP)
class ConfigEmailWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração de Email (SMTP)")
        self.setWindowIcon(QIcon("conectar.png"))
        self.setGeometry(300, 300, 600, 500)
        
        layout = QVBoxLayout()
        
        # Grupo: Configurações do Servidor
        server_group = QGroupBox("Servidor SMTP")
        server_layout = QFormLayout()
        
        self.smtp_host = QLineEdit()
        self.smtp_host.setPlaceholderText("Ex: smtp.gmail.com")
        server_layout.addRow("Servidor SMTP:", self.smtp_host)
        
        self.smtp_port = QLineEdit()
        self.smtp_port.setPlaceholderText("Ex: 587")
        self.smtp_port.setValidator(QIntValidator(1, 65535))
        server_layout.addRow("Porta:", self.smtp_port)
        
        self.smtp_user = QLineEdit()
        self.smtp_user.setPlaceholderText("seu@email.com")
        server_layout.addRow("Usuário:", self.smtp_user)
        
        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.Password)
        self.smtp_password.setPlaceholderText("Senha ou App Password")
        server_layout.addRow("Senha:", self.smtp_password)
        
        self.smtp_from_name = QLineEdit()
        self.smtp_from_name.setPlaceholderText("Nome do Remetente")
        server_layout.addRow("Nome Remetente:", self.smtp_from_name)
        
        self.smtp_use_tls = QCheckBox("Usar TLS/SSL")
        self.smtp_use_tls.setChecked(True)
        server_layout.addRow("", self.smtp_use_tls)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Grupo: Teste de Conexão
        test_group = QGroupBox("Testar Conexão")
        test_layout = QVBoxLayout()
        
        self.test_email = QLineEdit()
        self.test_email.setPlaceholderText("Email para teste")
        test_layout.addWidget(self.test_email)
        
        btn_test = QPushButton("Enviar Email de Teste")
        btn_test.clicked.connect(self.testar_conexao)
        test_layout.addWidget(btn_test)
        
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        test_layout.addWidget(self.test_result)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_salvar = QPushButton("Salvar Configuração")
        btn_salvar.clicked.connect(self.salvar_config)
        btn_layout.addWidget(btn_salvar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancelar)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.carregar_config()
    
    def carregar_config(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_config (
                    id INTEGER PRIMARY KEY,
                    smtp_host TEXT,
                    smtp_port INTEGER,
                    smtp_user TEXT,
                    smtp_password TEXT,
                    smtp_from_name TEXT,
                    smtp_use_tls INTEGER DEFAULT 1
                )
            """)
            cursor.execute("SELECT smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_name, smtp_use_tls FROM email_config LIMIT 1")
            config = cursor.fetchone()
            conn.close()
            
            if config:
                self.smtp_host.setText(config[0] or "")
                self.smtp_port.setText(str(config[1]) if config[1] else "")
                self.smtp_user.setText(config[2] or "")
                self.smtp_password.setText(config[3] or "")
                self.smtp_from_name.setText(config[4] or "")
                self.smtp_use_tls.setChecked(bool(config[5]))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar configuração: {str(e)}")
    
    def salvar_config(self):
        host = self.smtp_host.text().strip()
        port = self.smtp_port.text().strip()
        user = self.smtp_user.text().strip()
        password = self.smtp_password.text()
        from_name = self.smtp_from_name.text().strip()
        use_tls = 1 if self.smtp_use_tls.isChecked() else 0
        
        if not host or not port or not user:
            QMessageBox.warning(self, "Erro", "Preencha servidor, porta e usuário.")
            return
        
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_config (
                    id INTEGER PRIMARY KEY,
                    smtp_host TEXT,
                    smtp_port INTEGER,
                    smtp_user TEXT,
                    smtp_password TEXT,
                    smtp_from_name TEXT,
                    smtp_use_tls INTEGER DEFAULT 1
                )
            """)
            cursor.execute("DELETE FROM email_config")
            cursor.execute("""
                INSERT INTO email_config (smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_name, smtp_use_tls)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (host, int(port), user, password, from_name, use_tls))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sucesso", "Configuração salva com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")
    
    def testar_conexao(self):
        test_email = self.test_email.text().strip()
        if not test_email or "@" not in test_email:
            QMessageBox.warning(self, "Erro", "Informe um email válido para teste.")
            return
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            host = self.smtp_host.text().strip()
            port = int(self.smtp_port.text().strip())
            user = self.smtp_user.text().strip()
            password = self.smtp_password.text()
            from_name = self.smtp_from_name.text().strip() or user
            use_tls = self.smtp_use_tls.isChecked()
            
            msg = MIMEMultipart()
            msg['From'] = f"{from_name} <{user}>"
            msg['To'] = test_email
            msg['Subject'] = "Teste de Configuração SMTP - Gestor Cursos"
            
            body = "Este é um email de teste da configuração SMTP do sistema Gestor de Cursos.\n\nSe você recebeu este email, a configuração está funcionando corretamente!"
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()
            server.login(user, password)
            server.send_message(msg)
            server.quit()
            
            self.test_result.setText(f"✓ Email de teste enviado com sucesso para {test_email}")
            self.test_result.setStyleSheet("color: green;")
            
        except Exception as e:
            self.test_result.setText(f"✗ Erro ao enviar: {str(e)}")
            self.test_result.setStyleSheet("color: red;")


# ---------------- Configurações de Atualização ----------------
REPO_OWNER = "JeffVane"
REPO_NAME = "gestorcursos"
BRANCH = "main"

VERSION_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/version.txt"
LOCAL_VERSION_FILE = "version.txt"

LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
INSTALLER_ASSET_NAME = "GestaoDeCursos_Setup.exe"
# --------------------------------------------------------------


def get_remote_version():
    try:
        r = requests.get(VERSION_URL, timeout=10)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None


def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "0.0.0"


def parse_version(v: str) -> Version:
    try:
        return Version(v.strip())
    except InvalidVersion:
        return Version("0.0.0")


def get_latest_installer_url():
    r = requests.get(LATEST_RELEASE_API, timeout=10)
    r.raise_for_status()
    data = r.json()
    for a in data.get("assets", []):
        if a.get("name") == INSTALLER_ASSET_NAME:
            return a.get("browser_download_url")
    raise RuntimeError(f"Asset '{INSTALLER_ASSET_NAME}' não encontrado no Latest Release.")


class DownloadThread(QThread):
    progress_update = pyqtSignal(int, float, float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, download_url: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url

    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            installer_path = os.path.join(temp_dir, INSTALLER_ASSET_NAME)

            with requests.get(self.download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 2 * 1024 * 1024

                with open(installer_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                percent = int((downloaded / total) * 100)
                                mb_down = downloaded / (1024 * 1024)
                                mb_total = total / (1024 * 1024)
                                self.progress_update.emit(percent, mb_down, mb_total)

            self.finished.emit(installer_path)
        except Exception as e:
            self.error.emit(str(e))


def verificar_atualizacao():
    if sys.platform != 'win32':
        return False

    remote_txt = get_remote_version()
    local_txt = get_local_version()

    if not remote_txt:
        return False

    remote = parse_version(remote_txt)
    local = parse_version(local_txt)

    if remote <= local:
        return False

    if not QApplication.instance():
        _ = QApplication(sys.argv)

    resposta = QMessageBox.question(
        None,
        "Atualização disponível",
        f"Uma nova versão do sistema está disponível!\n\n"
        f"Versão atual: {local}\nNova versão: {remote}\n\n"
        f"Deseja baixar e instalar agora?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes
    )

    if resposta != QMessageBox.Yes:
        return False

    try:
        installer_url = get_latest_installer_url()
    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Não foi possível localizar o instalador no GitHub Releases:\n{e}")
        return False

    progress = QProgressDialog("Preparando download...", "Cancelar", 0, 100)
    progress.setWindowTitle("Baixando Atualização")
    progress.setWindowModality(Qt.WindowModal)
    progress.setMinimumWidth(420)
    progress.setValue(0)
    progress.show()

    thread = DownloadThread(installer_url)

    def atualizar_barra(percent, mb_down, mb_total):
        progress.setValue(percent)
        progress.setLabelText(f"Baixando: {mb_down:.1f} MB de {mb_total:.1f} MB")

    def ao_finalizar(caminho):
        progress.close()
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(None, "runas", caminho, None, None, 1)
            sys.exit(0)
        else:
            QMessageBox.information(None, "Download concluído", f"Instalador salvo em:\n{caminho}\n\nExecute manualmente para instalar.")
            loop.quit()

    def ao_errar(mensagem):
        progress.close()
        QMessageBox.critical(None, "Erro", f"Erro ao baixar instalador:\n{mensagem}")
        loop.quit()

    thread.progress_update.connect(atualizar_barra)
    thread.finished.connect(ao_finalizar)
    thread.error.connect(ao_errar)

    loop = QEventLoop()
    thread.finished.connect(loop.quit)
    thread.error.connect(loop.quit)

    thread.start()
    loop.exec_()

    return True


if __name__ == '__main__':
    criar_banco()
    app = QApplication(sys.argv)
    atualizado = verificar_atualizacao()
    if not atualizado:
        janela = MainWindow()
        janela.show()
        atualizar_banco()
        sys.exit(app.exec_())
    else:
        sys.exit(0)