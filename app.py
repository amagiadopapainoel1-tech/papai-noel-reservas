from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

# ---------------------------
# CONFIGURAÇÕES DO EMAIL
# ---------------------------
EMAIL_REMETENTE = "amagiadopapainoel1@gmail.com"
SENHA_EMAIL = "taniameuamor"   # ← coloque aqui sua App Password
NOME_REMETENTE = "Central de Distribuição de Presentes do Papai Noel"

# Caminhos dos anexos
QR_CODE_PATH = "static/KrCode pix Paulo.jpg"
NOEL_FOTO_PATH = "static/noel.png"

# ---------------------------
# FUNÇÃO: CRIA TABELA
# ---------------------------
def criar_tabela():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            idade TEXT,
            data TEXT,
            horario_escolhido TEXT,
            horario_real TEXT,
            endereco TEXT,
            email TEXT,
            telefone TEXT,
            presente TEXT,
            valor REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

criar_tabela()

# ---------------------------
# FUNÇÃO: GERAR LISTA DE HORÁRIOS DE 2 EM 2 MINUTOS
# ---------------------------
def gerar_horarios_reais():
    inicio = datetime(2025, 12, 24, 14, 0)
    fim = datetime(2025, 12, 25, 11, 0)

    horarios = []
    atual = inicio
    while atual <= fim:
        horarios.append(atual.strftime("%d/%m/%Y %H:%M"))
        atual += timedelta(minutes=2)

    return horarios

HORARIOS_REAIS = gerar_horarios_reais()

# ---------------------------
# FUNÇÃO: OBTER HORÁRIOS JÁ AGENDADOS
# ---------------------------
def horarios_ocupados():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT horario_real FROM agendamentos")
    dados = cursor.fetchall()
    conn.close()
    return {linha[0] for linha in dados}

# ---------------------------
# FUNÇÃO: ENCONTRAR O HORÁRIO DISPONÍVEL MAIS PRÓXIMO
# ---------------------------
def encontrar_horario_real(horario_desejado):
    ocupados = horarios_ocupados()

    # Converte o horário escolhido
    h = datetime.strptime(horario_desejado, "%H:%M")

    # Constrói um datetime completo com data base 24/12
    base = datetime(2025, 12, 24, h.hour, h.minute)

    # Procura o primeiro horário real posterior
    for hr in HORARIOS_REAIS:
        dt_hr = datetime.strptime(hr, "%d/%m/%Y %H:%M")
        if dt_hr >= base:
            if hr not in ocupados:
                return hr

    return None  # caso muito improvável

# ---------------------------
# FUNÇÃO: ENVIAR O EMAIL
# ---------------------------
def enviar_email(destinatario, nome, horario_real, valor):
    msg = EmailMessage()
    msg["Subject"] = "Confirmação de Agendamento - Papai Noel 🎅"
    msg["From"] = f"{NOME_REMETENTE} <{EMAIL_REMETENTE}>"
    msg["To"] = destinatario

    corpo = f"""
Olá {nome}!

Seu agendamento foi recebido com sucesso pela 
**Central de Distribuição de Presentes do Papai Noel 🎅**

---------------------------------------
📅 **Horário confirmado:** {horario_real}
💰 **Valor da entrega:** R$ {valor:.2f}
---------------------------------------

### 🔻 Formas de Pagamento

Você pode concluir o pagamento da reserva usando **qualquer opção abaixo**:

---

### ✅ **1) PIX Copia e Cola**
