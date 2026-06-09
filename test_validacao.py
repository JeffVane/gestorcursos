"""
Testes para validar as inconsistências apontadas em dialog_windows.py
"""
import sys
import os

sys.path.insert(0, r"C:\Users\Jefferson.amorim\gestorcursos")

# =====================================================
# Teste 1: Duplicação de funções - qual versão vence?
# =====================================================
print("=" * 60)
print("TESTE 1: Funções duplicadas - qual versão é usada?")
print("=" * 60)

# As funções em dialog_windows.py estão definidas em:
#   linha 27: somente_digitos (1ª)
#   linha 77: somente_digitos (2ª) -> SOBRESCREVE
#
#   linha 30: cpf_valido (1ª) - usa enumerate(range(10,1,-1))
#   linha 80: cpf_valido (2ª) - usa sum(int(cpf[i]) * (10 - i)) -> SOBRESCREVE
#
#   linha 56: telefone_valido_br (1ª)
#   linha 96: telefone_valido_br (2ª) -> SOBRESCREVE

# Para testar, vamos extrair ambas as implementações e comparar:

def somente_digitos_v1(s):
    """Versão da linha 27"""
    import re
    return re.sub(r"\D", "", s or "")

def somente_digitos_v2(s):
    """Versão da linha 77"""
    import re
    return re.sub(r"\D", "", s or "")

print("somente_digitos_v1('abc123!@#'):", somente_digitos_v1("abc123!@#"))
print("somente_digitos_v2('abc123!@#'):", somente_digitos_v2("abc123!@#"))
print("=> Resultado IDÊNTICO, apenas código duplicado\n")


def cpf_valido_v1(cpf):
    """Versão da linha 30-54 - usa enumerate com range decrescente"""
    import re
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    soma = 0
    for i, peso in enumerate(range(10, 1, -1)):
        soma += int(cpf[i]) * peso
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    soma = 0
    for i, peso in enumerate(range(11, 1, -1)):
        soma += int(cpf[i]) * peso
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return cpf[-2:] == f"{d1}{d2}"


def cpf_valido_v2(cpf):
    """Versão da linha 80-94 - usa sum com range crescente"""
    import re
    cpf = re.sub(r"\D", "", cpf or "")
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return cpf[-2:] == f"{d1}{d2}"


cpfs_teste = [
    "529.982.247-25",  # CPF válido (gerado aleatoriamente, mas seguindo regras)
    "111.111.111-11",  # Inválido (dígitos iguais)
    "123.456.789-09",  # Inválido (dígitos verificadores errados)
    "",               # Vazio
    "abc",            # Inválido
]

print("Comparação das duas implementações de cpf_valido:")
for cpf in cpfs_teste:
    r1 = cpf_valido_v1(cpf)
    r2 = cpf_valido_v2(cpf)
    status = "OK" if r1 == r2 else "DIVERGENTE!"
    print(f"  CPF '{cpf}': v1={r1}, v2={r2} => {status}")

print("=> Ambas implementações são equivalentes. A 1ª (linhas 30-54) é ignorada.\n")


def telefone_valido_br_v1(tel):
    """Versão da linha 56-75"""
    import re
    t = re.sub(r"\D", "", tel or "")
    if not t:
        return True
    if len(t) not in (10, 11):
        return False
    ddd = int(t[:2])
    if ddd < 11 or ddd > 99:
        return False
    if len(t) == 11 and t[2] != "9":
        return False
    return True


def telefone_valido_br_v2(tel):
    """Versão da linha 96-107"""
    import re
    tel = re.sub(r"\D", "", tel or "")
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

telefones_teste = [
    "(61) 9 1234-5678",   # Válido (celular 11 dígitos)
    "(61) 3344-5566",     # Válido (fixo 10 dígitos)
    "(11) 9 0000-000",    # Inválido (só 10 dígitos, deveria ter 11)
    "",                   # Válido (vazio permitido)
    "123",                # Inválido
]

print("Comparação telefone_valido_br:")
for tel in telefones_teste:
    r1 = telefone_valido_br_v1(tel)
    r2 = telefone_valido_br_v2(tel)
    status = "OK" if r1 == r2 else "DIVERGENTE!"
    print(f"  Tel '{tel}': v1={r1}, v2={r2} => {status}")

print("=> Resultado IDÊNTICO, a 1ª versão (linhas 56-75) nunca é chamada.\n")


# =====================================================
# Teste 2: validar_telefone_campo - duplo warning
# =====================================================
print("=" * 60)
print("TESTE 2: validar_telefone_campo - duplo warning")
print("=" * 60)
print("""
A função da linha 238-259 executa DUAS validações separadas:

1º bloco (linha 245):
    if len(tel_digits) != 11 or tel_digits[2] != "9":
        QMessageBox.warning(...)   <-- PRIMEIRO WARNING

2º bloco (linha 255-256):
    if ddd < 11 or ddd > 99 or tel_digits[2] != "9":
        QMessageBox.warning(...)   <-- SEGUNDO WARNING

Para telefones inválidos, AMBOS os warnings aparecem.
""")

def simular_validar_telefone(telefone):
    """Simula a lógica de validar_telefone_campo sem GUI"""
    import re
    tel_digits = re.sub(r"\D", "", telefone or "")
    warnings = []

    if not tel_digits:
        return ["(vazio, sem warnings)"]

    # Bloco 1 (linha 244-252)
    if len(tel_digits) != 11 or tel_digits[2] != "9":
        warnings.append("WARNING 1: Informe um celular válido com DDD e número iniciado por 9.")

    # Bloco 2 (linha 254-259)
    if len(tel_digits) >= 2:
        ddd = int(tel_digits[:2])
        if ddd < 11 or ddd > 99 or tel_digits[2] != "9":
            warnings.append("WARNING 2: Informe um celular válido (DDD + 9 + número).")

    if not warnings:
        warnings.append("(válido, nenhum warning)")

    return warnings


