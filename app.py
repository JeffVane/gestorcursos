from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QCalendarWidget, QDialog,
    QMessageBox, QListWidget, QListWidgetItem, QMenu, QAction, QComboBox,QTimeEdit,QHBoxLayout,QHeaderView
)
import sqlite3
from PyQt5.QtCore import Qt,QDate,QTime
from PyQt5.QtGui import QTextCharFormat, QColor, QIcon
from reportlab.lib.pagesizes import letter
from PyQt5.QtWidgets import QFileDialog
import sys
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit

# Configuração do banco de dados
def criar_banco():
    conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
    cursor = conn.cursor()

    # Criar tabela de instrutores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instrutores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        niveis_formacao TEXT,
        modalidades TEXT
    )
    ''')

    # Criar tabela de cursos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL
    )
    ''')

    # Criar tabela de datas de cursos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cursos_datas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        hora TEXT,
        instrutor_id INTEGER,
        FOREIGN KEY(curso_id) REFERENCES cursos(id),
        FOREIGN KEY(instrutor_id) REFERENCES instrutores(id)
    )
    ''')

    # Criar tabela de associação entre instrutores e cursos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instrutores_cursos (
        instrutor_id INTEGER,
        curso_id INTEGER,
        FOREIGN KEY(instrutor_id) REFERENCES instrutores(id),
        FOREIGN KEY(curso_id) REFERENCES cursos(id),
        PRIMARY KEY(instrutor_id, curso_id)
    )
    ''')

    conn.commit()
    conn.close()

def atualizar_banco():
    conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
    cursor = conn.cursor()

    # Verificar e adicionar colunas na tabela 'instrutores'
    cursor.execute("PRAGMA table_info(instrutores)")
    colunas_instrutores = [coluna[1] for coluna in cursor.fetchall()]

    if "niveis_formacao" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN niveis_formacao TEXT")
    if "modalidades" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN modalidades TEXT")

    # Verificar e adicionar colunas na tabela 'cursos_datas'
    cursor.execute("PRAGMA table_info(cursos_datas)")
    colunas_cursos_datas = [coluna[1] for coluna in cursor.fetchall()]

    if "hora" not in colunas_cursos_datas:
        cursor.execute("ALTER TABLE cursos_datas ADD COLUMN hora TEXT")
    if "instrutor_id" not in colunas_cursos_datas:
        cursor.execute("ALTER TABLE cursos_datas ADD COLUMN instrutor_id INTEGER")

    conn.commit()
    conn.close()


