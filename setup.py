from cx_Freeze import setup, Executable
import os
import sys

# ---- Caminhos do PyQt5 / Qt (plugins) ----
pyqt5_path = os.path.join(sys.prefix, "Lib", "site-packages", "PyQt5")
qt5_path = os.path.join(pyqt5_path, "Qt5")
qt_plugins_path = os.path.join(qt5_path, "plugins")
qt_bin_path = os.path.join(qt5_path, "bin")  # onde ficam DLLs do Qt

include_files = [
    # imagens
    "agenda.png",
    "cadastre-se.png",
    "conectar.png",
    "curso.png",
    "curso-removebg-preview.png",
    "editar.png",
    "excluir.png",
    "historico.png",
    "informacoes.png",

    # ícones
    "crc.ico",
    "teste.ico",

    # plugins do Qt (necessário pro platform plugin "windows")
    (qt_plugins_path, "Qt5/plugins"),

    # dlls do Qt (ajuda a evitar erro de dll faltando)
    (qt_bin_path, "Qt5/bin"),
]

build_exe_options = {
    "packages": [
        "sqlite3", "PyQt5", "reportlab", "datetime", "os", "sys", "re",
        "tempfile", "smtplib", "email", "email.mime.text", "email.mime.multipart",
        "email.mime.image", "urllib.parse",
    ],
    "includes": [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtPrintSupport",
    ],
    "include_files": include_files,
    # Excluir módulos não utilizados
    "excludes": [
        "tkinter",
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.QtQmlModels",
        "PyQt5.QtQuickWidgets",
    ],
    "include_msvcr": True,
}

base = "gui" if sys.platform == "win32" else None

setup(
    name="GerenciamentoCursos",
    version="1.0",
    description="Sistema de Gerenciamento de Cursos e Instrutores",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            icon=os.path.abspath("crc.ico"),
            target_name="Gestão De Cursos.exe",
        )
    ],
)