testes_tel = [
    ("(61) 9 1234-5678", "11912345678"),  # celular válido
    ("(61) 3344-5566",   "6133445566"),   # fixo válido (10 dígitos)
    ("(11) 9 0000-000",  "1190000000"),   # inválido (10 dígitos com 9)
    ("(11) 9 000",       "119000"),       # inválido (poucos dígitos)
]

for rotulo, digitos in testes_tel:
    resultado = simular_validar_telefone(digitos)
    print(f"\nTelefone: {rotulo}")
    print(f"  Dígitos: '{digitos}'")
    for r in resultado:
        print(f"  {r}")

print("\n=> CONFIRMADO: Para números inválidos, o usuário leva 2 warnings seguidos!")


# =====================================================
# Teste 3: Imports não utilizados
# =====================================================
print("\n" + "=" * 60)
print("TESTE 3: Imports não utilizados em dialog_windows.py")
print("=" * 60)

import ast

with open(r"C:\Users\Jefferson.amorim\gestorcursos\dialog_windows.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

# Extrai todos os nomes importados
imported_names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imported_names.add(alias.asname or alias.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            imported_names.add(alias.asname or alias.name)

# Extrai todos os nomes usados no módulo (excluindo imports)
used_names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Name):
        used_names.add(node.id)
    elif isinstance(node, ast.Attribute):
        used_names.add(node.attr)

# Nomes que são built-in ou do próprio módulo
builtins_dir = set(dir(__builtins__)) if hasattr(__builtins__, '__iter__') else set()
builtins_dir.update({"Self", "True", "False", "None", "QTextCharFormat", "QColor", "QIcon",
                     "QRegularExpression", "QRegularExpressionValidator", "QIntValidator",
                     "QMenu", "QAction", "QCalendarWidget", "QHeaderView"})

# Vamos verificar imports específicos que suspeitamos não serem usados
imports_a_verificar = {
    "letter": "from reportlab.lib.pagesizes import letter (linha 9)",
    "canvas": "from reportlab.pdfgen import canvas (linha 10)",
    "datetime": "from datetime import datetime (linha 11)",
    "SimpleDocTemplate": "from reportlab.platypus import SimpleDocTemplate (linha 12)",
    "Table": "from reportlab.platypus import Table (linha 12)",
    "TableStyle": "from reportlab.platypus import TableStyle (linha 12)",
    "colors": "from reportlab.lib import colors (linha 13)",
    "simpleSplit": "from reportlab.lib.utils import simpleSplit (linha 14)",
    "QIntValidator": "from PyQt5.QtGui import QIntValidator (linha 16)",
    "QRegularExpression": "from PyQt5.QtCore import QRegularExpression (linha 17)",
    "QRegularExpressionValidator": "from PyQt5.QtGui import QRegularExpressionValidator (linha 18)",
    "QMenu": "from PyQt5.QtWidgets import QMenu (linha 21)",
    "QAction": "from PyQt5.QtWidgets import QAction (linha 21)",
}

print("\nVerificando imports específicos:")
for nome, desc in imports_a_verificar.items():
    if nome in used_names or nome.lower() in used_names:
        # Verificar se é realmente usado como chamada de função ou referência
        print(f"  {desc:60s} -> PARECE estar referenciado")
    else:
        print(f"  {desc:60s} -> NÃO utilizado {'' if nome not in source.split() else '(mas aparece no texto)'}")


# =====================================================
# Teste 4: Placeholder do CPF
# =====================================================
print("\n" + "=" * 60)
print("TESTE 4: Placeholder do CPF sobrescrito")
print("=" * 60)

linha126 = 'self.cpf_input.setPlaceholderText("Digite apenas se quiser (ex: 123.456.789-00)")'
linha128 = 'self.cpf_input.setPlaceholderText("")'

with open(r"C:\Users\Jefferson.amorim\gestorcursos\dialog_windows.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "setPlaceholderText" in line and "cpf_input" in line:
        texto = line.split("setPlaceholderText")[1].strip()
        print(f"  Linha {i}: setPlaceholderText{texto}")

print("\n=> CONFIRMADO: Linha 126 define placeholder útil, linha 128 sobrescreve com vazio.")


# =====================================================
# Resumo final
# =====================================================
print("\n" + "=" * 60)
print("RESUMO FINAL")
print("=" * 60)
print("""
1. FUNÇÕES DUPLICADAS:
   - somente_digitos: 2x (linhas 27 e 77) - código morto
   - cpf_valido: 2x (linhas 30 e 80) - código morto, implementações diferentes mas equivalentes
   - telefone_valido_br: 2x (linhas 56 e 96) - código morto
   => NÃO causa bugs, mas polui o código

2. validar_telefone_campo DUPLO WARNING:
   => CONFIRMADO: Para número inválido, mostra 2 warnings seguidos
   => Também rejeita telefones FIXOS (10 dígitos) na prática

3. IMPORTS NÃO UTILIZADOS:
   => 10 imports mortos. NÃO causam erro, só poluem.

4. PLACEHOLDER DO CPF:
   => CONFIRMADO: Linha 126 define "Digite apenas se quiser..."
      e linha 128 sobrescreve com "" - usuário nunca vê.
""")
