import sqlite3

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        descricao TEXT
    )
    """)

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


    # Criar tabela de documentos anexados ao instrutor
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instrutores_documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instrutor_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        extensao TEXT,
        mime_type TEXT,
        conteudo BLOB NOT NULL,
        data_upload TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(instrutor_id) REFERENCES instrutores(id)
    )
    ''')

    # Criar tabela de alunos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        curso_id INTEGER NOT NULL,
        nome TEXT NOT NULL,
        faculdade TEXT,
        nome_arquivo TEXT,
        extensao TEXT,
        mime_type TEXT,
        conteudo BLOB,
        data_cadastro TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(curso_id) REFERENCES cursos(id)
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

    # Novas colunas de cadastro do instrutor
    if "cpf" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN cpf TEXT")

    if "cnpj" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN cnpj TEXT")

    if "empresa" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN empresa TEXT")

    if "email" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN email TEXT")

    if "telefone" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN telefone TEXT")
    # >>> NOVO CAMPO: PROCESSO SEI <<<
    if "processo_sei" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN processo_sei TEXT")

    # >>> NOVOS CAMPOS: CREDENCIAMENTO <<<
    if "data_solicitacao_credenciamento" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN data_solicitacao_credenciamento TEXT")
    if "validade_contrato" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN validade_contrato TEXT")
    if "convocado_ano" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN convocado_ano TEXT")
    if "sugestoes_cursos" not in colunas_instrutores:
        cursor.execute("ALTER TABLE instrutores ADD COLUMN sugestoes_cursos TEXT")

    # Verificar e adicionar colunas na tabela 'cursos_datas'
    cursor.execute("PRAGMA table_info(cursos_datas)")
    colunas_cursos_datas = [coluna[1] for coluna in cursor.fetchall()]

    if "hora" not in colunas_cursos_datas:
        cursor.execute("ALTER TABLE cursos_datas ADD COLUMN hora TEXT")
    if "instrutor_id" not in colunas_cursos_datas:
        cursor.execute("ALTER TABLE cursos_datas ADD COLUMN instrutor_id INTEGER")

    # Verificar e adicionar coluna na tabela 'cursos'
    cursor.execute("PRAGMA table_info(cursos)")
    colunas_cursos = [coluna[1] for coluna in cursor.fetchall()]

    if "descricao" not in colunas_cursos:
        cursor.execute("ALTER TABLE cursos ADD COLUMN descricao TEXT")

    # >>> NOVAS COLUNAS <<<
    if "epc" not in colunas_cursos:
        cursor.execute("ALTER TABLE cursos ADD COLUMN epc TEXT")

    if "carga_horaria" not in colunas_cursos:
        cursor.execute("ALTER TABLE cursos ADD COLUMN carga_horaria INTEGER")

    # Criar tabela de alunos se não existir
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='alunos'
    """)
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                faculdade TEXT,
                nome_arquivo TEXT,
                extensao TEXT,
                mime_type TEXT,
                conteudo BLOB,
                data_cadastro TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(curso_id) REFERENCES cursos(id)
            )
        ''')

    # Criar tabela de temas se não existir
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='temas'
    """)
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE temas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            )
        ''')

    # Criar tabela de subtemas se não existir
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='subtemas'
    """)
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE subtemas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                FOREIGN KEY(tema_id) REFERENCES temas(id) ON DELETE CASCADE
            )
        ''')

    # Criar tabela de associação temas-instrutores se não existir
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='temas_instrutores'
    """)
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE temas_instrutores (
                tema_id INTEGER NOT NULL,
                instrutor_id INTEGER NOT NULL,
                FOREIGN KEY(tema_id) REFERENCES temas(id) ON DELETE CASCADE,
                FOREIGN KEY(instrutor_id) REFERENCES instrutores(id) ON DELETE CASCADE,
                PRIMARY KEY(tema_id, instrutor_id)
            )
        ''')

    conn.commit()
    conn.close()