def atualizar_banco():
    conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
    cursor = conn.cursor()

    # Verificar se a coluna 'niveis_formacao' existe
    cursor.execute("PRAGMA table_info(instrutores)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]

    if "niveis_formacao" not in colunas:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN niveis_formacao TEXT")
    if "modalidades" not in colunas:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN modalidades TEXT")

    conn.commit()
    conn.close()

# Janela de cadastro de instrutores
class CadastroInstrutorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Cadastrar Instrutor")
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout()

        # Campo de nome do instrutor
        layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        layout.addWidget(self.instrutor_input)

        # Nível de Formação
        layout.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        niveis_formacao = ["Doutor", "Especialista", "Graduação", "Mestre"]
        for nivel in niveis_formacao:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        layout.addWidget(self.niveis_formacao_list)

        # Modalidade
        layout.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        modalidades = ["Presencial", "On-line", "Conteudista"]
        for modalidade in modalidades:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        layout.addWidget(self.modalidades_list)

        # Botão para cadastrar
        self.add_button = QPushButton("Cadastrar")
        self.add_button.clicked.connect(self.cadastrar_instrutor)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def cadastrar_instrutor(self):
        nome = self.instrutor_input.text()
        niveis_selecionados = [item.text() for item in self.niveis_formacao_list.selectedItems()]
        modalidades_selecionadas = [item.text() for item in self.modalidades_list.selectedItems()]

        if nome and niveis_selecionados and modalidades_selecionadas:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO instrutores (nome, niveis_formacao, modalidades) VALUES (?, ?, ?)",
                (nome, ",".join(niveis_selecionados), ",".join(modalidades_selecionadas))
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sucesso", f'Instrutor "{nome}" cadastrado com sucesso!')
            self.instrutor_input.clear()
            self.niveis_formacao_list.clearSelection()
            self.modalidades_list.clearSelection()

        else:
            QMessageBox.warning(self, "Erro", "Preencha o nome e selecione pelo menos um nível de formação e uma modalidade.")

# Janela para editar instrutor
class EditarInstrutorWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("editar.png"))
        self.setWindowTitle("Editar Instrutor")
        self.setGeometry(200, 200, 800, 600)
        layout = QVBoxLayout()

        # Seleção de instrutor
        layout.addWidget(QLabel("Selecione o Instrutor"))
        self.instrutor_combo = QComboBox()
        self.instrutor_combo.currentIndexChanged.connect(self.carregar_dados_instrutor)
        layout.addWidget(self.instrutor_combo)

        # Campo de nome
        layout.addWidget(QLabel("Nome do Instrutor"))
        self.instrutor_input = QLineEdit()
        layout.addWidget(self.instrutor_input)

        # Níveis de Formação
        layout.addWidget(QLabel("Nível de Formação"))
        self.niveis_formacao_list = QListWidget()
        self.niveis_formacao_list.setSelectionMode(QListWidget.MultiSelection)
        niveis_formacao = ["Doutor", "Especialista", "Graduação", "Mestre"]
        for nivel in niveis_formacao:
            self.niveis_formacao_list.addItem(QListWidgetItem(nivel))
        layout.addWidget(self.niveis_formacao_list)

        # Modalidades
        layout.addWidget(QLabel("Modalidade"))
        self.modalidades_list = QListWidget()
        self.modalidades_list.setSelectionMode(QListWidget.MultiSelection)
        modalidades = ["Presencial", "On-line", "Conteudista"]
        for modalidade in modalidades:
            self.modalidades_list.addItem(QListWidgetItem(modalidade))
        layout.addWidget(self.modalidades_list)

        # Cursos associados
        layout.addWidget(QLabel("Cursos Associados"))
        self.cursos_list = QListWidget()
        self.cursos_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.cursos_list)

        # Botão para salvar alterações
        self.save_button = QPushButton("Salvar Alterações")
        self.save_button.clicked.connect(self.salvar_alteracoes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.carregar_instrutores()

    def carregar_instrutores(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Selecionar instrutores em ordem alfabética
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            conn.close()

            # Limpar a combobox e adicionar os instrutores ordenados
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
            cursor.execute("SELECT nome, niveis_formacao, modalidades FROM instrutores WHERE id = ?", (instrutor_id,))
            instrutor = cursor.fetchone()

            if instrutor:
                nome, niveis_formacao, modalidades = instrutor
                self.instrutor_input.setText(nome)

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

                # Carregar todos os cursos em ordem alfabética
                cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
                todos_cursos = cursor.fetchall()
                for curso_id, curso_nome in todos_cursos:
                    item = QListWidgetItem(curso_nome)
                    item.setData(Qt.UserRole, curso_id)
                    self.cursos_list.addItem(item)

                # Destacar cursos associados
                cursor.execute("""
                    SELECT curso_id
                    FROM instrutores_cursos
                    WHERE instrutor_id = ?
                """, (instrutor_id,))
                cursos_associados = [row[0] for row in cursor.fetchall()]
                for i in range(self.cursos_list.count()):
                    item = self.cursos_list.item(i)
                    if item.data(Qt.UserRole) in cursos_associados:
                        item.setSelected(True)

            else:
                QMessageBox.warning(self, "Erro", "Os dados do instrutor não foram encontrados.")

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Ocorreu um erro: {str(e)}")

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
            UPDATE instrutores
            SET nome = ?, niveis_formacao = ?, modalidades = ?
            WHERE id = ?
        """, (nome, ",".join(niveis_selecionados), ",".join(modalidades_selecionadas), instrutor_id))

        # Atualizar cursos associados
        cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
        for curso_id in cursos_selecionados:
            cursor.execute("INSERT INTO instrutores_cursos (instrutor_id, curso_id) VALUES (?, ?)", (instrutor_id, curso_id))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Sucesso", f"Instrutor '{nome}' atualizado com sucesso!")

# Janela de cadastro de cursos
class CadastroCursoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("cadastre-se.png"))
        self.setWindowTitle("Cadastrar Curso")
        self.setGeometry(200, 200, 600, 200)
        layout = QVBoxLayout()

        # Campo para nome do curso
        layout.addWidget(QLabel("Nome do Curso"))
        self.curso_input = QLineEdit()
        self.curso_input.textChanged.connect(self.corrigir_nome_curso)  # Conectar para correção automática
        layout.addWidget(self.curso_input)

        # Campo para seleção do tema
        layout.addWidget(QLabel("Tema do Curso"))
        self.tema_combo = QComboBox()
        temas = ["Contabilidade", "Direito", "Especializações", "Ética",
                 "Ferramentas", "Gestão", "Recursos Humanos", "Tecnologia",
                 "Tributos e Obrigações Acessórias"]
        self.tema_combo.addItems(temas)
        layout.addWidget(self.tema_combo)

        # Botão de cadastro
        self.add_button = QPushButton("Cadastrar")
        self.add_button.clicked.connect(self.cadastrar_curso)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def corrigir_nome_curso(self):
        """Corrige espaços extras automaticamente enquanto o usuário digita."""
        texto_corrigido = " ".join(self.curso_input.text().split()).strip()

        # Atualiza o campo apenas se houver alteração
        if self.curso_input.text() != texto_corrigido:
            self.curso_input.setText(texto_corrigido)

    def cadastrar_curso(self):
        nome = self.curso_input.text()
        tema = self.tema_combo.currentText()

        if nome:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            cursor.execute("PRAGMA table_info(cursos)")
            colunas = [coluna[1] for coluna in cursor.fetchall()]
            if "tema" not in colunas:
                cursor.execute("ALTER TABLE cursos ADD COLUMN tema TEXT")

            cursor.execute("INSERT INTO cursos (nome, tema) VALUES (?, ?)", (nome, tema))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", f'Curso "{nome}" cadastrado com sucesso!\nTema: {tema}')
            self.curso_input.clear()
            self.tema_combo.setCurrentIndex(0)

        else:
            QMessageBox.warning(self, "Erro", "Preencha o nome do curso.")



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

        self.selecao_temporaria = {}  # Dicionário para salvar seleções temporárias
        self.carregar_dados()

    def carregar_dados(self):
        """Carrega os instrutores e cursos do banco de dados em ordem alfabética."""
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()

        # Carregar instrutores em ordem alfabética
        cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
        instrutores = cursor.fetchall()
        for instrutor in instrutores:
            self.instrutor_combo.addItem(instrutor[1], instrutor[0])

        # Carregar cursos em ordem alfabética
        cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
        cursos = cursor.fetchall()
        for curso in cursos:
            item = QListWidgetItem(curso[1])
            item.setData(1, curso[0])
            self.cursos_list.addItem(item)

        conn.close()

        # Carregar os cursos associados para o primeiro instrutor
        self.alternar_instrutor()

    def alternar_instrutor(self):
        """Salva as seleções atuais e carrega os cursos associados ao instrutor selecionado."""
        instrutor_id_anterior = self.instrutor_combo.itemData(self.instrutor_combo.currentIndex() - 1)
        instrutor_id_atual = self.instrutor_combo.currentData()

        # Salvar seleções temporárias do instrutor anterior
        if instrutor_id_anterior:
            cursos_selecionados = [item.data(1) for item in self.cursos_list.selectedItems()]
            self.selecao_temporaria[instrutor_id_anterior] = set(cursos_selecionados)

        # Limpar a seleção atual
        for i in range(self.cursos_list.count()):
            self.cursos_list.item(i).setSelected(False)

        # Restaurar seleções temporárias ou carregar cursos do banco
        if instrutor_id_atual in self.selecao_temporaria:
            cursos_temporarios = self.selecao_temporaria[instrutor_id_atual]
            for i in range(self.cursos_list.count()):
                if self.cursos_list.item(i).data(1) in cursos_temporarios:
                    self.cursos_list.item(i).setSelected(True)
        else:
            self.carregar_cursos_associados(instrutor_id_atual)

    def carregar_cursos_associados(self, instrutor_id):
        """Carrega os cursos já associados ao instrutor selecionado."""
        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()

        # Buscar os IDs dos cursos associados ao instrutor
        cursor.execute("""
            SELECT curso_id FROM instrutores_cursos WHERE instrutor_id = ?
        """, (instrutor_id,))
        cursos_associados = {row[0] for row in cursor.fetchall()}

        conn.close()

        # Marcar os cursos associados
        for i in range(self.cursos_list.count()):
            item = self.cursos_list.item(i)
            if item.data(1) in cursos_associados:
                item.setSelected(True)

    def associar_cursos(self):
        """Associa os cursos selecionados ao instrutor no banco de dados."""
        instrutor_id = self.instrutor_combo.currentData()
        cursos_selecionados = [item.data(1) for item in self.cursos_list.selectedItems()]

        if instrutor_id and cursos_selecionados:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Remover associações antigas
            cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))

            # Inserir novas associações
            for curso_id in cursos_selecionados:
                cursor.execute("INSERT INTO instrutores_cursos (instrutor_id, curso_id) VALUES (?, ?)",
                               (instrutor_id, curso_id))

            conn.commit()
            conn.close()

            # Atualizar seleções confirmadas
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

            # Selecionar instrutores em ordem alfabética
            cursor.execute("SELECT id, nome FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()
            conn.close()

            # Limpar a combobox e adicionar os instrutores ordenados
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

            resposta = QMessageBox.question(
                self,
                "Confirmação",
                "Tem certeza de que deseja excluir este instrutor? Essa ação não pode ser desfeita.",
                QMessageBox.Yes | QMessageBox.No
            )
            if resposta == QMessageBox.Yes:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()

                # Excluir associações de cursos
                cursor.execute("DELETE FROM instrutores_cursos WHERE instrutor_id = ?", (instrutor_id,))
                # Excluir o instrutor
                cursor.execute("DELETE FROM instrutores WHERE id = ?", (instrutor_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Sucesso", "Instrutor excluído com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir instrutor: {str(e)}")
class ProgramarCursoWindow(QDialog):
    def __init__(self, data_selecionada, parent=None, curso_id=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("agenda.png"))
        self.setWindowTitle("Programar/Editar Curso")
        self.setGeometry(300, 300, 800, 500)

        self.data_selecionada = data_selecionada
        self.curso_programado_id = None  # ID da programação existente

        layout = QVBoxLayout()

        # Exibir a data selecionada
        layout.addWidget(QLabel(f"Data Selecionada: {self.data_selecionada}"))

        # Lista de programações existentes
        layout.addWidget(QLabel("Programações Existentes:"))
        self.programacoes_list = QListWidget()
        self.programacoes_list.itemClicked.connect(self.carregar_programacao)
        layout.addWidget(self.programacoes_list)

        # Campos de edição
        self.form_widget = QWidget()
        form_layout = QVBoxLayout()

        # Selecionar Instrutor
        form_layout.addWidget(QLabel("Selecione o Instrutor"))
        self.instrutor_combo = QComboBox()
        form_layout.addWidget(self.instrutor_combo)

        # Selecionar Curso
        form_layout.addWidget(QLabel("Selecione o Curso"))
        self.curso_combo = QComboBox()
        form_layout.addWidget(self.curso_combo)

        # Selecionar Hora
        form_layout.addWidget(QLabel("Selecione a Hora"))
        self.hora_input = QTimeEdit()
        self.hora_input.setDisplayFormat("HH:mm")
        form_layout.addWidget(self.hora_input)

        self.form_widget.setLayout(form_layout)
        layout.addWidget(self.form_widget)

        # Botões
        button_layout = QHBoxLayout()

        self.salvar_button = QPushButton("Salvar")
        self.salvar_button.clicked.connect(self.salvar_programacao)
        button_layout.addWidget(self.salvar_button)

        self.excluir_button = QPushButton("Excluir")
        self.excluir_button.clicked.connect(self.excluir_programacao)
        self.excluir_button.setEnabled(False)  # Inicialmente desabilitado
        button_layout.addWidget(self.excluir_button)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancelar_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Carregar os dados
        self.carregar_instrutores()
        self.carregar_cursos()
        self.carregar_programacoes_existentes()

    # Removi o método reject() que estava causando o problema

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
                cursos_datas.id,
                cursos.nome as curso_nome,
                instrutores.nome as instrutor_nome,
                cursos_datas.hora
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
            item.setData(Qt.UserRole, prog_id)  # Guardar o ID da programação
            self.programacoes_list.addItem(item)

    def carregar_programacao(self, item):
        self.curso_programado_id = item.data(Qt.UserRole)
        self.excluir_button.setEnabled(True)

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                cursos_datas.curso_id,
                cursos_datas.instrutor_id,
                cursos_datas.hora
            FROM cursos_datas
            WHERE cursos_datas.id = ?
        """, (self.curso_programado_id,))
        programacao = cursor.fetchone()
        conn.close()

        if programacao:
            curso_id, instrutor_id, hora = programacao

            # Selecionar o curso
            index = self.curso_combo.findData(curso_id)
            if index >= 0:
                self.curso_combo.setCurrentIndex(index)

            # Selecionar o instrutor
            index = self.instrutor_combo.findData(instrutor_id)
            if index >= 0:
                self.instrutor_combo.setCurrentIndex(index)

            # Definir a hora
            hora_obj = QTime.fromString(hora, "HH:mm")
            self.hora_input.setTime(hora_obj)

    def salvar_programacao(self):
        curso_id = self.curso_combo.currentData()
        hora = self.hora_input.time().toString("HH:mm")

        if not curso_id:
            QMessageBox.warning(self, "Erro", "Selecione o curso.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Obter instrutores associados ao curso
            cursor.execute("""
                SELECT instrutor_id FROM instrutores_cursos
                WHERE curso_id = ?
                ORDER BY instrutor_id
            """, (curso_id,))
            instrutores = [row[0] for row in cursor.fetchall()]

            if not instrutores:
                QMessageBox.warning(self, "Erro", "Nenhum instrutor associado ao curso.")
                return

            # Identificar o último instrutor que ministrou o curso
            cursor.execute("""
                SELECT instrutor_id FROM cursos_datas
                WHERE curso_id = ?
                ORDER BY data DESC, hora DESC LIMIT 1
            """, (curso_id,))
            ultimo_instrutor = cursor.fetchone()

            if ultimo_instrutor:
                ultimo_instrutor_id = ultimo_instrutor[0]
                # Determinar o próximo instrutor no rodízio
                if ultimo_instrutor_id in instrutores:
                    proximo_instrutor_index = (instrutores.index(ultimo_instrutor_id) + 1) % len(instrutores)
                else:
                    proximo_instrutor_index = 0
            else:
                # Se não houver histórico, use o primeiro instrutor na lista
                proximo_instrutor_index = 0

            instrutor_id = instrutores[proximo_instrutor_index]

            # Inserir ou atualizar a programação no banco de dados
            if self.curso_programado_id:  # Atualizar
                cursor.execute("""
                    UPDATE cursos_datas
                    SET curso_id = ?, instrutor_id = ?, hora = ?
                    WHERE id = ?
                """, (curso_id, instrutor_id, hora, self.curso_programado_id))
                mensagem = "Programação atualizada com sucesso!"
            else:  # Nova programação
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
            self,
            "Confirmação",
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

class ExibirInstrutoresWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("informacoes.png"))
        self.setWindowTitle("Informações dos Instrutores")
        self.setGeometry(300, 300, 1500, 800)
        layout = QVBoxLayout()

        # Tabela para exibir informações
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)  # Nome, Níveis de Formação, Modalidades, Cursos
        self.tabela.setHorizontalHeaderLabels(["Nome", "Níveis de Formação", "Modalidades", "Cursos Associados"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setColumnWidth(0, 250)
        self.tabela.setColumnWidth(1, 250)
        self.tabela.setColumnWidth(2, 250)
        self.tabela.setColumnWidth(3, 400)
        layout.addWidget(self.tabela)

        self.setLayout(layout)
        self.carregar_instrutores()

    def carregar_instrutores(self):
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Buscar dados dos instrutores
            cursor.execute("SELECT id, nome, niveis_formacao, modalidades FROM instrutores ORDER BY nome ASC")
            instrutores = cursor.fetchall()

            # Buscar cursos associados para cada instrutor
            self.tabela.setRowCount(len(instrutores))
            for row, (instrutor_id, nome, niveis_formacao, modalidades) in enumerate(instrutores):
                # Adicionar dados do instrutor
                item_nome = QTableWidgetItem(nome)
                item_nome.setFlags(item_nome.flags() & ~Qt.ItemIsEditable)  # Tornar a célula não editável
                self.tabela.setItem(row, 0, item_nome)

                item_niveis = QTableWidgetItem(niveis_formacao or "")
                item_niveis.setFlags(item_niveis.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 1, item_niveis)

                item_modalidades = QTableWidgetItem(modalidades or "")
                item_modalidades.setFlags(item_modalidades.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 2, item_modalidades)

                # Buscar cursos associados
                cursor.execute("""
                       SELECT cursos.nome
                       FROM instrutores_cursos
                       JOIN cursos ON cursos.id = instrutores_cursos.curso_id
                       WHERE instrutores_cursos.instrutor_id = ?
                   """, (instrutor_id,))
                cursos = [curso[0] for curso in cursor.fetchall()]

                item_cursos = QTableWidgetItem(", ".join(cursos))
                item_cursos.setFlags(item_cursos.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, 3, item_cursos)

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar instrutores: {str(e)}")

class HistoricoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Histórico de Cursos")
        self.setGeometry(300, 300, 1350, 600)
        self.setWindowIcon(QIcon("historico.png"))

        layout = QVBoxLayout()

        # Campo de pesquisa
        search_layout = QHBoxLayout()
        search_label = QLabel("Pesquisar:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para pesquisar...")
        self.search_input.textChanged.connect(self.aplicar_filtros)

        # Filtro por mês
        self.mes_combo = QComboBox()
        self.mes_combo.addItem("Todos os meses", None)
        for mes in range(1, 13):
            self.mes_combo.addItem(QDate.longMonthName(mes), mes)
        self.mes_combo.currentIndexChanged.connect(self.aplicar_filtros)

        # Adicionar ao layout de busca e filtros
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(QLabel("Filtrar por Mês:"))
        search_layout.addWidget(self.mes_combo)

        layout.addLayout(search_layout)

        # Tabela de histórico
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Curso", "Instrutor", "Datas", "Horário"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setColumnWidth(0, 650)
        self.tabela.setColumnWidth(1, 300)
        self.tabela.setColumnWidth(2, 200)
        layout.addWidget(self.tabela)

        # Botão de exportação para PDF
        self.exportar_pdf_button = QPushButton("Exportar para PDF")
        self.exportar_pdf_button.clicked.connect(self.exportar_para_pdf)
        layout.addWidget(self.exportar_pdf_button)

        self.setLayout(layout)
        self.carregar_historico()

    def carregar_historico(self):
        """Carrega o histórico de cursos programados no banco de dados e armazena os dados brutos."""
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()

            # Buscar o histórico de cursos ordenados por curso, instrutor e data
            cursor.execute("""
                SELECT 
                    cursos.nome AS curso_nome,
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

            # Armazenar o histórico bruto para filtros
            self.historico_bruto = historico
            self.aplicar_filtros()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {str(e)}")

    def aplicar_filtros(self):
        """Aplica os filtros de pesquisa e mês ao histórico e exibe na tabela."""
        texto_pesquisa = self.search_input.text().lower()
        mes_selecionado = self.mes_combo.currentData()

        # Filtrar o histórico bruto
        historico_filtrado = []
        for curso, instrutor, data, hora in self.historico_bruto:
            data_qdate = QDate.fromString(data, "yyyy-MM-dd")
            if (
                    (not texto_pesquisa or texto_pesquisa in curso.lower() or texto_pesquisa in instrutor.lower()) and
                    (mes_selecionado is None or data_qdate.month() == mes_selecionado)
            ):
                historico_filtrado.append((curso, instrutor, data_qdate, hora))  # Substituí data por data_qdate

        # Agrupar por curso e instrutor, com datas consecutivas juntas
        agrupado = []
        if historico_filtrado:
            curso_atual, instrutor_atual, data_inicio, data_fim, hora_atual = historico_filtrado[0][0], \
                historico_filtrado[0][1], historico_filtrado[0][2], historico_filtrado[0][2], historico_filtrado[0][3]
            for curso, instrutor, data, hora in historico_filtrado[1:]:
                if curso == curso_atual and instrutor == instrutor_atual and data_inicio.daysTo(data) == 1:
                    # Data consecutiva
                    data_fim = data
                else:
                    # Adicionar ao agrupamento com datas formatadas
                    agrupado.append((curso_atual, instrutor_atual,
                                     f"{data_inicio.toString('dd/MM/yyyy')} - {data_fim.toString('dd/MM/yyyy')}"
                                     if data_inicio != data_fim else data_inicio.toString('dd/MM/yyyy'),
                                     hora_atual))
                    # Atualizar para o próximo grupo
                    curso_atual, instrutor_atual, data_inicio, data_fim, hora_atual = curso, instrutor, data, data, hora
            # Adicionar o último grupo
            agrupado.append((curso_atual, instrutor_atual,
                             f"{data_inicio.toString('dd/MM/yyyy')} - {data_fim.toString('dd/MM/yyyy')}"
                             if data_inicio != data_fim else data_inicio.toString('dd/MM/yyyy'),
                             hora_atual))

        # Preencher a tabela com os dados agrupados
        self.tabela.setRowCount(len(agrupado))
        for row, (curso, instrutor, datas, hora) in enumerate(agrupado):
            item_curso = QTableWidgetItem(curso)
            item_curso.setFlags(item_curso.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 0, item_curso)

            item_instrutor = QTableWidgetItem(instrutor)
            item_instrutor.setFlags(item_instrutor.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 1, item_instrutor)

            item_datas = QTableWidgetItem(datas)
            item_datas.setFlags(item_datas.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 2, item_datas)

            item_hora = QTableWidgetItem(hora)
            item_hora.setFlags(item_hora.flags() & ~Qt.ItemIsEditable)
            self.tabela.setItem(row, 3, item_hora)

    def exportar_para_pdf(self):
        """Exporta os dados do histórico para um arquivo PDF com quebras de linha nos nomes dos cursos."""
        try:
            # Selecionar o arquivo para salvar
            nome_arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "", "PDF Files (*.pdf)")
            if not nome_arquivo:
                return

            # Configuração do documento
            pdf = SimpleDocTemplate(nome_arquivo, pagesize=letter)
            elementos = []

            # Título
            elementos.append(Table([["Histórico de Cursos"]], colWidths=[500]))
            elementos[-1].setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 16),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]))

            # Cabeçalho da tabela
            dados = [["Curso", "Instrutor", "Datas", "Horário"]]

            # Função para quebrar texto em múltiplas linhas
            def quebra_linhas(texto, largura_coluna, font_name="Helvetica", font_size=10):
                return "\n".join(simpleSplit(texto, font_name, font_size, largura_coluna))

            # Dados da tabela
            for row in range(self.tabela.rowCount()):
                curso = self.tabela.item(row, 0).text()
                instrutor = self.tabela.item(row, 1).text()
                datas = self.tabela.item(row, 2).text()
                horario = self.tabela.item(row, 3).text()

                # Quebrar texto para colunas com largura definida
                curso = quebra_linhas(curso, 200)
                instrutor = quebra_linhas(instrutor, 150)
                datas = quebra_linhas(datas, 150)
                horario = quebra_linhas(horario, 100)

                dados.append([curso, instrutor, datas, horario])

            # Configurar tabela
            tabela = Table(dados, colWidths=[200, 150, 150, 100])
            tabela.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ]))

            # Adicionar tabela ao documento
            elementos.append(tabela)

            # Construir o PDF
            pdf.build(elementos)
            QMessageBox.information(self, "Sucesso", "Histórico exportado para PDF com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar PDF: {str(e)}")


class ExcluirCursoWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon("editar.png"))
        self.setWindowTitle("Editar ou Excluir Curso")
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()

        # ComboBox para selecionar o curso
        layout.addWidget(QLabel("Selecione o Curso"))
        self.curso_combo = QComboBox()
        self.curso_combo.currentIndexChanged.connect(self.carregar_dados_curso)
        layout.addWidget(self.curso_combo)

        # Campo para editar o nome do curso
        layout.addWidget(QLabel("Editar Nome do Curso"))
        self.curso_input = QLineEdit()
        layout.addWidget(self.curso_input)

        # Botões
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

            # Selecionar os cursos em ordem alfabética
            cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
            cursos = cursor.fetchall()
            conn.close()

            # Limpar a combobox e adicionar os cursos ordenados
            self.curso_combo.clear()
            for curso in cursos:
                self.curso_combo.addItem(curso[1], curso[0])

            if cursos:
                self.carregar_dados_curso()  # Carregar dados do primeiro curso automaticamente
            else:
                QMessageBox.warning(self, "Aviso", "Nenhum curso encontrado no banco de dados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Erro ao carregar cursos: {str(e)}")

    def carregar_dados_curso(self):
        curso_id = self.curso_combo.currentData()
        if curso_id:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM cursos WHERE id = ?", (curso_id,))
                curso = cursor.fetchone()
                conn.close()

                if curso:
                    self.curso_input.setText(curso[0])  # Preencher o campo de edição com o nome atual

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar dados do curso: {str(e)}")

    def editar_curso(self):
        curso_id = self.curso_combo.currentData()
        novo_nome = self.curso_input.text().strip()

        if not curso_id or not novo_nome:
            QMessageBox.warning(self, "Erro", "Selecione um curso e insira um novo nome.")
            return

        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE cursos SET nome = ? WHERE id = ?", (novo_nome, curso_id))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Nome do curso atualizado com sucesso!")
            self.carregar_cursos()  # Recarregar a lista de cursos

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar curso: {str(e)}")

    def excluir_curso(self):
        curso_id = self.curso_combo.currentData()
        if not curso_id:
            QMessageBox.warning(self, "Aviso", "Nenhum curso selecionado para exclusão.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmação",
            "Tem certeza de que deseja excluir este curso? Essa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
                cursor = conn.cursor()

                # Excluir associações de datas e instrutores
                cursor.execute("DELETE FROM cursos_datas WHERE curso_id = ?", (curso_id,))
                cursor.execute("DELETE FROM instrutores_cursos WHERE curso_id = ?", (curso_id,))
                # Excluir o curso
                cursor.execute("DELETE FROM cursos WHERE id = ?", (curso_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Sucesso", "Curso excluído com sucesso!")
                self.carregar_cursos()

            except Exception as e:
                QMessageBox.critical(self, "Erro Crítico", f"Erro ao excluir curso: {str(e)}")


# Janela principal
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("crc.ico"))
        self.setWindowTitle("Gerenciamento de Cursos e Instrutores")
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        self.opcoes_button = QPushButton("Opções")
        self.opcoes_button.setMenu(self.criar_menu_opcoes())
        layout.addWidget(self.opcoes_button)

        # Botão para programar cursos
        self.programar_curso_button = QPushButton("Programar Curso")
        self.programar_curso_button.clicked.connect(self.abrir_programacao_rapida)
        layout.addWidget(self.programar_curso_button)

        # Calendário
        layout.addWidget(QLabel("Calendário com Cursos Programados"))
        self.calendar = QCalendarWidget()
        self.calendar.setFocusPolicy(Qt.NoFocus)  # Desativar navegação por teclado
        self.calendar.clicked.connect(self.handle_single_click)  # Clique simples mostra cursos
        self.calendar.activated.connect(self.handle_double_click)  # Duplo clique abre edição

        layout.addWidget(self.calendar)

        # Label para mostrar as datas selecionadas
        self.selected_dates_label = QLabel("Datas Selecionadas: Nenhuma")
        layout.addWidget(self.selected_dates_label)

        # Tabela para cursos programados
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Curso", "Instrutor", "Horário"])

        # Ajustar colunas automaticamente
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Coluna "Curso"
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Coluna "Instrutor"
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Coluna "Horário"

        # Ajustar quebra de texto
        self.tabela.setWordWrap(True)

        # Ajustar altura das linhas ao conteúdo
        self.tabela.resizeRowsToContents()

        layout.addWidget(self.tabela)

        # Armazenar datas selecionadas
        self.selected_dates = set()  # Datas que o usuário seleciona
        self.programmed_dates = set()  # Datas de cursos programados

        # Atualizar o calendário
        self.atualizar_calendario()

        # Aplicar o tema futurista com mais animações
        self.setStyleSheet("""
            /* Fundo da janela */
            QMainWindow {
                background-color: #f5f5f5;  /* Fundo branco suave */
                color: #333;  /* Texto escuro */
            }

            /* Botões */
            QPushButton {
                background-color: #4a90e2;  /* Azul moderno */
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.3s ease-in-out;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }

            QPushButton:hover {
                background-color: #357abd;  /* Azul mais escuro no hover */
                transform: scale(1.1);  /* Efeito de zoom suave */
                box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.4);
            }

            QPushButton:pressed {
                background-color: #2d6cb1;
                transform: scale(0.95);  /* Efeito de "clique" */
            }

            /* Animação de Fade In nos Botões */
            QPushButton {
                animation: fadeIn 1s ease-in-out;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: scale(0.9); }
                to { opacity: 1; transform: scale(1); }
            }

            /* Tabelas */
            QTableWidget {
                background-color: white;
                border: 1px solid #ccc;
                color: #333;
                font-size: 14px;
                selection-background-color: #4a90e2;  /* Destaque azul */
                selection-color: white;
                transition: background-color 0.3s ease;
            }

            /* Efeito de Seleção na Tabela */
            QTableWidget::item:selected {
                background-color: #357abd;
                color: white;
                transition: background-color 0.4s ease-in-out;
            }

            /* Cabeçalhos da Tabela */
            QHeaderView::section {
                background-color: #e1e1e1;
                color: #333;
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }

            /* Campos de Entrada */
            QLineEdit {
                background-color: white;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 6px;
                font-size: 14px;
                transition: border-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
            }

            QLineEdit:focus {
                border: 2px solid #4a90e2;
                box-shadow: 0px 0px 8px rgba(74, 144, 226, 0.7);
            }

            /* Calendário */
            QCalendarWidget QWidget {
                alternate-background-color: #f8f8f8;
                color: #333;
                font-size: 14px;
            }

            /* Datas Selecionadas no Calendário */
            QCalendarWidget QAbstractItemView:enabled {
                selection-background-color: #4a90e2;
                selection-color: white;
                transition: background-color 0.3s ease-in-out;
            }

            /* Animação Hover nas Datas */
            QCalendarWidget QAbstractItemView:item:hover {
                background-color: #ddeeff;
                transition: background-color 0.3s ease-in-out;
            }

            /* Rótulos */
            QLabel {
                color: #4a90e2;
                font-size: 16px;
                font-weight: bold;
            }
        """)

    def handle_date_selection(self, clicked_date):
        """Abre a janela de programação do curso ao clicar em uma data no calendário."""
        data_str = clicked_date.toString("yyyy-MM-dd")

        # Abre a janela para editar ou excluir cursos na data selecionada
        self.abrir_programar_curso(clicked_date)

    def handle_single_click(self, clicked_date):
        """Apenas exibe os cursos programados para a data clicada sem alterar as datas programadas."""
        date_str = clicked_date.toString("yyyy-MM-dd")
        self.atualizar_tabela_cursos(clicked_date)  # Mostra os cursos na tabela
        self.selected_dates_label.setText(f"Cursos programados para: {date_str}")

    def handle_double_click(self, clicked_date):
        """Abre a janela de edição/exclusão de curso ao dar um duplo clique no calendário."""
        self.abrir_programar_curso(clicked_date)

    def update_calendar_visual(self):
        """Atualiza o fundo das datas no calendário."""
        # Limpar formatações anteriores
        default_format = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_format)

        # Destacar datas programadas (em verde)
        programmed_format = QTextCharFormat()
        programmed_format.setBackground(QColor("lightgreen"))

        for date_str in self.programmed_dates:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            self.calendar.setDateTextFormat(date, programmed_format)

        # Destacar datas selecionadas pelo usuário (em azul)
        selected_format = QTextCharFormat()
        selected_format.setBackground(QColor("lightblue"))

        for date_str in self.selected_dates:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            self.calendar.setDateTextFormat(date, selected_format)

    def atualizar_calendario(self):
        """Carrega as datas programadas do banco de dados e atualiza a visualização do calendário."""
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT data FROM cursos_datas")
            datas = cursor.fetchall()
            conn.close()

            # Armazenar as datas programadas em um conjunto
            self.programmed_dates = {data[0] for data in datas}

            # Atualizar o visual do calendário
            self.update_calendar_visual()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar calendário: {str(e)}")

    def abrir_programacao_rapida(self):
        """Abre a janela para programar cursos rapidamente com lógica automática de escolha do instrutor."""
        try:
            # Resetar datas selecionadas
            datas_selecionadas = set()

            dialog = QDialog(self)

            dialog.setWindowTitle("Programação Rápida de Curso")
            dialog.setGeometry(300, 300, 500, 600)
            # Adicionar ícone à janela
            dialog.setWindowIcon(QIcon("agenda.png"))


            layout = QVBoxLayout(dialog)

            # Seleção de curso
            layout.addWidget(QLabel("Selecione o Curso"))
            curso_combo = QComboBox()

            # Campo de pesquisa
            search_input = QLineEdit()
            search_input.setPlaceholderText("Pesquisar curso...")
            layout.addWidget(search_input)

            # ComboBox para cursos
            curso_combo = QComboBox()
            layout.addWidget(curso_combo)

            # Conectar ao banco de dados e carregar cursos
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM cursos ORDER BY nome ASC")
            cursos = cursor.fetchall()
            conn.close()

            if not cursos:
                QMessageBox.warning(self, "Aviso", "Nenhum curso cadastrado!")
                return

            # Lista de cursos original (para filtro)
            cursos_originais = cursos

            # Função para filtrar cursos com base no texto digitado
            def filtrar_cursos(texto):
                texto = texto.lower()
                curso_combo.clear()
                for curso_id, curso_nome in cursos_originais:
                    if texto in curso_nome.lower():
                        curso_combo.addItem(curso_nome, curso_id)

            # Conectar o campo de pesquisa ao filtro
            search_input.textChanged.connect(filtrar_cursos)

            # Preencher o ComboBox inicialmente
            filtrar_cursos("")

            # Calendário para seleção de múltiplas datas
            layout.addWidget(QLabel("Selecione as Datas"))
            calendario = QCalendarWidget()
            layout.addWidget(calendario)

            # Lista de datas selecionadas
            # Lista de datas selecionadas
            def toggle_date(date):
                """Adiciona ou remove a data da lista de selecionadas."""
                date_str = date.toString("yyyy-MM-dd")
                if date_str in datas_selecionadas:
                    datas_selecionadas.remove(date_str)
                else:
                    datas_selecionadas.add(date_str)
                update_calendar_visual()

            def update_calendar_visual():
                """Atualiza o visual do calendário para destacar as datas selecionadas."""
                default_format = QTextCharFormat()
                calendario.setDateTextFormat(QDate(), default_format)
                highlight_format = QTextCharFormat()
                highlight_format.setBackground(QColor("lightblue"))
                for date_str in datas_selecionadas:
                    date = QDate.fromString(date_str, "yyyy-MM-dd")
                    calendario.setDateTextFormat(date, highlight_format)
            calendario.clicked.connect(toggle_date)
            # Seleção de horário
            layout.addWidget(QLabel("Hora do Curso"))
            hora_input = QTimeEdit()
            hora_input.setDisplayFormat("HH:mm")
            layout.addWidget(hora_input)
            # Botão de salvar
            salvar_button = QPushButton("Salvar Programação")
            salvar_button.clicked.connect(lambda: self.salvar_programacao_rapida(
                curso_combo.currentData(),
                datas_selecionadas,
                hora_input.time().toString("HH:mm"),
                dialog
            ))
            layout.addWidget(salvar_button)
            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
              QMessageBox.critical(self, "Erro Crítico", f"Erro ao abrir programação: {str(e)}")

    def salvar_programacao_rapida(self, curso_id, datas, hora, dialog):
        """Salva a programação do curso para as datas selecionadas com atribuição cíclica de instrutores."""
        if not curso_id or not datas:
            QMessageBox.warning(self, "Erro", "Selecione curso e pelo menos uma data.")
            return

        conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
        cursor = conn.cursor()

        try:
            # Buscar instrutores associados ao curso
            cursor.execute("""
                SELECT instrutores.id, instrutores.nome
                FROM instrutores_cursos
                JOIN instrutores ON instrutores.id = instrutores_cursos.instrutor_id
                WHERE instrutores_cursos.curso_id = ?
                ORDER BY instrutores.id
            """, (curso_id,))
            instrutores = cursor.fetchall()

            if not instrutores:
                QMessageBox.warning(self, "Erro", "Nenhum instrutor associado a este curso.")
                return

            # Obter o último instrutor atribuído para o curso
            cursor.execute("""
                SELECT instrutor_id
                FROM cursos_datas
                WHERE curso_id = ?
                ORDER BY data DESC, hora DESC
                LIMIT 1
            """, (curso_id,))
            ultimo_instrutor = cursor.fetchone()
            ultimo_instrutor_id = ultimo_instrutor[0] if ultimo_instrutor else None

            # Determinar o próximo instrutor na fila
            instrutores_ids = [instrutor[0] for instrutor in instrutores]
            if ultimo_instrutor_id in instrutores_ids:
                proximo_instrutor_index = (instrutores_ids.index(ultimo_instrutor_id) + 1) % len(instrutores_ids)
            else:
                proximo_instrutor_index = 0  # Começar pelo primeiro instrutor se nenhum foi atribuído ainda

            proximo_instrutor_id = instrutores_ids[proximo_instrutor_index]

            # Salvar programações para as datas selecionadas
            for date_str in datas:
                cursor.execute("""
                    INSERT INTO cursos_datas (curso_id, data, hora, instrutor_id)
                    VALUES (?, ?, ?, ?)
                """, (curso_id, date_str, hora, proximo_instrutor_id))

            conn.commit()
            QMessageBox.information(self, "Sucesso", "Cursos programados com sucesso!")

            # Atualizar o calendário principal para refletir os cursos programados
            self.atualizar_calendario()

            # Limpar datas selecionadas e fechar a janela
            datas.clear()
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao programar cursos: {str(e)}")

        finally:
            conn.close()

    def atualizar_calendario(self):
        """Atualiza o calendário principal com as datas programadas e destaca datas passadas."""
        try:
            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT data FROM cursos_datas")
            datas = cursor.fetchall()
            conn.close()

            # Limpar formatações anteriores
            default_format = QTextCharFormat()
            self.calendar.setDateTextFormat(QDate(), default_format)

            # Formato para datas futuras programadas
            future_format = QTextCharFormat()
            future_format.setBackground(QColor("lightgreen"))

            # Formato para datas passadas programadas
            past_format = QTextCharFormat()
            past_format.setBackground(QColor("gray"))

            # Data atual
            hoje = QDate.currentDate()

            # Aplicar formatações
            for data in datas:
                data_qdate = QDate.fromString(data[0], "yyyy-MM-dd")
                if data_qdate < hoje:
                    # Data passou
                    self.calendar.setDateTextFormat(data_qdate, past_format)
                else:
                    # Data futura
                    self.calendar.setDateTextFormat(data_qdate, future_format)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao atualizar calendário: {str(e)}")

    def atualizar_tabela_cursos(self, qdate):
        """Atualiza a tabela com os cursos programados para a data selecionada, impedindo modificações."""
        if isinstance(qdate, str):
            qdate = QDate.fromString(qdate, "yyyy-MM-dd")
            if not qdate.isValid():
                print(f"Erro: não foi possível converter '{qdate}' para QDate.")
                return

        if not isinstance(qdate, QDate):
            print(f"Erro: qdate deve ser do tipo QDate, mas é {type(qdate)}")
            return

        try:
            data = qdate.toString("yyyy-MM-dd")

            conn = sqlite3.connect(r'\\srvsql\Banco Cursos\instrutores.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    cursos.nome as curso_nome,
                    instrutores.nome as instrutor_nome,
                    cursos_datas.hora
                FROM cursos_datas
                JOIN cursos ON cursos.id = cursos_datas.curso_id
                JOIN instrutores ON instrutores.id = cursos_datas.instrutor_id
                WHERE cursos_datas.data = ?
                ORDER BY cursos_datas.hora
            ''', (data,))
            cursos = cursor.fetchall()
            conn.close()

            self.tabela.setRowCount(0)

            for row, (curso_nome, instrutor_nome, hora) in enumerate(cursos):
                self.tabela.insertRow(row)

                # Adicionar os itens na tabela, tornando-os somente leitura
                curso_item = QTableWidgetItem(curso_nome)
                curso_item.setFlags(curso_item.flags() & ~Qt.ItemIsEditable)

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
            print(f"Erro: qdate deve ser do tipo QDate, mas é {type(qdate)}")
            return

        data = qdate.toString("yyyy-MM-dd")
        janela_programacao = ProgramarCursoWindow(data, self)
        janela_programacao.setModal(True)
        janela_programacao.exec_()

        # Atualizar calendário e tabela após o fechamento
        self.atualizar_calendario()
        self.atualizar_tabela_cursos(self.calendar.selectedDate())

    from PyQt5.QtGui import QIcon

    def criar_menu_opcoes(self):
        menu = QMenu()

        menu.addAction(
            QAction(QIcon("conectar.png"), "Associar Cursos a Instrutor", self, triggered=self.abrir_associar_curso))
        menu.addAction(QAction(QIcon("cadastre-se.png"), "Cadastrar Curso", self, triggered=self.abrir_cadastro_curso))
        menu.addAction(
            QAction(QIcon("cadastre-se.png"), "Cadastrar Instrutor", self, triggered=self.abrir_cadastro_instrutor))
        menu.addAction(
            QAction(QIcon("editar.png"), "Editar/Excluir Curso", self, triggered=self.abrir_editar_excluir_curso))
        menu.addAction(QAction(QIcon("editar.png"), "Editar Instrutor", self, triggered=self.abrir_editar_instrutor))
        menu.addAction(QAction(QIcon("excluir.png"), "Excluir Instrutor", self, triggered=self.abrir_excluir_instrutor))
        menu.addAction(QAction(QIcon("informacoes.png"), "Exibir Informações dos Instrutores", self,
                               triggered=self.abrir_exibir_instrutores))
        menu.addAction(QAction(QIcon("historico.png"), "Ver Histórico", self, triggered=self.abrir_historico))

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


if __name__ == '__main__':
    criar_banco()
    app = QApplication(sys.argv)
    janela = MainWindow()
    janela.show()
    sys.exit(app.exec_())
